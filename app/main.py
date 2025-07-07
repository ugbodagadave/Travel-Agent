import os
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
import stripe
from twilio.rest import Client as TwilioClient

from app.amadeus_service import AmadeusService
from app.database import init_db, SessionLocal, Conversation, redis_client
from app.telegram_service import send_message
from app.core_logic import process_message
from app.new_session_manager import load_session, save_session

load_dotenv()

app = Flask(__name__)

# Initialize the database
init_db()

# Initialize services
amadeus_service = AmadeusService()

# Initialize Twilio Client
twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token)

# WARNING: TEMPORARY ADMIN ENDPOINT. REMOVE AFTER USE.
@app.route("/admin/reset-db/<secret_key>")
def reset_database(secret_key):
    # Use a simple secret key from env to prevent accidental runs
    admin_secret = os.environ.get("ADMIN_SECRET_KEY", "default_secret")
    if secret_key != admin_secret:
        return "Unauthorized", 401
    
    db = SessionLocal()
    try:
        num_rows_deleted = db.query(Conversation).delete()
        db.commit()
        # Also flush the redis cache to be safe
        if redis_client:
            redis_client.flushall()
        return f"Database reset successfully. Deleted {num_rows_deleted} conversation(s)."
    except Exception as e:
        db.rollback()
        return f"An error occurred: {e}", 500
    finally:
        db.close()

@app.route("/webhook", methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').lower()
    user_id = request.values.get('From', '')
    
    response_msg = process_message(user_id, incoming_msg, amadeus_service)
    
    resp = MessagingResponse()
    resp.message(response_msg)
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
        
        response_msg = process_message(user_id, text, amadeus_service)
        
        send_message(chat_id, response_msg)

    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True) 