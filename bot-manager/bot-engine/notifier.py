import os
import sqlite3
import db_manager
from dotenv import load_dotenv
from engine import send_msg, load_config

NOTIFY_NUMBER = "5493765245980"
LAST_CHECK_FILE = os.path.join(os.path.dirname(__file__), "last_notification_time.txt")

def get_last_messages(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.phone_number, m.content, MAX(m.timestamp) as last_time
        FROM messages m
        JOIN contacts c ON m.contact_id = c.id
        WHERE m.sender = 'client' AND c.phone_number != '5493765245980'
        GROUP BY c.phone_number
        ORDER BY last_time DESC
        LIMIT 5
    ''')
    return cursor.fetchall()

def main():
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    
    conn = None
    try:
        conn = db_manager.get_db_connection()
        messages = get_last_messages(conn)
        
        if not messages:
            return

        last_check = ""
        if os.path.exists(LAST_CHECK_FILE):
            with open(LAST_CHECK_FILE, "r") as f:
                last_check = f.read().strip()
                
        newest_msg_time = messages[0]['last_time']
        
        if not last_check or newest_msg_time > last_check:
            text_lines = ["🔔 *Nuevos mensajes detectados* 🔔\nÚltimos activos:\n"]
            for row in messages:
                phone = row['phone_number']
                content = row['content']
                if content is None:
                    content = "(Archivo/Media)"
                elif len(content) > 50:
                    content = content[:47] + "..."
                text_lines.append(f"📱 {phone}:\n💬 {content}\n")
                
            notification_text = "\n".join(text_lines)
            
            cfg = load_config()
            send_msg(cfg, NOTIFY_NUMBER, notification_text, sender_type='bot')
            
            with open(LAST_CHECK_FILE, "w") as f:
                f.write(newest_msg_time)
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
