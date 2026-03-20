import sqlite3
import os
from datetime import datetime

# Define the path to the bot_dashboard.db file relative to the bot-dashboard project
# Assuming bot-pagina and bot-dashboard are siblings in the /home/adrian directory
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'bot_dashboard.db')

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

def add_message(phone_number, sender_type, message_content, message_type='text'):
    """
    Adds a message to the database, ensuring the contact and conversation exist.
    sender_type can be 'client', 'bot', or 'human'.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Ensure contact exists
        cursor.execute("INSERT OR IGNORE INTO contacts (phone_number) VALUES (?)", (phone_number,))
        cursor.execute("SELECT id FROM contacts WHERE phone_number = ?", (phone_number,))
        contact_id = cursor.fetchone()['id']

        # 2. Ensure conversation exists
        cursor.execute("INSERT OR IGNORE INTO conversations (contact_id) VALUES (?)", (contact_id,))

        # 3. Insert the message
        cursor.execute(
            "INSERT INTO messages (contact_id, sender, message_type, content, timestamp) VALUES (?, ?, ?, ?, ?)",
            (contact_id, sender_type, message_type, message_content, datetime.now())
        )
        conn.commit()
        print(f"Message added for {phone_number} by {sender_type}.")
    except sqlite3.Error as e:
        print(f"Database error in add_message: {e}")
    finally:
        if conn:
            conn.close()

def update_contact_name(phone_number, name):
    """Updates the name of a contact."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE contacts SET name = ? WHERE phone_number = ?", (name, phone_number))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in update_contact_name: {e}")
    finally:
        if conn:
            conn.close()

def get_conversation_status(phone_number):
    """
    Retrieves the human intervention status for a given phone number.
    Returns True if human is intervening, False otherwise.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.is_human_intervening
            FROM conversations c
            JOIN contacts co ON c.contact_id = co.id
            WHERE co.phone_number = ?
            """,
            (phone_number,)
        )
        result = cursor.fetchone()
        if result:
            return bool(result['is_human_intervening'])
        return False # No conversation entry found, so no intervention
    except sqlite3.Error as e:
        print(f"Database error in get_conversation_status: {e}")
        return False
    finally:
        if conn:
            conn.close()

def set_human_intervention_status(phone_number, status):
    """
    Sets the human intervention status for a given phone number.
    status should be True or False.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ensure contact and conversation exist first
        cursor.execute("INSERT OR IGNORE INTO contacts (phone_number) VALUES (?)", (phone_number,))
        cursor.execute("SELECT id FROM contacts WHERE phone_number = ?", (phone_number,))
        contact_id = cursor.fetchone()['id']
        cursor.execute("INSERT OR IGNORE INTO conversations (contact_id) VALUES (?)", (contact_id,))

        cursor.execute(
            """
            UPDATE conversations
            SET is_human_intervening = ?, last_updated = ?
            WHERE contact_id = (SELECT id FROM contacts WHERE phone_number = ?)
            """,
            (1 if status else 0, datetime.now(), phone_number)
        )
        conn.commit()
        print(f"Human intervention status for {phone_number} set to {status}.")
    except sqlite3.Error as e:
        print(f"Database error in set_human_intervention_status: {e}")
    finally:
        if conn:
            conn.close()


def get_bot_setting(key, default_value=""):
    """Retrieves a setting from the bot_settings table."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM bot_settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        if result:
            return result['value']
        return default_value
    except sqlite3.Error as e:
        print(f"Database error in get_bot_setting: {e}")
        return default_value
    finally:
        if conn:
            conn.close()

def update_bot_setting(key, value):
    """Updates a setting in the bot_settings table."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO bot_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in update_bot_setting: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_all_bot_settings():
    """Retrieves all settings from the bot_settings table as a dictionary."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM bot_settings")
        results = cursor.fetchall()
        return {row['key']: row['value'] for row in results}
    except sqlite3.Error as e:
        print(f"Database error in get_all_bot_settings: {e}")
        return {}
    finally:
        if conn:
            conn.close()



def get_all_menus():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM menus")
        menus = [dict(row) for row in cursor.fetchall()]
        for menu in menus:
            cursor.execute("SELECT * FROM menu_options WHERE menu_id = ?", (menu['id'],))
            menu['options'] = [dict(row) for row in cursor.fetchall()]
        return menus
    except sqlite3.Error as e:
        print(f"Database error in get_all_menus: {e}")
        return []
    finally:
        if conn:
            conn.close()

def create_menu(name, description):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO menus (name, description) VALUES (?, ?)", (name, description))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Database error in create_menu: {e}")
        return None
    finally:
        if conn:
            conn.close()

def delete_menu(menu_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM menu_options WHERE menu_id = ?", (menu_id,))
        cursor.execute("DELETE FROM menus WHERE id = ?", (menu_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in delete_menu: {e}")
        return False
    finally:
        if conn:
            conn.close()

def create_menu_option(menu_id, option_key, option_text, action_type, action_payload):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO menu_options (menu_id, option_key, option_text, action_type, action_payload) VALUES (?, ?, ?, ?, ?)",
            (menu_id, option_key, option_text, action_type, action_payload)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Database error in create_menu_option: {e}")
        return None
    finally:
        if conn:
            conn.close()

def delete_menu_option(option_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM menu_options WHERE id = ?", (option_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in delete_menu_option: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_conversation(phone_number):
    """
    Deletes a conversation and all its messages based on the phone number.
    Returns True if successful, False otherwise.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Obtener el contact_id primero
        cursor.execute("SELECT id FROM contacts WHERE phone_number = ?", (phone_number,))
        contact_row = cursor.fetchone()

        if contact_row:
            contact_id = contact_row['id']
            # Borrar mensajes primero por la llave foránea
            cursor.execute("DELETE FROM messages WHERE contact_id = ?", (contact_id,))
            # Borrar la conversación
            cursor.execute("DELETE FROM conversations WHERE contact_id = ?", (contact_id,))
            conn.commit()
            return True
        else:
            print(f"No se encontró el contacto {phone_number} para borrar.")
            return False

    except sqlite3.Error as e:
        print(f"Database error deleting conversation {phone_number}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_all_inventory():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventory WHERE is_active = 1")
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error in get_all_inventory: {e}")
        return []
    finally:
        if conn:
            conn.close()

def add_inventory_item(marca, modelo, reparacion, precio, stock=0):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO inventory (marca, modelo, reparacion, precio, stock) VALUES (?, ?, ?, ?, ?)",
            (marca, modelo, reparacion, precio, stock)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Database error in add_inventory_item: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_inventory_item(item_id, marca, modelo, reparacion, precio, stock):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE inventory SET marca=?, modelo=?, reparacion=?, precio=?, stock=? WHERE id=?",
            (marca, modelo, reparacion, precio, stock, item_id)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in update_inventory_item: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_inventory_item(item_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in delete_inventory_item: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':

    # Example usage:
    # Ensure the bot-dashboard/backend directory exists and run the Node.js backend to create the DB first
    print(f"Database path: {DB_PATH}")
    # connect_db() # This would initialize the db, but the Node.js backend should do it first

    # Test adding messages
    # add_message('5491123456789', 'client', 'Hola bot!', 'text')
    # add_message('5491123456789', 'bot', 'Hola, ¿en qué puedo ayudarte?', 'text')
    # add_message('5491198765432', 'client', 'Necesito información.', 'text')

    # Test updating contact name
    # update_contact_name('5491123456789', 'Juan Perez')

    # Test intervention status
    # print(f"Is 5491123456789 intervened? {get_conversation_status('5491123456789')}")
    # set_human_intervention_status('5491123456789', True)
    # print(f"Is 5491123456789 intervened? {get_conversation_status('5491123456789')}")
    # set_human_intervention_status('5491123456789', False)
    # print(f"Is 5491123456789 intervened? {get_conversation_status('5491123456789')}")
