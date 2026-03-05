import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BOT_ENGINE_PATH = os.path.join(PROJECT_ROOT, 'bot-engine')

if BOT_ENGINE_PATH not in sys.path:
    sys.path.insert(0, BOT_ENGINE_PATH)

import db_manager

def main():
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
        conversations = cursor.fetchall()
        print(f"Total conversations found in DB: {len(conversations)}")
        for conv in conversations:
            print(dict(conv))
    except Exception as e:
        print(f"Error querying DB: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
