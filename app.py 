import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Configuración ---
CHATWOOT_API_URL = os.environ.get("CHATWOOT_API_URL", "https://app.chatwoot.com" )
CHATWOOT_API_ACCESS_TOKEN = os.environ.get("CHATWOOT_API_ACCESS_TOKEN")
S3_PDF_URL = os.environ.get("S3_PDF_URL")

@app.route("/chatwoot-webhook", methods=["POST"])
def chatwoot_webhook():
    data = request.json
    print(f"Webhook recibido: {data}")

    conversation_id = data.get("conversation", {}).get("id")
    account_id = data.get("account", {}).get("id")

    if not conversation_id or not account_id:
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        # Descargar PDF de S3
        pdf_response = requests.get(S3_PDF_URL, stream=True)
        pdf_response.raise_for_status()
        pdf_content = pdf_response.content
    except Exception as e:
        return jsonify({"error": f"Error S3: {e}"}), 500

    # Enviar a Chatwoot
    upload_url = f"{CHATWOOT_API_URL}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
    headers = {"api_access_token": CHATWOOT_API_ACCESS_TOKEN}
    files = {"attachments[]": ("catalogo.pdf", pdf_content, "application/pdf")}
    payload = {"message_type": "outgoing", "content": "Aquí tienes el catálogo solicitado."}

    try:
        requests.post(upload_url, headers=headers, data=payload, files=files)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": f"Error Chatwoot: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
