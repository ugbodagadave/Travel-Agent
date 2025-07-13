import threading
from app.new_session_manager import load_session, save_session
from app.ai_service import get_ai_response, extract_flight_details_from_history, extract_traveler_details
from app.amadeus_service import AmadeusService
from app.payment_service import create_checkout_session
from app.tasks import search_flights_task
from app.utils import _format_flight_offers

# This is a simplified formatting function.
# In a real app, this would be more robust.
def _format_flight_offers(flights):
    """Formats flight offers into a string."""
    if not flights:
        return "Sorry, I couldn't find any flights for the given criteria."

    response_lines = ["I found a few options for you:"]
    for i, flight in enumerate(flights[:5], 1):
        itinerary = flight['itineraries'][0]
        price = flight['price']['total']
        response_lines.append(f"{i}. Flight to {itinerary['segments'][0]['arrival']['iataCode']} for {price} {flight['price']['currency']}.")

    response_lines.append("\nReply with the number of the flight you'd like to book, or say 'no' to start over.")
    return "\n".join(response_lines)


def process_message(user_id, incoming_msg, amadeus_service: AmadeusService):
    """
    Processes an incoming message from any platform.
    Returns a list of response messages to be sent back to the user.
    """
    state, conversation_history, flight_offers = load_session(user_id)
    response_messages = []

    # NOTE: This is a simplified version of the logic from app/main.py's webhook.
    # It does not yet include payment or final booking logic.
    if state == "GATHERING_INFO":
        ai_response, updated_history = get_ai_response(incoming_msg, conversation_history, state)
        
        if "[INFO_COMPLETE]" in ai_response:
            response_messages.append(ai_response.replace("[INFO_COMPLETE]", "").strip() + "\n\nIs this information correct?")
            state = "AWAITING_CONFIRMATION"
        else:
            response_messages.append(ai_response)
        
        save_session(user_id, state, updated_history, flight_offers)

    elif state == "AWAITING_CONFIRMATION":
        ai_response, updated_history = get_ai_response(incoming_msg, conversation_history, state)

        if "[CONFIRMED]" in ai_response:
            flight_details = extract_flight_details_from_history(updated_history)
            
            if flight_details:
                # Immediately respond to the user
                response_messages.append("Okay, I'm searching for the best flights for you. This might take a moment...")
                
                # Trigger the background task in a separate thread
                task_thread = threading.Thread(target=search_flights_task, args=(user_id, flight_details))
                task_thread.start()
                
                # Update state to prevent other inputs during search
                state = "SEARCH_IN_PROGRESS"
                save_session(user_id, state, updated_history, [])
            else:
                # This should rarely happen, but it's a safe fallback.
                response_messages.append("I seem to have lost the details. Let's start over.")
                state = "GATHERING_INFO"
                save_session(user_id, state, [], [])
        
        elif "[INFO_COMPLETE]" in ai_response:
            # This means the user made a correction and the AI has re-confirmed.
            response_messages.append(ai_response.replace("[INFO_COMPLETE]", "").strip() + "\n\nIs this information correct?")
            state = "AWAITING_CONFIRMATION" # Stay in this state
            save_session(user_id, state, updated_history, [])

        else:
            # Fallback for unexpected AI responses
            response_messages.append(ai_response)
            save_session(user_id, state, updated_history, flight_offers)

    elif state == "SEARCH_IN_PROGRESS":
        response_messages.append("I'm still looking for flights for you. I'll send them over as soon as they're ready.")
        save_session(user_id, state, conversation_history, flight_offers)

    elif state == "FLIGHT_SELECTION":
        if "no" in incoming_msg.lower():
            response_messages.append("Okay, let's start over. Where would you like to go?")
            state = "GATHERING_INFO"
            save_session(user_id, state, [], [])
        else:
            try:
                selection = int(incoming_msg.strip())
                if 1 <= selection <= len(flight_offers):
                    selected_flight = flight_offers[selection - 1]
                    response_messages.append("Great choice! To proceed with the booking, please provide the full name of the traveler as it appears on their passport.")
                    state = "AWAITING_TRAVELER_DETAILS"
                    save_session(user_id, state, conversation_history, [selected_flight])
                else:
                    response_messages.append("Invalid selection. Please choose a number from the list.")
                    save_session(user_id, state, conversation_history, flight_offers)
            except (ValueError, IndexError):
                response_messages.append("I didn't understand. Please reply with the flight number.")
                save_session(user_id, state, conversation_history, flight_offers)

    elif state == "AWAITING_TRAVELER_DETAILS":
        traveler_details = extract_traveler_details(incoming_msg)
        if traveler_details and traveler_details.get("fullName"):
            # The selected flight is the first (and only) in the list
            selected_flight = flight_offers[0]
            selected_flight['traveler_name'] = traveler_details["fullName"] # Save the name

            checkout_url = create_checkout_session(selected_flight, user_id)
            if checkout_url:
                response_messages.append(f"Thank you, {traveler_details['fullName']}. Please complete your payment using this secure link: {checkout_url}")
                state = "AWAITING_PAYMENT"
                save_session(user_id, state, conversation_history, [selected_flight])
            else:
                response_messages.append("I'm sorry, I couldn't create a payment link. Please try again.")
                save_session(user_id, state, conversation_history, flight_offers) # Keep old offers
        else:
            response_messages.append("I'm sorry, I couldn't understand the name. Please provide the traveler's full name.")
            save_session(user_id, state, conversation_history, flight_offers)

    else:
        # Default fallback for unhandled states
        response_messages.append("I'm not sure how to handle that right now. Let's start over. Where would you like to go?")
        state = "GATHERING_INFO"
        save_session(user_id, state, [], [])

    return response_messages 