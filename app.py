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

    # La macro de Chatwoot manda el id de la conversación al nivel superior
    conversation_id = data.get("id")

    # El account_id sí aparece en messages[0].account_id en tus logs
    messages = data.get("messages") or []
    first_message = messages[0] if messages else {}
    account_id = first_message.get("account_id")

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
        "attachments[]": ("catalogo-2026-deportes-cdmx.pdf", pdf_content, "application/pdf")
    }
    payload = {
        "message_type": "outgoing",
        "content": ""
    }

    try:
        response = requests.post(
            upload_url,
            headers=headers,
            data=payload,
            files=files,
            timeout=30
        )
        print(f"Status Chatwoot: {response.status_code}", flush=True)
        print(f"Respuesta Chatwoot: {response.text}", flush=True)
        response.raise_for_status()

        return jsonify({"status": "success"}), 200
    except requests.exceptions.RequestException as e:
        body = getattr(e.response, "text", str(e))
        print(f"Error al enviar PDF a Chatwoot: {body}", flush=True)
        return jsonify({"error": f"Error al enviar PDF a Chatwoot: {body}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
