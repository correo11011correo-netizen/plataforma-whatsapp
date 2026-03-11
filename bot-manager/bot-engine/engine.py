import os
import json
import requests
from utils import log_message, setup_logging
from flows.state import get, clear, set as set_state
import db_manager

processed_message_ids = set()

# Función vacía para que el servidor (server.py) no falle si intenta llamarla al encender
def load_submenu_flows():
    pass

def load_config():
    return {
        "token": os.getenv("WHATSAPP_BUSINESS_API_TOKEN"),
        "phone_id": "880275461842101",
        "verify": os.getenv("VERIFY_TOKEN"),
        "facebook_token": os.getenv("FACEBOOK_TOKEN"),
        "page_id": os.getenv("PAGE_ID"),
        "page_name": os.getenv("PAGE_NAME"),
        "test_recipient_id": os.getenv("TEST_RECIPIENT_ID"),
        "meta_app_id": os.getenv("META_APP_ID"),
        "meta_app_secret": os.getenv("META_APP_SECRET"),
        "ngrok_public_url": os.getenv("NGROK_PUBLIC_URL"),
        "default_test_number": os.getenv("DEFAULT_TEST_NUMBER")
    }

def send_msg(cfg, to, body, sender_type='bot'):
    url = f"https://graph.facebook.com/v19.0/{cfg['phone_id']}/messages"
    headers = {"Authorization": f"Bearer {cfg['token']}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body}}
    try:
        r = requests.post(url, headers=headers, json=payload)
        r.raise_for_status()
        print(f"✅ Enviado a {to}: {body}")
        db_manager.add_message(to, sender_type, body)
    except Exception as e:
        print(f"❌ Error enviando: {e}")

def process_message(cfg, data):
    for msg in data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", []):
        text_raw = msg.get("text", {}).get("body", "")
        text = text_raw.strip().lower()
        sender = msg.get("from")
        message_id = msg.get("id")
        
        if message_id in processed_message_ids:
            log_message(sender, f"Duplicate message_id {message_id} received, ignoring.")
            continue
        processed_message_ids.add(message_id)
        log_message(sender, text_raw)
        db_manager.add_message(sender, 'client', text_raw)

        # -- COMPROBACIÓN MODO HUMANO --
        if text == "!humano":
            db_manager.set_human_intervention_status(sender, True)
            response_body = "🤖 Pausando respuestas automáticas. Un humano tomará el control. 🙋"
            db_manager.add_message(sender, 'bot', response_body)
            send_msg(cfg, sender, response_body)
            continue
        if text == "!bot":
            db_manager.set_human_intervention_status(sender, False)
            response_body = "🙋 Devolviendo el control al bot. ¡Gracias! 🤖"
            db_manager.add_message(sender, 'bot', response_body)
            send_msg(cfg, sender, response_body)
            continue
        if db_manager.get_conversation_status(sender):
            print(f"Human is intervening in conversation with {sender}. Bot will not auto-respond.")
            continue

        # -- RECUPERAR DATOS EN VIVO DEL DASHBOARD --
        all_menus = db_manager.get_all_menus()
        menu_dict = {m['name'].lower(): m for m in all_menus}
        state = get(sender) or {}
        current_menu_name = state.get("current_menu")

        # 1. BIENVENIDA Y MENÚ PRINCIPAL
        if text in ["/start", "hola", "buenas"]:
            clear(sender)
            welcome_text = db_manager.get_bot_setting("welcome_message", "¡Hola! Soy tu asistente virtual.")
            db_manager.add_message(sender, 'bot', welcome_text)
            send_msg(cfg, sender, welcome_text)
            
            # Autodesplegar el menú principal para evitar que el usuario tenga que adivinar
            main_menu_text = db_manager.get_bot_setting("main_menu_text", "Aquí tienes nuestras categorías principales:")
            if all_menus:
                cat_list = [f"➡️ *{m['name']}*: {m['description']}" for m in all_menus]
                full_msg = f"{main_menu_text}\n\n" + "\n".join(cat_list) + "\n\n👉 _Escribe exactamente el nombre de la categoría para continuar (ej: {all_menus[0]['name']})_"
            else:
                full_msg = f"{main_menu_text}\n\n_(Aún no hay menús configurados)_"
            
            db_manager.add_message(sender, 'bot', full_msg)
            send_msg(cfg, sender, full_msg)
            continue
            
        if text in ["menu", "opciones", "volver", "menú"]:
            clear(sender)
            main_menu_text = db_manager.get_bot_setting("main_menu_text", "Aquí tienes nuestras categorías principales:")
            if all_menus:
                cat_list = [f"➡️ *{m['name']}*: {m['description']}" for m in all_menus]
                full_msg = f"{main_menu_text}\n\n" + "\n".join(cat_list) + "\n\n👉 _Escribe exactamente el nombre de la categoría para entrar (ej: {all_menus[0]['name']})_"
            else:
                full_msg = f"{main_menu_text}\n\n_(Aún no hay menús configurados)_"
                
            db_manager.add_message(sender, 'bot', full_msg)
            send_msg(cfg, sender, full_msg)
            continue

        # 2. EL USUARIO ESCRIBIÓ EL NOMBRE DE UNA CATEGORÍA DIRECTAMENTE
        if text in menu_dict:
            target_menu = menu_dict[text]
            set_state(sender, {"current_menu": text})
            options = target_menu.get("options", [])
            opts_text = "\n".join([f"*[ {opt['option_key']} ]* - {opt['option_text']}" for opt in options])
            msg = f"📍 Estás en: *{target_menu['name'].upper()}*\n{target_menu['description']}\n\n{opts_text}\n\n👉 _(Responde con el número de opción, o escribe 'volver' para ir al inicio)_"
            db_manager.add_message(sender, 'bot', msg)
            send_msg(cfg, sender, msg)
            continue

        # 3. NAVEGACIÓN DENTRO DE UN MENÚ
        if current_menu_name and current_menu_name in menu_dict:
            active_menu = menu_dict[current_menu_name]
            chosen_opt = next((o for o in active_menu.get("options", []) if str(o['option_key']).lower() == text), None)
            
            if chosen_opt:
                action = chosen_opt['action_type']
                payload = chosen_opt['action_payload']
                if action == 'text':
                    db_manager.add_message(sender, 'bot', payload)
                    send_msg(cfg, sender, payload)
                elif action == 'submenu':
                    if payload.lower() in menu_dict:
                        next_menu = menu_dict[payload.lower()]
                        set_state(sender, {"current_menu": payload.lower()})
                        next_opts = next_menu.get("options", [])
                        opts_text = "\n".join([f"*[ {opt['option_key']} ]* - {opt['option_text']}" for opt in next_opts])
                        msg = f"📍 Estás en: *{next_menu['name'].upper()}*\n{next_menu['description']}\n\n{opts_text}\n\n_(Escribe 'volver' para ir al inicio)_"
                        db_manager.add_message(sender, 'bot', msg)
                        send_msg(cfg, sender, msg)
                    else:
                        err = f"⚠️ El submenú '{payload}' no existe."
                        send_msg(cfg, sender, err)
                continue
            else:
                err = "⚠️ Opción inválida. Escribe un número válido o 'volver' para salir."
                send_msg(cfg, sender, err)
                continue

        # 4. MENSAJE NO RECONOCIDO (FALLBACK)
        fallback_msg = db_manager.get_bot_setting("fallback_message", "No he entendido ese mensaje. Escribe 'menu' para ver las opciones disponibles.")
        db_manager.add_message(sender, 'bot', fallback_msg)
        send_msg(cfg, sender, fallback_msg)