import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        data = await request.json()

        subject = data.get("subject", "")
        body = data.get("body", "")
        to_email = data.get("to", "")

        if not to_email:
            return {"error": "Missing recipient email in webhook"}

        # WooCommerce credentials
        store_url = os.environ.get("WC_STORE_URL")
        ck = os.environ.get("WC_CONSUMER_KEY")
        cs = os.environ.get("WC_CONSUMER_SECRET")

        # WhatsApp API credentials
        whatsapp_api = os.environ.get("WHATSAPP_API_URL")
        whatsapp_token = os.environ.get("WHATSAPP_TOKEN")

        # Step 1: Find phone number by email from WooCommerce
        orders_url = f"{store_url}/wp-json/wc/v3/orders"
        res = requests.get(
            orders_url,
            params={"per_page": 50, "consumer_key": ck, "consumer_secret": cs}
        )
        orders = res.json()

        for order in orders:
            billing = order.get("billing", {})
            if billing.get("email", "").lower() == to_email.lower():
                phone = billing.get("phone", "")
                name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()

                if not phone:
                    return {"error": "Phone not found in order"}

                # Step 2: Add contact if not exists
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
                            "subject": subject
                        }
                    }
                    requests.post(
                        f"{whatsapp_api}/api/wpbox/makeContact",
                        json=add_payload,
                        headers={"Content-Type": "application/json"}
                    )

                # Step 3: Send WhatsApp template message
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

        return {"error": "No matching order found for email"}

    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}
