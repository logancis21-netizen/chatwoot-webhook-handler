import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

CHATWOOT_API_URL = os.environ.get("CHATWOOT_API_URL", "https://app.chatwoot.com/api/v1").rstrip("/")
CHATWOOT_API_ACCESS_TOKEN = os.environ.get("CHATWOOT_API_ACCESS_TOKEN")
S3_PDF_URL = os.environ.get("S3_PDF_URL")

@app.route("/chatwoot-webhook", methods=["POST"])
def chatwoot_webhook():
    data = request.get_json(silent=True) or {}
    print(f"Webhook recibido: {data}", flush=True)

    conversation = data.get("conversation", {}) or {}

    conversation_id = conversation.get("id")
    account_id = (
        conversation.get("account_id")
        or data.get("account", {}).get("id")
    )

    if not conversation_id or not account_id:
        print("Error: conversation_id o account_id no encontrados en el webhook", flush=True)
        return jsonify({
            "error": "conversation_id o account_id no encontrados en el webhook",
            "payload_recibido": data
        }), 400

    if not CHATWOOT_API_ACCESS_TOKEN:
        print("Error: CHATWOOT_API_ACCESS_TOKEN no configurado", flush=True)
        return jsonify({"error": "CHATWOOT_API_ACCESS_TOKEN no configurado"}), 500

    if not S3_PDF_URL:
        print("Error: S3_PDF_URL no configurado", flush=True)
        return jsonify({"error": "S3_PDF_URL no configurado"}), 500

    try:
        pdf_response = requests.get(S3_PDF_URL, timeout=30)
        pdf_response.raise_for_status()
        pdf_content = pdf_response.content
        print(f"PDF descargado de S3: {S3_PDF_URL}", flush=True)
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar PDF de S3: {e}", flush=True)
        return jsonify({"error": f"Error al descargar PDF de S3: {e}"}), 500

    upload_url = f"{CHATWOOT_API_URL}/accounts/{account_id}/conversations/{conversation_id}/messages"
    headers = {
        "api_access_token": CHATWOOT_API_ACCESS_TOKEN,
    }
    files = {
        "attachments[]": ("catalogo.pdf", pdf_content, "application/pdf")
    }
    payload = {
        "message_type": "outgoing",
        "content": "Aquí tienes el catálogo solicitado."
    }

    try:
        chatwoot_response = requests.post(
            upload_url,
            headers=headers,
            data=payload,
            files=files,
            timeout=30
        )
        print(f"Status Chatwoot: {chatwoot_response.status_code}", flush=True)
        print(f"Respuesta Chatwoot: {chatwoot_response.text}", flush=True)
        chatwoot_response.raise_for_status()

        return jsonify({
            "status": "success",
            "chatwoot_response": chatwoot_response.json()
        }), 200
    except requests.exceptions.RequestException as e:
        body = getattr(e.response, "text", str(e))
        print(f"Error al enviar PDF a Chatwoot: {body}", flush=True)
        return jsonify({"error": f"Error al enviar PDF a Chatwoot: {body}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
