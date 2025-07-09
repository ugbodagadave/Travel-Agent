
import os
from twilio.rest import Client as TwilioClient
from app.celery_worker import celery_app
from app.amadeus_service import AmadeusService
from app.new_session_manager import load_session, save_session
from app.utils import _format_flight_offers
from app.telegram_service import send_message
from tenacity import retry, stop_after_delay, wait_fixed, RetryError

# Initialize Twilio Client for the task
twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token)

@retry(stop=stop_after_delay(15), wait=wait_fixed(2))
def _search_flights_with_retry(amadeus_service, **kwargs):
    """Wrapper to search flights with retry logic."""
    return amadeus_service.search_flights(**kwargs)

@celery_app.task
def search_flights_task(user_id, flight_details):
    """
    Celery task to search for flights asynchronously, send a proactive message,
    and update the session state.
    """
    print(f"[{user_id}] - INFO: Starting search_flights_task.")
    
    # --- Check for essential environment variables ---
    missing_vars = [var for var in ["REDIS_URL", "AMADEUS_CLIENT_ID", "AMADEUS_CLIENT_SECRET", "TELEGRAM_BOT_TOKEN", "TWILIO_ACCOUNT_SID"] if not os.getenv(var)]
    if missing_vars:
        print(f"[{user_id}] - CRITICAL: The following environment variables are missing in the Celery worker: {', '.join(missing_vars)}")
        # Even if we can't send a message, we must log this critical configuration error.
        # We won't proceed because nearly everything will fail.
        return

    print(f"[{user_id}] - INFO: All environment variables seem to be present.")

    _, conversation_history, _ = load_session(user_id)
    print(f"[{user_id}] - INFO: Session loaded successfully.")

    try:
        amadeus_service = AmadeusService()
        print(f"[{user_id}] - INFO: AmadeusService initialized.")
        
        origin_iata = amadeus_service.get_iata_code(flight_details.get('origin'))
        print(f"[{user_id}] - INFO: Got origin IATA '{origin_iata}' for '{flight_details.get('origin')}'.")

        destination_iata = amadeus_service.get_iata_code(flight_details.get('destination'))
        print(f"[{user_id}] - INFO: Got destination IATA '{destination_iata}' for '{flight_details.get('destination')}'.")
        
        offers = []
        if origin_iata and destination_iata:
            print(f"[{user_id}] - INFO: Searching flights with Amadeus...")
            try:
                offers = _search_flights_with_retry(
                    amadeus_service,
                    originLocationCode=origin_iata,
                    destinationLocationCode=destination_iata,
                    departureDate=flight_details.get('departure_date'),
                    adults=str(flight_details.get('number_of_travelers', '1'))
                )
                print(f"[{user_id}] - INFO: Amadeus search returned {len(offers) if offers else 0} offers.")
            except RetryError:
                print(f"[{user_id}] - WARNING: Amadeus API timeout/retry error.")
                offers = []
        else:
            print(f"[{user_id}] - WARNING: Missing IATA code. Skipping flight search.")

        
        if offers:
            response_msg = _format_flight_offers(offers)
            next_state = "FLIGHT_SELECTION"
            print(f"[{user_id}] - INFO: Formatted flight offers successfully.")
        else:
            response_msg = "Sorry, I couldn't find any flights for the given criteria. Would you like to try a different destination or date?"
            next_state = "GATHERING_INFO"
            print(f"[{user_id}] - INFO: No flights found. Preparing 'no flights' message.")

    except Exception as e:
        print(f"[{user_id}] - CRITICAL: An unexpected exception occurred during the flight search logic: {e}")
        response_msg = "I'm sorry, but I encountered an unexpected error while searching for flights. Please try again in a moment."
        next_state = "GATHERING_INFO"
        offers = []

    # Proactively send the message back to the user
    try:
        print(f"[{user_id}] - INFO: Attempting to send message to user.")
        if user_id.startswith('whatsapp:'):
            twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                body=response_msg,
                to=user_id
            )
        elif user_id.startswith('telegram:'):
            chat_id = user_id.split(':')[1]
            send_message(chat_id, response_msg)
        print(f"[{user_id}] - INFO: Message sent successfully.")
    except Exception as e:
        print(f"[{user_id}] - CRITICAL: Failed to send proactive message from task: {e}")

    # Update the user's session with the new state and offers
    save_session(user_id, next_state, conversation_history, offers)
    print(f"[{user_id}] - INFO: Session saved with new state '{next_state}'. Task finished.") 