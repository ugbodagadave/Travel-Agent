import os
from flask import Flask, request, send_from_directory, url_for
from twilio.twiml.messaging_response import MessagingResponse
import stripe
from twilio.rest import Client as TwilioClient
import uuid

from app.amadeus_service import AmadeusService
from app.telegram_service import send_message, send_pdf as send_telegram_pdf
from app.core_logic import process_message
from app.new_session_manager import load_session, save_session, load_user_id_from_wallet
from app.pdf_service import create_flight_itinerary
from app.utils import sanitize_filename

app = Flask(__name__)

# Initialize services
amadeus_service = AmadeusService()

# Initialize Twilio Client
twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token)

def send_whatsapp_pdf(to_number, pdf_bytes, filename="itinerary.pdf"):
    """
    Saves a PDF, gets its public URL, and sends it to a WhatsApp user via Twilio.
    """
    temp_dir = 'temp_files'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(temp_dir, unique_filename)
    
    with open(file_path, 'wb') as f:
        f.write(pdf_bytes)
    
    # Generate the public URL for the file
    with app.app_context():
        # We need to manually set the SERVER_NAME for url_for to work in a script
        app.config['SERVER_NAME'] = os.getenv('SERVER_NAME', 'localhost:5000')
        media_url = url_for('serve_file', filename=unique_filename, _external=True)

    try:
        twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=f"Here is your flight itinerary: {filename}",
            media_url=[media_url],
            to=to_number
        )
        print(f"PDF sent to WhatsApp user {to_number}")
    except Exception as e:
        print(f"Error sending PDF to WhatsApp: {e}")

@app.route("/health")
def health():
    return {'status': 'healthy'}, 200

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
            # Load the session to get the flight offer that was paid for
            state, conversation_history, flight_offers, flight_details = load_session(user_id)
            
            if flight_offers:
                selected_flight = flight_offers[0]
                traveler_names = flight_details.get("traveler_names", [])

                # If no specific names were collected, fall back to the single name in the offer
                if not traveler_names:
                    traveler_names = [selected_flight.get('traveler_name', 'traveler')]
                
                pdf_filenames = []
                for name in traveler_names:
                    # Get the traveler's name and create a sanitized filename
                    pdf_filename = f"flight_ticket_{sanitize_filename(name)}.pdf"
                    pdf_filenames.append(pdf_filename)

                    # 1. Create the PDF with the specific traveler's name
                    pdf_bytes = create_flight_itinerary(selected_flight, traveler_name=name)
                    
                    # 2. Send the PDF based on the platform
                    try:
                        if user_id.startswith('whatsapp:'):
                            send_whatsapp_pdf(user_id, pdf_bytes, pdf_filename)
                        elif user_id.startswith('telegram:'):
                            chat_id = user_id.split(':')[1]
                            send_telegram_pdf(chat_id, pdf_bytes, pdf_filename)
                    except Exception as e:
                        print(f"Error sending PDF for {name} to {user_id}: {e}")

                # 3. Send a final confirmation message
                try:
                    num_tickets = len(pdf_filenames)
                    if num_tickets > 1:
                        confirmation_text = f"Thank you for booking with Flai 😊. I've sent {num_tickets} separate tickets for each passenger."
                    else:
                        confirmation_text = f"Thank you for booking with Flai 😊. Your flight ticket ({pdf_filenames[0]}) has been sent."
                    
                    if user_id.startswith('telegram:'):
                        chat_id = user_id.split(':')[1]
                        send_message(chat_id, confirmation_text)
                    # Note: Sending a final summary message for WhatsApp is also a good idea.
                    # This can be added here if needed.

                except Exception as e:
                    print(f"Error in post-payment flow for {user_id}: {e}")
                
                # 4. Update the state
                state = "BOOKING_CONFIRMED"
                save_session(user_id, state, conversation_history, flight_offers, flight_details)
            else:
                print(f"Error: No flight offer found in session for {user_id} after payment.")

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
            # We return 400 here because this is a malformed but relevant notification.
            return 'Missing paymentIntentId', 400

        # Retrieve user_id from our Redis mapping
        user_id = load_user_id_from_wallet(payment_intent_id)
        if not user_id:
            print(f"ERROR: Could not find user_id for paymentIntentId: {payment_intent_id}")
            # 404 is appropriate as the user mapping was not found.
            return 'User not found for payment', 404

        # Load the user's full session
        state, conversation_history, flight_offers, flight_details = load_session(user_id)
        if not flight_offers:
            print(f"Error: No flight offer found in session for {user_id} after USDC payment.")
            return 'Flight offer not found', 404

        # The rest of the logic to generate and send the PDF
        selected_flight = flight_offers[0]
        traveler_names = flight_details.get("traveler_names", [])
        if not traveler_names:
            traveler_names = [selected_flight.get('traveler_name', 'traveler')]

        pdf_filenames = []
        for name in traveler_names:
            pdf_filename = f"flight_ticket_{sanitize_filename(name)}.pdf"
            pdf_filenames.append(pdf_filename)
            pdf_bytes = create_flight_itinerary(selected_flight, traveler_name=name)
            
            try:
                if user_id.startswith('whatsapp:'):
                    send_whatsapp_pdf(user_id, pdf_bytes, pdf_filename)
                elif user_id.startswith('telegram:'):
                    chat_id = user_id.split(':')[1]
                    send_telegram_pdf(chat_id, pdf_bytes, pdf_filename)
            except Exception as e:
                print(f"Error sending PDF for {name} to {user_id}: {e}")

        # Final confirmation message
        try:
            num_tickets = len(traveler_names)
            if num_tickets > 1:
                confirmation_text = f"Thank you for booking with Flai 😊. I've sent {num_tickets} separate tickets for each passenger."
            else:
                confirmation_text = f"Thank you for booking with Flai 😊. Your flight ticket ({pdf_filenames[0]}) has been sent."
            
            if user_id.startswith('telegram:'):
                chat_id = user_id.split(':')[1]
                send_message(chat_id, confirmation_text)

        except Exception as e:
            print(f"Error in post-payment flow for {user_id}: {e}")

        # Update state and save session
        state = "BOOKING_CONFIRMED"
        save_session(user_id, state, conversation_history, flight_offers, flight_details)
        
        print(f"Successfully processed payment and sent ticket for {user_id}.")
        return 'OK', 200
    
    else:
        # For any other notification type, just acknowledge it.
        unhandled_type = payment_data.get('status') if payment_data else 'N/A'
        print(f"Received unhandled notification type: '{notification_type}' with status: '{unhandled_type}'. Responding with OK.")
        return 'OK', 200


@app.route("/files/<filename>")
def serve_file(filename):
    """Serves a file from the temp_files directory."""
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