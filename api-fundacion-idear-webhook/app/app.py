import json
import logging
import requests
from flask import Flask, request, jsonify, render_template, Response

# --- Basic Setup ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/dashboard/api/<path:path>', methods=['GET', 'POST', 'DELETE', 'OPTIONS'])
def proxy_dashboard_api(path):
    if request.method == 'OPTIONS':
        return '', 200
    
    url = f"http://127.0.0.1:5001/api/{path}"
    
    try:
        if request.method == 'GET':
            resp = requests.get(url)
        elif request.method == 'POST':
            resp = requests.post(url, json=request.get_json())
        elif request.method == 'DELETE':
            resp = requests.delete(url)
            
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        
        return Response(resp.content, resp.status_code, headers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Global Variable for Last Request Time ---
# last_webhook_time = None # No usado en esta version simplificada

# --- Forced Configuration for Debugging ---
VERIFY_TOKEN = "fundacionidear2026" 
FORWARD_URL = "http://127.0.0.1:5001/api/webhook"
# --- End Forced Configuration ---

# --- Webhook Endpoint ---
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """
    Handles Meta's webhook requests.
    - GET: Used for the initial verification challenge.
    - POST: Used to receive and forward incoming messages.
    """
    # global last_webhook_time # No usado en esta version simplificada
    # last_webhook_time = datetime.now() # No usado en esta version simplificada

    if request.method == 'GET':
        if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == VERIFY_TOKEN:
            logging.info("Webhook verification successful! (Forwarder)")
            return request.args.get('hub.challenge'), 200
        else:
            logging.warning("Webhook verification failed. Token mismatch. (Forwarder)")
            return 'Verification token mismatch', 403

    if request.method == 'POST':
        data = request.get_json()
        
        if FORWARD_URL:
            logging.info(f"Received webhook. Forwarding to {FORWARD_URL}...")
            try:
                requests.post(FORWARD_URL, json=data, timeout=5)
                logging.info("Webhook forwarded successfully.")
            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to forward webhook to {FORWARD_URL}: {e}")
            
        else:
            logging.warning("No FORWARD_URL configured. Not forwarding webhook.")
        
        return 'OK', 200

# --- Dashboard Endpoint ---
@app.route('/dashboard')
def dashboard():
    """
    Renders the simple status dashboard.
    """
    return render_template('dashboard.html')

# --- Health Check Endpoint ---
@app.route('/health', methods=['GET'])
def health_check():
    """
A simple endpoint to confirm the service is running.
"""
    return jsonify({"status": "ok", "name": "webhook-forwarder"}), 200

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
