
import os
from twilio.rest import Client as TwilioClient
from app.celery_worker import celery_app
from app.amadeus_service import AmadeusService
from app.new_session_manager import load_session, save_session
from app.utils import _format_flight_offers
from app.telegram_service import send_message

# Initialize Twilio Client for the task
twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token)

@celery_app.task
def search_flights_task(user_id, flight_details):
    """
    Celery task to search for flights asynchronously, send a proactive message,
    and update the session state.
    """
    amadeus_service = AmadeusService()
    
    # Load session to get conversation history
    _, conversation_history, _ = load_session(user_id)
    
    origin_iata = amadeus_service.get_iata_code(flight_details.get('origin'))
    destination_iata = amadeus_service.get_iata_code(flight_details.get('destination'))
    
    offers = []
    if origin_iata and destination_iata:
        offers = amadeus_service.search_flights(
            originLocationCode=origin_iata,
            destinationLocationCode=destination_iata,
            departureDate=flight_details.get('departure_date'),
            adults=str(flight_details.get('number_of_travelers', '1'))
        )
    
    if offers:
        response_msg = _format_flight_offers(offers)
        next_state = "FLIGHT_SELECTION"
    else:
        response_msg = "Sorry, I couldn't find any flights for the given criteria. Would you like to try a different destination or date?"
        next_state = "GATHERING_INFO"

    # Proactively send the message back to the user
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
        print(f"Error sending proactive message from task: {e}")

    # Update the user's session with the new state and offers
    save_session(user_id, next_state, conversation_history, offers) 