import os
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
import stripe
from twilio.rest import Client as TwilioClient

from app.amadeus_service import AmadeusService
from app.telegram_service import send_message
from app.core_logic import process_message
from app.new_session_manager import load_session, save_session

load_dotenv()

app = Flask(__name__)

# Initialize services
amadeus_service = AmadeusService()

# Initialize Twilio Client
twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token)

@app.route("/webhook", methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').lower()
    user_id = request.values.get('From', '')
    
    response_messages = process_message(user_id, incoming_msg, amadeus_service)

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
                    twilio_client.messages.create(
                        from_=TWILIO_WHATSAPP_NUMBER,
                        body=response_msg,
                        to=user_id
                    )
                elif user_id.startswith('telegram:'):
                    chat_id = user_id.split(':')[1]
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
        
        response_messages = process_message(user_id, text, amadeus_service)
        
        for msg in response_messages:
            send_message(chat_id, msg)

    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True) 