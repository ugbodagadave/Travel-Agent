import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import stripe

app = Flask(__name__)

# Lazy-loaded service instances
_amadeus_service = None
_twilio_client = None
_twilio_whatsapp_number = None

def get_amadeus_service():
    global _amadeus_service
    if _amadeus_service is None:
        from app.amadeus_service import AmadeusService
        _amadeus_service = AmadeusService()
    return _amadeus_service

def get_twilio_client():
    global _twilio_client, _twilio_whatsapp_number
    if _twilio_client is None:
        from twilio.rest import Client as TwilioClient
        twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        _twilio_whatsapp_number = os.environ.get("TWILIO_WHATSAPP_NUMBER")
        _twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token)
    return _twilio_client, _twilio_whatsapp_number

@app.route("/webhook", methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').lower()
    user_id = request.values.get('From', '')
    
    response_messages = process_message(user_id, incoming_msg, get_amadeus_service())

    resp = MessagingResponse()
    for msg in response_messages:
        resp.message(msg)
    return str(resp)

@app.route("/stripe-webhook", methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        return 'Invalid request', 400

    if event['type'] == 'checkout.session.completed':
        session_data = event['data']['object']
        user_id = session_data.get('client_reference_id')
        
        if user_id:
            state, conversation_history, flight_offers = load_session(user_id)
            state = "GATHERING_BOOKING_DETAILS"
            save_session(user_id, state, conversation_history, flight_offers)
            
            response_msg = "Your payment was successful! To finalize the booking, please provide your full name and date of birth (e.g., John Doe YYYY-MM-DD)."
            
            try:
                if user_id.startswith('whatsapp:'):
                    twilio_client, whatsapp_number = get_twilio_client()
                    twilio_client.messages.create(
                        from_=whatsapp_number,
                        body=response_msg,
                        to=user_id
                    )
                elif user_id.startswith('telegram:'):
                    chat_id = user_id.split(':')[1]
                    from app.telegram_service import send_message
                    send_message(chat_id, response_msg)
            except Exception as e:
                print(f"Error sending proactive message: {e}")

    return 'OK', 200

@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"].lower()
        user_id = f"telegram:{chat_id}"
        
        from app.core_logic import process_message
        response_messages = process_message(user_id, text, get_amadeus_service())
        
        from app.telegram_service import send_message
        for msg in response_messages:
            send_message(chat_id, msg)

    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True)