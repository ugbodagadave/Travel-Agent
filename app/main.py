import os
from flask import Flask, request, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
import stripe
from twilio.rest import Client as TwilioClient
from app.amadeus_service import AmadeusService
from app.core_logic import process_message
from app.new_session_manager import load_session, save_session, get_redis_client
from app.telegram_service import send_message, send_telegram_pdf
from app.pdf_service import create_flight_itinerary
from app.utils import sanitize_filename
from app.storage_service import setup_cloudinary, upload_pdf

app = Flask(__name__)

# Initialize services at startup
amadeus_service = AmadeusService()
setup_cloudinary()

# Initialize Twilio Client
twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token)

def handle_successful_payment(user_id):
    """
    Centralized handler for successful payments.
    """
    state, conversation_history, flight_offers, flight_details = load_session(user_id)
    if not flight_offers:
        print(f"[{user_id}] - ERROR: No flight offer found in session after payment.")
        return
    selected_flight = flight_offers[0]
    traveler_names = flight_details.get("traveler_names", [])
    if not traveler_names:
        traveler_names = [selected_flight.get("traveler_name", "traveler")]
    pdf_filenames = []
    all_pdfs_sent_successfully = True
    for name in traveler_names:
        pdf_filename = f"flight_ticket_{sanitize_filename(name)}.pdf"
        pdf_filenames.append(pdf_filename)
        pdf_bytes = create_flight_itinerary(selected_flight, traveler_name=name)
        if user_id.startswith('whatsapp:'):
            download_url = upload_pdf(pdf_bytes, pdf_filename)
            if download_url:
                twilio_client.messages.create(
                    from_=TWILIO_WHATSAPP_NUMBER,
                    body=f"Kindly download your flight ticket with this link:\n{download_url}",
                    to=user_id
                )
            else:
                all_pdfs_sent_successfully = False
                twilio_client.messages.create(
                    from_=TWILIO_WHATSAPP_NUMBER,
                    body="I'm sorry, there was an error generating your ticket. Please contact support.",
                    to=user_id
                )
        elif user_id.startswith('telegram:'):
            chat_id = user_id.split(':')[1]
            send_telegram_pdf(chat_id, pdf_bytes, pdf_filename)
    if all_pdfs_sent_successfully:
        try:
            num_tickets = len(pdf_filenames)
            if num_tickets > 1:
                confirmation_text = f"Thank you for booking with Flai 😊. I've sent {num_tickets} separate tickets for each passenger."
            else:
                confirmation_text = f"Thank you for booking with Flai 😊. Your flight booking is confirmed."
            if user_id.startswith('telegram:'):
                chat_id = user_id.split(':')[1]
                send_message(chat_id, confirmation_text)
            elif user_id.startswith('whatsapp:'):
                twilio_client.messages.create(
                    from_=TWILIO_WHATSAPP_NUMBER,
                    body=confirmation_text,
                    to=user_id
                )
        except Exception as e:
            print(f"[{user_id}] - ERROR in post-payment confirmation: {e}")
    state = "BOOKING_CONFIRMED"
    save_session(user_id, state, conversation_history, flight_offers, flight_details)

@app.route("/admin/clear-redis/<secret_key>")
def clear_redis(secret_key):
    admin_key = os.environ.get("ADMIN_SECRET_KEY")
    if not admin_key:
        return "Admin secret key not configured.", 500
    if secret_key == admin_key:
        try:
            client = get_redis_client()
            if client:
                client.flushall()
                return "Redis database cleared successfully.", 200
            else:
                return "Redis client not available.", 500
        except Exception as e:
            return f"An error occurred while clearing Redis: {e}", 500
    else:
        return "Unauthorized.", 403

@app.route("/health")
def health():
    # Check Redis connection
    redis_status = "unknown"
    try:
        redis_client = get_redis_client()
        if redis_client:
            redis_client.ping()
            redis_status = "connected"
        else:
            redis_status = "not_available"
    except Exception as e:
        redis_status = f"error: {str(e)}"
    
    # Check environment variables
    env_status = {
        "REDIS_URL": "set" if os.environ.get("REDIS_URL") else "not_set",
        "IO_API_KEY": "set" if os.environ.get("IO_API_KEY") else "not_set",
        "TWILIO_ACCOUNT_SID": "set" if os.environ.get("TWILIO_ACCOUNT_SID") else "not_set",
        "TELEGRAM_BOT_TOKEN": "set" if os.environ.get("TELEGRAM_BOT_TOKEN") else "not_set",
        "AMADEUS_CLIENT_ID": "set" if os.environ.get("AMADEUS_CLIENT_ID") else "not_set",
        "CIRCLE_API_KEY": "set" if os.environ.get("CIRCLE_API_KEY") else "not_set",
        "STRIPE_SECRET_KEY": "set" if os.environ.get("STRIPE_SECRET_KEY") else "not_set"
    }
    
    return {
        'status': 'healthy',
        'redis': redis_status,
        'environment_variables': env_status,
        'timestamp': '2025-08-23T10:45:00Z'
    }, 200

@app.route("/payment-success")
def payment_success():
    return """
    <html>
        <head><title>Payment Successful</title></head>
        <body>
            <h1>Thank you for your payment!</h1>
            <p>Your flight itinerary is being processed and will be sent to you shortly.</p>
        </body>
    </html>
    """, 200

@app.route("/")
def root():
    return {'message': 'Travel Agent API is running'}, 200

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
            handle_successful_payment(user_id)
    return 'OK', 200

@app.route("/circle-webhook", methods=['POST'])
def circle_webhook():
    """
    Handles incoming webhooks from Circle.

    This function is designed to be robust and handle multiple scenarios:
    1.  **Subscription Confirmation**: Responds to Circle's initial verification.
    2.  **Pings**: Responds to test pings from the Circle dashboard.
    3.  **Payment Notifications**: Processes actual payment completion events.
    4.  **Other Notifications**: Acknowledges other notification types without processing them to ensure the webhook remains active.
    """
    # Use silent=True to prevent an exception if the payload is not valid JSON.
    data = request.get_json(silent=True)

    # Acknowledge empty requests, subscription confirmations, and pings immediately.
    if not data or \
       data.get("notificationType") == "SubscriptionConfirmation" or \
       data.get('notification', {}).get('type') == 'ping':
        print("Received a webhook verification, ping, or empty request. Responding with OK.")
        return 'OK', 200

    # From here, we expect a 'notification' object. If it's missing, we'll
    # acknowledge the request and log it, but not treat it as an error.
    notification = data.get('notification')
    if not notification:
        print(f"Received a webhook without a 'notification' object. Payload: {data}. Responding with OK.")
        return 'OK', 200

    # Process only completed payment notifications.
    notification_type = notification.get('type')
    payment_data = notification.get('payment')

    if notification_type == 'payments' and payment_data and payment_data.get('status') == 'complete':
        print(f"Processing completed payment notification: {payment_data.get('id')}")
        payment_intent_id = payment_data.get('paymentIntentId')
        if not payment_intent_id:
            print("ERROR: Payment notification is missing 'paymentIntentId'.")
            return 'Missing paymentIntentId', 400

        # Retrieve the user ID from the mapping
        user_id = load_user_id_from_wallet(payment_intent_id)
        if not user_id:
            print(f"ERROR: Could not find user_id for paymentIntentId: {payment_intent_id}")
            return 'User not found for payment', 404

        # Delegate to the unified payment handler
        handle_successful_payment(user_id)

        return 'OK', 200

    # For all other notifications, simply acknowledge.
    return 'OK', 200


@app.route("/files/<filename>")
def serve_file(filename):
    """Serves a file from the temp_files directory."""
    # This endpoint is no longer used for sending PDFs to WhatsApp,
    # but we'll keep it for now for other potential uses.
    return send_from_directory('../temp_files', filename)

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
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))