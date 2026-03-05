import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# --- Configurar Path para usar la lógica del Bot Engine en vivo ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BOT_ENGINE_PATH = os.path.join(PROJECT_ROOT, 'bot-engine')

if BOT_ENGINE_PATH not in sys.path:
    sys.path.insert(0, BOT_ENGINE_PATH)

import db_manager
from engine import load_config, send_msg

def clear_screen():
    """Limpia la terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_main_menu():
    """Muestra el menú principal."""
    clear_screen()
    print("=== Terminal Chat Manager (Conectado a SQLite DB) ===")
    print("1. Ver Chats Activos")
    print("2. Salir")
    print("=====================================================")

def get_conversations():
    """Obtiene todas las conversaciones escaneando la base de datos."""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT
            c.id AS contact_id,
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
    try:
        cursor.execute(query)
        conversations = [dict(row) for row in cursor.fetchall()]
        return conversations
    except Exception as e:
        print(f"Error reading DB: {e}")
        return []
    finally:
        conn.close()

def display_conversations(conversations):
    clear_screen()
    print("=== Chats Activos (Leídos desde la base de datos) ===")
    if not conversations:
        print("No hay conversaciones activas. El bot aún no ha recibido mensajes.")
        print("---------------------")
        return

    for i, conv in enumerate(conversations):
        status = "HUMANO (Bot Pausado)" if conv['is_human_intervening'] else "BOT (Activo)"
        last_msg = conv['last_message_content'] if conv['last_message_content'] else "Sin mensajes"
        name = conv['name'] if conv['name'] else conv['phone_number']
        print(f"{i+1}. Número: {name} | Estado actual: {status}")
        print(f"   Último registro: '{last_msg}'")
    print("---------------------")

def get_messages_for_contact(phone_number):
    """Lee el historial completo de mensajes desde la DB"""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT
            m.sender,
            m.content,
            m.timestamp
        FROM messages m
        JOIN contacts c ON m.contact_id = c.id
        WHERE c.phone_number = ?
        ORDER BY m.timestamp ASC;
    """
    try:
        cursor.execute(query, (phone_number,))
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error reading messages: {e}")
        return []
    finally:
        conn.close()

def display_chat_history(contact_info, messages):
    clear_screen()
    name = contact_info['name'] if contact_info['name'] else contact_info['phone_number']
    print(f"=== Historial de Chat con {name} ===")
    print(f"Estado: {'HUMANO (Bot Pausado)' if contact_info['is_human_intervening'] else 'BOT (Activo)'}")
    print("---------------------------------")
    for msg in messages:
        try:
            timestamp = datetime.strptime(msg['timestamp'], '%Y-%m-%d %H:%M:%S.%f').strftime('%H:%M:%S')
        except ValueError:
            try:
                timestamp = datetime.strptime(msg['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')
            except ValueError:
                timestamp = msg['timestamp']
        
        sender_label = "Tú (Humano)" if msg['sender'] == 'human' else "Bot" if msg['sender'] == 'bot' else "Cliente"
        print(f"[{timestamp}] {sender_label}: {msg['content']}")
    print("---------------------------------")

def manage_chat(cfg, contact_info):
    while True:
        phone_number = contact_info['phone_number']
        messages = get_messages_for_contact(phone_number)
        
        # Leer estado actual de intervención desde BD
        is_intervening = db_manager.get_conversation_status(phone_number)
        contact_info['is_human_intervening'] = is_intervening

        display_chat_history(contact_info, messages)

        print("\nOpciones:")
        print("1. Responder mensaje")
        print("2. Alternar estado (Pausar/Reanudar Bot para este usuario)")
        print("3. Actualizar pantalla de Chat")
        print("4. Volver al menú principal")

        choice = input("Elige una opción: ")

        if choice == '1':
            message = input("Escribe tu mensaje: ")
            if message.strip():
                print("Enviando mensaje vía Meta API...")
                
                # Enviar el mensaje usando las credenciales del bot
                send_msg(cfg, phone_number, message)
                
                # Forzar en BD que el registro sea 'human'
                conn = db_manager.get_db_connection()
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
                    
                print("✅ Mensaje enviado y registrado en la base de datos como humano.")
            input("Presiona Enter para continuar...")
            
        elif choice == '2':
            new_status = not is_intervening
            db_manager.set_human_intervention_status(phone_number, new_status)
            print(f"✅ Estado de intervención cambiado a: {'Pausado (Humano)' if new_status else 'Activo (Bot)'}")
            input("Presiona Enter para continuar...")
            
        elif choice == '3':
            pass
            
        elif choice == '4':
            break
        else:
            print("Opción inválida.")
            input("Presiona Enter para continuar...")

def main():
    # Cargar .env desde el motor
    env_path = os.path.join(BOT_ENGINE_PATH, '.env')
    load_dotenv(dotenv_path=env_path)
    
    # Cargar Configuración del bot engine
    cfg = load_config()

    while True:
        display_main_menu()
        choice = input("Elige una opción (1 o 2): ")

        if choice == '1':
            conversations = get_conversations()
            if not conversations:
                print("\nNo hay conversaciones activas en la base de datos.")
                print("Asegúrate de que alguien haya enviado un mensaje al bot.")
                input("Presiona Enter para volver.")
                continue
            
            display_conversations(conversations)
            chat_choice = input("Elige el número del chat para gestionar (o 'q' para volver): ")
            if chat_choice.lower() == 'q':
                continue
            
            try:
                chat_index = int(chat_choice) - 1
                if 0 <= chat_index < len(conversations):
                    manage_chat(cfg, conversations[chat_index])
                else:
                    print("Número de chat inválido.")
                    input("Presiona Enter para continuar...")
            except ValueError:
                print("Entrada inválida.")
                input("Presiona Enter para continuar...")

        elif choice == '2':
            print("Saliendo del Chat Manager.")
            sys.exit(0)
        else:
            print("Opción inválida.")
            input("Presiona Enter para continuar...")

if __name__ == '__main__':
    main()
