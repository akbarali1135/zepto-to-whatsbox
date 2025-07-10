import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        data = await request.json()

        subject = (
            data.get("event_message", [{}])[0]
            .get("email_info", {})
            .get("subject", "ZeptoMail Event")
        )
        to_email = (
            data.get("event_message", [{}])[0]
            .get("event_data", [{}])[0]
            .get("details", [{}])[0]
            .get("bounced_recipient", "")
        )
        body = (
            data.get("event_message", [{}])[0]
            .get("event_data", [{}])[0]
            .get("details", [{}])[0]
            .get("diagnostic_message", "No diagnostic message provided")
        )

        if not to_email:
            return {"error": "Missing recipient email in webhook"}

        # Hardcoded phone and name
        phone = "8355086283"
        name = "Admin Receiver"

        # WhatsApp API credentials
        whatsapp_api = os.environ.get("WHATSAPP_API_URL")
        whatsapp_token = os.environ.get("WHATSAPP_TOKEN")

        # Step 1: Add contact if not exists
        exists_res = requests.get(
            f"{whatsapp_api}/api/wpbox/getSingleContact",
            params={"token": whatsapp_token, "phone": phone}
        )

        if exists_res.status_code != 200 or exists_res.json().get("status") != "success":
            add_payload = {
                "token": whatsapp_token,
                "phone": phone,
                "name": name,
                "groups": "Sample Group For Testing",
                "custom": {
                    "email": to_email,
                    "subject": subject,
                    "reason": body
                }
            }
            requests.post(
                f"{whatsapp_api}/api/wpbox/makeContact",
                json=add_payload,
                headers={"Content-Type": "application/json"}
            )

        # Step 2: Send WhatsApp template message
        send_payload = {
            "token": whatsapp_token,
            "phone": phone,
            "group": "Sample Group For Testing",
            "template_name": "hello_world",
            "template_language": "en_US"
        }
        send_res = requests.post(
            f"{whatsapp_api}/api/wpbox/sendtemplatemessage",
            json=send_payload,
            headers={"Content-Type": "application/json"}
        )

        return {
            "email": to_email,
            "phone": phone,
            "subject": subject,
            "whatsapp_status": "sent" if send_res.status_code == 200 else "failed"
        }

    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}
