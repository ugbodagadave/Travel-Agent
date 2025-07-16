
import os
from twilio.rest import Client as TwilioClient
from app.amadeus_service import AmadeusService
from app.new_session_manager import load_session, save_session
from app.utils import _format_flight_offers
from app.telegram_service import send_message
from tenacity import retry, stop_after_delay, wait_fixed, RetryError
import time

# Initialize Twilio Client for the task
twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token)

@retry(stop=stop_after_delay(15), wait=wait_fixed(2))
def _search_flights_with_retry(amadeus_service, **kwargs):
    """Wrapper to search flights with retry logic."""
    return amadeus_service.search_flights(**kwargs)

def search_flights_task(user_id, flight_details):
    """
    Function to search for flights asynchronously, send a proactive message,
    and update the session state. Now runs in a background thread.
    """
    
    # --- Check for essential environment variables ---
    missing_vars = [var for var in ["REDIS_URL", "AMADEUS_CLIENT_ID", "AMADEUS_CLIENT_SECRET", "TELEGRAM_BOT_TOKEN", "TWILIO_ACCOUNT_SID"] if not os.getenv(var)]
    if missing_vars:
        print(f"[{user_id}] - CRITICAL: The following environment variables are missing in the Celery worker: {', '.join(missing_vars)}")
        # Even if we can't send a message, we must log this critical configuration error.
        # We won't proceed because nearly everything will fail.
        return

    print(f"[{user_id}] - INFO: All environment variables seem to be present.")

    _, conversation_history, _, _ = load_session(user_id)
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
            
            search_params = {
                "originLocationCode": origin_iata,
                "destinationLocationCode": destination_iata,
                "departureDate": flight_details.get('departure_date'),
                "adults": str(flight_details.get('number_of_travelers', '1'))
            }
            if 'travel_class' in flight_details and flight_details['travel_class']:
                search_params['travelClass'] = flight_details['travel_class']

            try:
                offers = _search_flights_with_retry(
                    amadeus_service,
                    **search_params
                )
                print(f"[{user_id}] - INFO: Amadeus search returned {len(offers) if offers else 0} offers.")
            except RetryError:
                print(f"[{user_id}] - WARNING: Amadeus API timeout/retry error.")
                offers = []
        else:
            print(f"[{user_id}] - WARNING: Missing IATA code. Skipping flight search.")

        
        if offers:
            # Enrich offers with airline names and the traveler's name
            traveler_name = flight_details.get('traveler_name')
            for offer in offers:
                carrier_code = offer['itineraries'][0]['segments'][0]['carrierCode']
                airline_name = amadeus_service.get_airline_name(carrier_code)
                offer['airlineName'] = airline_name
                if traveler_name:
                    offer['traveler_name'] = traveler_name

            response_msg = _format_flight_offers(offers, amadeus_service)
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
            print(f"[{user_id}] - DEBUG: Sending proactive message from: '{TWILIO_WHATSAPP_NUMBER}' to: '{user_id}'")
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
    save_session(user_id, next_state, conversation_history, offers, flight_details)
    print(f"[{user_id}] - INFO: Session saved with new state '{next_state}'. Task finished.") 

# -----------------------------------------------
# USDC Payment Polling Task
# -----------------------------------------------

def poll_usdc_payment_task(user_id, intent_id, poll_interval=30, timeout_seconds=3600):
    """Polls Circle for payment status until complete or timeout.

    Args:
        user_id (str): The platform-specific user identifier (e.g., telegram:12345).
        intent_id (str): The Circle payment intent ID.
        poll_interval (int, optional): Seconds between polls. Defaults to 30.
        timeout_seconds (int, optional): Maximum time to poll. Defaults to 1 hour.
    """
    from app.circle_service import CircleService  # Imported here to avoid circular deps at load time
    circle_service = CircleService()

    start_time = time.time()
    print(f"[{user_id}] - INFO: Starting polling for payment intent {intent_id}.")

    while time.time() - start_time < timeout_seconds:
        status = circle_service.get_payment_intent_status(intent_id)
        print(f"[{user_id}] - DEBUG: Payment intent {intent_id} status: {status}")

        if status == "complete":
            print(f"[{user_id}] - INFO: Payment intent {intent_id} marked complete. Handling success.")
            try:
                from app.main import handle_successful_payment  # Local import to avoid circular deps
                handle_successful_payment(user_id)
            except Exception as e:
                print(f"[{user_id}] - ERROR in handle_successful_payment: {e}")
            return
        elif status is None:
            print(f"[{user_id}] - WARNING: Unable to retrieve status for {intent_id}. Will retry.")

        time.sleep(poll_interval)

    print(f"[{user_id}] - WARNING: Polling timed out for payment intent {intent_id} after {timeout_seconds} seconds.") 