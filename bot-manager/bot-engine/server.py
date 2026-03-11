import os
import json
import requests
import sqlite3
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv
from engine import setup_logging, load_submenu_flows, load_config, process_message, send_msg
from flows.messenger import handle_messenger
import db_manager

# --- Paths Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_UI_PATH = os.path.join(BASE_DIR, '../dashboard-ui')
DB_PATH = os.path.join(BASE_DIR, '../database/bot_dashboard.db')

# Initialize Flask
app = Flask(__name__, template_folder=DASHBOARD_UI_PATH, static_folder=DASHBOARD_UI_PATH)

# --- Cargar configuración al iniciar la aplicación (para Gunicorn) ---
load_dotenv()
setup_logging()
load_submenu_flows()
try:
    app.config["cfg"] = load_config()
    print("✅ Configuración cargada exitosamente para Gunicorn.")
except Exception as e:
    print(f"❌ Error al cargar la configuración para Gunicorn: {e}")
    app.config["cfg"] = {}

# --- Database Utilities for Dashboard ---
def get_db_connection():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Bot Webhook Endpoints ---
@app.route("/api/webhook", methods=["GET"])
def verify_whatsapp_instagram():
    cfg = app.config.get("cfg", {})
    verify_token = cfg.get("verify", os.getenv("VERIFY_TOKEN"))
    if request.args.get("hub.verify_token") == verify_token:
        return request.args.get("hub.challenge")
    return ("Token mismatch WhatsApp/Instagram", 403)

@app.route("/api/webhook", methods=["POST"])
def webhook_whatsapp_instagram():
    cfg = app.config["cfg"]
    data = request.get_json()
    print(f"---------- MENSAJE RECIBIDO EN BOT-ENGINE ----------")
    print(json.dumps(data, indent=2))
    print(f"----------------------------------------------------")
    process_message(cfg, data)
    return "OK", 200

# --- Dashboard Frontend & API Endpoints ---
@app.route('/')
def serve_dashboard():
    ngrok_url = app.config.get("cfg", {}).get("ngrok_public_url", "")
    return render_template('index.html', NGROK_URL=ngrok_url)

@app.route('/<path:path>')
def serve_dashboard_static_files(path):
    return send_from_directory(DASHBOARD_UI_PATH, path)
    
@app.route("/api/conversations", methods=["GET"])
def get_conversations():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.phone_number, c.name, conv.is_human_intervening,
                   (SELECT content FROM messages WHERE contact_id = c.id ORDER BY timestamp DESC LIMIT 1) as last_message,
                   (SELECT timestamp FROM messages WHERE contact_id = c.id ORDER BY timestamp DESC LIMIT 1) as last_timestamp
            FROM contacts c
            LEFT JOIN conversations conv ON c.id = conv.contact_id
            ORDER BY last_timestamp DESC
        ''')
        rows = cursor.fetchall()
        conversations = []
        for row in rows:
            # Check if conversation actually has messages, otherwise skip or handle gracefully.
            # SQLite max/min on empty sets can return null timestamps
            if row["last_timestamp"]:
               conversations.append({
                   "phone_number": row["phone_number"],
                   "name": row["name"] or row["phone_number"],
                   "is_human_intervening": bool(row["is_human_intervening"]),
                   "last_message": row["last_message"],
                   "last_timestamp": row["last_timestamp"]
               })
        return jsonify(conversations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

import logging

# Configurar logging detallado
logging.basicConfig(
    filename='delete_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

@app.route("/api/conversations/delete", methods=["POST", "OPTIONS"])
def delete_conversation():
    if request.method == "OPTIONS":
        return "", 200

    logging.info("--- Iniciando peticion de borrado ---")
    try:
        logging.info(f"Headers recibidos: {dict(request.headers)}")
        data = request.get_json(force=True, silent=True)
        logging.info(f"Datos parseados (JSON): {data}")

        if not data:
            logging.error("No se recibieron datos JSON válidos.")
            return jsonify({"error": "Formato JSON invalido o vacio"}), 400

        phone_number = data.get("phone_number")
        if not phone_number:
            logging.error("El campo phone_number no esta presente en los datos.")
            return jsonify({"error": "Phone number is required"}), 400

        logging.info(f"Intentando borrar conversacion para el numero: {phone_number}")
        success = db_manager.delete_conversation(phone_number)
        
        if success:
            logging.info(f"Exito al borrar {phone_number} en la base de datos.")
            return jsonify({"status": "success", "message": "Conversación eliminada."}), 200
        else:
            logging.warning(f"La funcion de base de datos devolvio False para {phone_number}.")
            return jsonify({"error": "Conversación no encontrada en base de datos."}), 404

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"Excepcion critica al borrar:\n{error_details}")
        return jsonify({"error": str(e), "traceback": error_details}), 500

@app.route("/api/messages/<string:phone_number>", methods=["GET"])
def get_messages(phone_number):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.sender, m.content, m.timestamp
            FROM messages m
            JOIN contacts c ON m.contact_id = c.id
            WHERE c.phone_number = ?
            ORDER BY m.timestamp ASC
        ''', (phone_number,))
        rows = cursor.fetchall()
        messages = [{"sender": row["sender"], "content": row["content"], "timestamp": row["timestamp"]} for row in rows]
        return jsonify(messages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route("/api/send_message_from_dashboard", methods=["POST"])
def send_message_from_dashboard():
    cfg = app.config["cfg"]
    data = request.get_json()
    phone_number = data.get("phone_number")
    content = data.get("content")
    
    if not phone_number or not content:
        return jsonify({"error": "phone_number and content required"}), 400
        
    try:
        # Send via WhatsApp API and log as human
        send_msg(cfg, phone_number, content, sender_type='human')
        return jsonify({"status": "success", "message": "Enviado correctamente."}), 200
    except Exception as e:
        print(f"Error sending message from dashboard: {e}")
        return jsonify({"error": str(e)}), 500

# --- NUEVA RUTA DE API PARA INTERVENCIÓN ---
@app.route("/api/intervention", methods=["POST"])
def set_intervention():
    data = request.get_json()
    phone_number = data.get("phone_number")
    status = data.get("status") # Debería ser True o False

    if not phone_number or status is None:
        return jsonify({"error": "phone_number and status son requeridos."}), 400

    try:
        db_manager.set_human_intervention_status(phone_number, status)
        return jsonify({"status": "success", "message": f"Intervención para {phone_number} establecida a {status}."}), 200
    except Exception as e:
        print(f"Error al establecer intervención: {e}")
        return jsonify({"error": str(e)}), 500
# --- FIN DE NUEVA RUTA ---


# --- NUEVAS RUTAS PARA CONFIGURACIÓN ---
@app.route('/api/settings', methods=['GET'])
def get_settings():
    try:
        settings = db_manager.get_all_bot_settings()
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['POST'])
def update_settings():
    data = request.get_json()
    try:
        for key, value in data.items():
            db_manager.update_bot_setting(key, value)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/menus', methods=['GET'])
def get_menus():
    try:
        menus = db_manager.get_all_menus()
        return jsonify(menus)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/menus', methods=['POST'])
def create_menu():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    try:
        menu_id = db_manager.create_menu(name, description)
        if menu_id:
            return jsonify({'status': 'success', 'id': menu_id}), 201
        return jsonify({'error': 'Could not create menu'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/menus/<int:menu_id>', methods=['DELETE'])
def delete_menu(menu_id):
    try:
        if db_manager.delete_menu(menu_id):
            return jsonify({'status': 'success'})
        return jsonify({'error': 'Could not delete menu'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/menus/<int:menu_id>/options', methods=['POST'])
def create_menu_option(menu_id):
    data = request.get_json()
    option_key = data.get('option_key')
    option_text = data.get('option_text')
    action_type = data.get('action_type', 'text')
    action_payload = data.get('action_payload', '')
    
    if not option_key or not option_text:
        return jsonify({'error': 'option_key and option_text are required'}), 400
        
    try:
        option_id = db_manager.create_menu_option(menu_id, option_key, option_text, action_type, action_payload)
        if option_id:
            return jsonify({'status': 'success', 'id': option_id}), 201
        return jsonify({'error': 'Could not create option'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/options/<int:option_id>', methods=['DELETE'])
def delete_menu_option(option_id):
    try:
        if db_manager.delete_menu_option(option_id):
            return jsonify({'status': 'success'})
        return jsonify({'error': 'Could not delete option'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# --- FIN NUEVAS RUTAS ---

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    print(f"🚀 Servidor del Bot Engine (ejecución manual) en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)