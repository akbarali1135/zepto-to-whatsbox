# api/webhook.py

from http.server import BaseHTTPRequestHandler
import json
import requests
import os

WC_STORE_URL = os.environ.get("WC_STORE_URL")
WC_CONSUMER_KEY = os.environ.get("WC_CONSUMER_KEY")
WC_CONSUMER_SECRET = os.environ.get("WC_CONSUMER_SECRET")
WHATSAPP_API_URL = os.environ.get("WHATSAPP_API_URL")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len)
        data = json.loads(body)

        subject = data.get("subject", "")
        body_text = data.get("body", "")
        email = data.get("to", "")

        phone, name = fetch_phone_from_woocommerce(email)
        if not phone:
            self.respond({"error": "No phone found for this email"}, 404)
            return

        success = ensure_whatsapp_contact_and_send(phone, name, email)

        self.respond({
            "email": email,
            "phone": phone,
            "message_status": "sent" if success else "failed"
        })

    def respond(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def fetch_phone_from_woocommerce(email):
    url = f"{WC_STORE_URL}/wp-json/wc/v3/orders"
    params = {
        "per_page": 50,
        "consumer_key": WC_CONSUMER_KEY,
        "consumer_secret": WC_CONSUMER_SECRET
    }

    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        orders = res.json()

        for order in orders:
            billing = order.get("billing", {})
            if billing.get("email", "").lower() == email.lower():
                phone = billing.get("phone")
                name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
                return phone, name
    except Exception as e:
        print("WooCommerce error:", e)

    return None, None

def ensure_whatsapp_contact_and_send(phone, name, email):
    if not whatsapp_contact_exists(phone):
        res = add_whatsapp_contact(phone, name, email)
        if res.get("httpCode") != 200:
            return False

    res = send_whatsapp_hello(phone)
    return res.get("httpCode") == 200

def whatsapp_contact_exists(phone):
    url = f"{WHATSAPP_API_URL}/api/wpbox/getSingleContact?token={WHATSAPP_TOKEN}&phone={phone}"
    try:
        res = requests.get(url, timeout=5)
        return res.status_code == 200 and res.json().get("status") == "success"
    except:
        return False

def add_whatsapp_contact(phone, name, email):
    url = f"{WHATSAPP_API_URL}/api/wpbox/makeContact"
    payload = {
        "token": WHATSAPP_TOKEN,
        "phone": phone,
        "name": name,
        "groups": "Sample Group For Testing",
        "custom": {
            "email": email,
            "location": "India"
        }
    }

    res = requests.post(url, json=payload)
    return {
        "httpCode": res.status_code,
        "response": res.text
    }

def send_whatsapp_hello(phone):
    url = f"{WHATSAPP_API_URL}/api/wpbox/sendtemplatemessage"
    payload = {
        "token": WHATSAPP_TOKEN,
        "phone": phone,
        "group": "Sample Group For Testing",
        "template_name": "hello_world",
        "template_language": "en_US"
    }

    res = requests.post(url, json=payload)
    return {
        "httpCode": res.status_code,
        "response": res.text
    }
