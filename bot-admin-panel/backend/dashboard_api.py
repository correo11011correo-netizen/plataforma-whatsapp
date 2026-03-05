import os
import sys
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# --- Rutas absolutas ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

BOT_ENGINE_PATH = os.path.join(PROJECT_ROOT, 'bot-manager', 'bot-engine')
DB_PATH = os.path.join(PROJECT_ROOT, 'bot-manager', 'database', 'bot_dashboard.db')

if BOT_ENGINE_PATH not in sys.path:
    sys.path.insert(0, BOT_ENGINE_PATH)

try:
    from engine import load_config, send_msg
except ImportError:
    print("❌ Error: No se pudo importar 'engine.py'.")
    sys.exit(1)

# Inicializar Flask
app = Flask(__name__)
# Habilitar CORS para permitir peticiones desde fundacionidear.com
CORS(app)

# Cargar configuración
env_path = os.path.join(BOT_ENGINE_PATH, '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
cfg = load_config()

# Credenciales quemadas para el login (SOLO PARA DEMO - En prod usar DB/JWT)
ADMIN_USER = "admin"
ADMIN_PASS = "idear2024"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- ENDPOINTS DE LA API ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if data.get('username') == ADMIN_USER and data.get('password') == ADMIN_PASS:
        return jsonify({"success": True, "token": "token-falso-123"}) # Simulación de token
    return jsonify({"success": False, "message": "Credenciales inválidas"}), 401

@app.route('/api/chats', methods=['GET'])
def get_chats():
    # En un caso real validaríamos el token aquí
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT
            c.phone_number,
            c.name,
            conv.is_human_intervening,
            MAX(m.timestamp) AS last_message_timestamp,
            (SELECT content FROM messages WHERE contact_id = c.id ORDER BY timestamp DESC LIMIT 1) AS last_message_content
        FROM contacts c
        LEFT JOIN conversations conv ON c.id = conv.contact_id
        LEFT JOIN messages m ON c.id = m.contact_id
        GROUP BY c.id
        ORDER BY last_message_timestamp DESC;
    """
    cursor.execute(query)
    conversations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(conversations)

@app.route('/api/chats/<phone_number>/messages', methods=['GET'])
def get_messages(phone_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT m.sender, m.content, m.timestamp
        FROM messages m
        JOIN contacts c ON m.contact_id = c.id
        WHERE c.phone_number = ?
        ORDER BY m.timestamp ASC;
    """
    cursor.execute(query, (phone_number,))
    messages = [dict(row) for row in cursor.fetchall()]
    
    # Obtener también el estado actual
    cursor.execute("""
        SELECT conv.is_human_intervening 
        FROM conversations conv
        JOIN contacts c ON conv.contact_id = c.id
        WHERE c.phone_number = ?
    """, (phone_number,))
    row = cursor.fetchone()
    is_human = bool(row['is_human_intervening']) if row else False
    
    conn.close()
    return jsonify({"messages": messages, "is_human_intervening": is_human})

@app.route('/api/chats/<phone_number>/toggle', methods=['POST'])
def toggle_bot(phone_number):
    data = request.json
    status = data.get('is_human_intervening', True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversations (contact_id, is_human_intervening)
        VALUES ((SELECT id FROM contacts WHERE phone_number = ?), ?)
        ON CONFLICT(contact_id) DO UPDATE SET
        is_human_intervening = excluded.is_human_intervening,
        last_updated = CURRENT_TIMESTAMP;
    """, (phone_number, 1 if status else 0))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "is_human_intervening": status})

@app.route('/api/chats/<phone_number>/send', methods=['POST'])
def send_message(phone_number):
    data = request.json
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({"success": False, "message": "Mensaje vacío"}), 400
        
    try:
        # Enviar vía API Meta
        send_msg(cfg, phone_number, message)
        
        # Corregir DB para que quede como Humano
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE messages 
            SET sender = 'human' 
            WHERE contact_id = (SELECT id FROM contacts WHERE phone_number = ?) 
            AND sender = 'bot' 
            ORDER BY timestamp DESC LIMIT 1
        """, (phone_number,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    # Ejecutar en el puerto 5002 para no chocar con el Bot Engine (5001) ni otros (5000)
    app.run(host='0.0.0.0', port=5002)
