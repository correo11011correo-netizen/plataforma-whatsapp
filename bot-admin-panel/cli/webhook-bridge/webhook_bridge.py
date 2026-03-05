from flask import Flask, request, jsonify
import os
import json

app = Flask(__name__)

# This is the token you set in the Meta App Dashboard
# It should be loaded from an environment variable for security
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "bot1234")

@app.route('/api/webhook', methods=['GET'])
def webhook_verify():
    """
    Handles the webhook verification request from Meta.
    """
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == VERIFY_TOKEN:
        print("✅ Webhook verificada exitosamente!")
        return request.args.get('hub.challenge'), 200
    else:
        print("❌ Falló la verificación del webhook.")
        return 'Verification token mismatch', 403

@app.route('/api/webhook', methods=['POST'])
def webhook_receive():
    """
    Handles incoming messages from Meta.
    """
    data = request.get_json()
    print("⬇️  Webhook recibido:")
    print(json.dumps(data, indent=2))
    
    # Here you would add logic to forward this data to your actual bot engine
    # For now, we just log it and respond OK.
    
    return 'OK', 200
    
@app.route('/')
def api_status():
    return jsonify({'status': 'API de Webhook Bridge funcionando'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    print(f"🚀 Iniciando Servidor Puente de Webhook en http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
