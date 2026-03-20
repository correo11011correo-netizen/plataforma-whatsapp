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

def upload_media(cfg, file_stream, filename, mime_type):
    """Sube un archivo a la API de WhatsApp y devuelve el ID del media."""
    url = f"https://graph.facebook.com/v19.0/{cfg['phone_id']}/media"
    headers = {"Authorization": f"Bearer {cfg['token']}"}
    files = {'file': (filename, file_stream, mime_type)}
    data = {'messaging_product': 'whatsapp'}
    
    try:
        r = requests.post(url, headers=headers, files=files, data=data)
        r.raise_for_status()
        return r.json().get('id')
    except Exception as e:
        print(f"❌ Error subiendo media a Meta: {e}")
        if hasattr(e, 'response') and e.response:
            print("Detalle de Meta:", e.response.text)
        return None

def send_media_msg(cfg, to, media_id, media_type, filename="", caption="", sender_type='bot'):
    """Envía un archivo adjunto usando el media ID obtenido."""
    url = f"https://graph.facebook.com/v19.0/{cfg['phone_id']}/messages"
    headers = {"Authorization": f"Bearer {cfg['token']}", "Content-Type": "application/json"}
    
    if 'image' in media_type: wapp_type = 'image'
    elif 'video' in media_type: wapp_type = 'video'
    elif 'audio' in media_type: wapp_type = 'audio'
    else: wapp_type = 'document'

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": wapp_type,
        wapp_type: {"id": media_id}
    }
    
    if caption:
        payload[wapp_type]['caption'] = caption
    if wapp_type == 'document' and filename:
        payload[wapp_type]['filename'] = filename
        
    try:
        r = requests.post(url, headers=headers, json=payload)
        r.raise_for_status()
        print(f"✅ Archivo ({wapp_type}) enviado a {to}")
        msg_text = f"📎 [Archivo: {wapp_type}] {caption}".strip()
        db_manager.add_message(to, sender_type, msg_text)
        return True
    except Exception as e:
        print(f"❌ Error enviando archivo al chat: {e}")
        if hasattr(e, 'response') and e.response:
            print("Detalle de Meta:", e.response.text)
        return False

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
        if text in ["!humano", "humano", "asesor", "contacto", "hablar con alguien", "hablar con asesor"]:
            db_manager.set_human_intervention_status(sender, True)
            response_body = "🤖 Te estoy transfiriendo con un asesor. Te responderemos por aquí a la brevedad. 🙋"
            db_manager.add_message(sender, 'bot', response_body)
            send_msg(cfg, sender, response_body)
            try:
                # Notificar al admin inmediatamente
                send_msg(cfg, "5493765245980", f"🚨 *¡ATENCIÓN!* 🚨\nEl número {sender} ha solicitado hablar con un asesor.", sender_type='bot')
            except Exception:
                pass
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
        has_been_welcomed = state.get("welcomed", False)
        emoji_map = {"1":"1️⃣","2":"2️⃣","3":"3️⃣","4":"4️⃣","5":"5️⃣","6":"6️⃣","7":"7️⃣","8":"8️⃣","9":"9️⃣"}

        # 1. BIENVENIDA Y MENÚ PRINCIPAL (Primer Mensaje)
        if text in ["/start", "hola", "buenas"] or not has_been_welcomed:
            clear(sender)
            set_state(sender, {"welcomed": True})
            
            # Solo mandamos texto de bienvenida explícito si dijeron hola o es su primer mensaje real
            if text in ["/start", "hola", "buenas"]:
                welcome_text = db_manager.get_bot_setting("welcome_message", "👋 ¡Hola! Soy tu asistente virtual.")
                db_manager.add_message(sender, 'bot', welcome_text)
                send_msg(cfg, sender, welcome_text)
            
            main_menu_text = db_manager.get_bot_setting("main_menu_text", "Por favor, selecciona una categoría:")
            if all_menus:
                cat_list = []
                for idx, m in enumerate(all_menus, 1):
                    num_emoji = emoji_map.get(str(idx), f"*[ {idx} ]*")
                    cat_list.append(f"{num_emoji} *{m['name'].upper()}*\n└ {m['description'] or 'Sin descripción'}")
                full_msg = f"{main_menu_text}\n\n" + "\n\n".join(cat_list) + "\n\n━━━━━━━━━━━━━━\n👉 _Responde con el número de la categoría_"
            else:
                full_msg = f"{main_menu_text}\n\n_(Aún no hay categorías configuradas)_"
            
            db_manager.add_message(sender, 'bot', full_msg)
            send_msg(cfg, sender, full_msg)
            continue
            
        # 2. VOLVER AL MENÚ PRINCIPAL VÍA COMANDO
        if text in ["menu", "opciones", "volver", "menú"]:
            clear(sender)
            set_state(sender, {"welcomed": True})
            main_menu_text = db_manager.get_bot_setting("main_menu_text", "Aquí tienes nuestras categorías principales:")
            if all_menus:
                cat_list = []
                for idx, m in enumerate(all_menus, 1):
                    num_emoji = emoji_map.get(str(idx), f"*[ {idx} ]*")
                    cat_list.append(f"{num_emoji} *{m['name'].upper()}*\n└ {m['description'] or 'Sin descripción'}")
                full_msg = f"{main_menu_text}\n\n" + "\n\n".join(cat_list) + "\n\n━━━━━━━━━━━━━━\n👉 _Responde con el número de la categoría_"
            else:
                full_msg = f"{main_menu_text}\n\n_(No hay categorías)_"
                
            db_manager.add_message(sender, 'bot', full_msg)
            send_msg(cfg, sender, full_msg)
            continue

        # 3. NAVEGACIÓN DENTRO DE UN MENÚ (Verifica número o palabra clave)
        if current_menu_name and current_menu_name in menu_dict:
            active_menu = menu_dict[current_menu_name]
            chosen_opt = None
            for idx, o in enumerate(active_menu.get("options", []), 1):
                # Coincide si el texto es el número de índice, el option_key configurado o el option_text
                if text == str(idx) or text == str(o['option_key']).lower() or text == str(o['option_text']).lower():
                    chosen_opt = o
                    break
            
            if chosen_opt:
                action = chosen_opt['action_type']
                payload = chosen_opt['action_payload']
                
                if action == 'text':
                    msg = f"{payload}\n\n━━━━━━━━━━━━━━\n👉 _Escribe *asesor* para hablar con nosotros, o *volver* al menú_"
                    db_manager.add_message(sender, 'bot', msg)
                    send_msg(cfg, sender, msg)
                elif action == 'image' or action == 'document':
                    url_media = f"https://graph.facebook.com/v19.0/{cfg['phone_id']}/messages"
                    headers_media = {"Authorization": f"Bearer {cfg['token']}", "Content-Type": "application/json"}
                    
                    media_type = 'image' if action == 'image' else 'document'
                    payload_media = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": media_type,
                        media_type: {"link": payload}
                    }
                    try:
                        r = requests.post(url_media, headers=headers_media, json=payload_media)
                        r.raise_for_status()
                        msg_log = f"📎 [Archivo Automático: {payload}]"
                        db_manager.add_message(sender, 'bot', msg_log)
                    except Exception as e:
                        print(f"❌ Error enviando media automático: {e}")
                        send_msg(cfg, sender, "⚠️ El archivo adjunto no está disponible actualmente.")
                        
                elif action == 'inventory':
                    inventory_items = db_manager.get_all_inventory()
                    if not inventory_items:
                        msg = "📦 *CATÁLOGO*\n\nEl catálogo está vacío actualmente."
                    else:
                        msg = "📦 *CATÁLOGO DE PRODUCTOS / SERVICIOS*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
                        for item in inventory_items:
                            marca_modelo = f"{item['marca']} {item['modelo']}".strip()
                            msg += f"🔹 *{item['reparacion']}*\n"
                            if marca_modelo: msg += f"   • {marca_modelo}\n"
                            msg += f"   • Precio: *${item['precio']}*\n"
                            if item['stock'] > 0: msg += f"   • Stock: {item['stock']} un.\n"
                            msg += "\n"
                        msg += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n👉 _Escribe *asesor* para comprar, o *volver* al menú_"
                    db_manager.add_message(sender, 'bot', msg)
                    send_msg(cfg, sender, msg)
                elif action == 'submenu':
                    if payload.lower() in menu_dict:
                        next_menu = menu_dict[payload.lower()]
                        set_state(sender, {"current_menu": payload.lower(), "welcomed": True})
                        next_opts = next_menu.get("options", [])
                        
                        opts_text_lines = []
                        for o_idx, opt in enumerate(next_opts, 1):
                            num_emoji = emoji_map.get(str(o_idx), f"*[ {o_idx} ]*")
                            opts_text_lines.append(f"{num_emoji} *{opt['option_text']}*")
                        opts_text = "\n".join(opts_text_lines)
                        
                        msg = f"📍 Estás en: *{next_menu['name'].upper()}*\n_{next_menu['description']}_\n\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n{opts_text}\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n👉 _(Marca un número o escribe 'volver' para ir al inicio)_"
                        db_manager.add_message(sender, 'bot', msg)
                        send_msg(cfg, sender, msg)
                    else:
                        err = f"⚠️ El submenú '{payload}' no existe."
                        db_manager.add_message(sender, 'bot', err)
                        send_msg(cfg, sender, err)
                continue
            else:
                err = "⚠️ Opción inválida. Escribe un número válido o 'volver' para salir."
                db_manager.add_message(sender, 'bot', err)
                send_msg(cfg, sender, err)
                continue

        # 4. CAMBIO DE CATEGORÍA DESDE CUALQUIER LADO (Por número en el main menu, o por nombre siempre)
        target_menu = None
        for idx, m in enumerate(all_menus, 1):
            # Solo permite salto por número si no está en un submenú actual (para evitar conflictos de números)
            if (not current_menu_name and text == str(idx)) or text == m['name'].lower():
                target_menu = m
                break
                
        if target_menu:
            set_state(sender, {"current_menu": target_menu['name'].lower(), "welcomed": True})
            options = target_menu.get("options", [])
            
            opts_text_lines = []
            for o_idx, opt in enumerate(options, 1):
                num_emoji = emoji_map.get(str(o_idx), f"*[ {o_idx} ]*")
                opts_text_lines.append(f"{num_emoji} *{opt['option_text']}*")
            opts_text = "\n".join(opts_text_lines)
            
            msg = f"📍 Estás en: *{target_menu['name'].upper()}*\n{target_menu['description']}\n\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n{opts_text}\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n👉 _(Responde con el número de opción, o escribe 'volver' para ir al inicio)_"
            db_manager.add_message(sender, 'bot', msg)
            send_msg(cfg, sender, msg)
            continue

        # 5. MENSAJE NO RECONOCIDO (FALLBACK)
        fallback_msg = db_manager.get_bot_setting("fallback_message", "No he entendido ese mensaje. Escribe 'menu' para ver las opciones disponibles.")
        db_manager.add_message(sender, 'bot', fallback_msg)
        send_msg(cfg, sender, fallback_msg)
