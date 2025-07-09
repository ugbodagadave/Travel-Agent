from app.new_session_manager import load_session, save_session
from app.ai_service import get_ai_response, extract_flight_details_from_history
from app.amadeus_service import AmadeusService
from app.payment_service import create_checkout_session

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
        ai_response, updated_history = get_ai_response(incoming_msg, conversation_history)
        
        if "[INFO_COMPLETE]" in ai_response:
            response_messages.append(ai_response.replace("[INFO_COMPLETE]", "").strip() + "\n\nIs this information correct?")
            state = "AWAITING_CONFIRMATION"
        else:
            response_messages.append(ai_response)
        
        save_session(user_id, state, updated_history, flight_offers)

    elif state == "AWAITING_CONFIRMATION":
        if "yes" in incoming_msg or "correct" in incoming_msg:
            response_messages.append("Okay, let me get the best flight options for you.")
            flight_details = extract_flight_details_from_history(conversation_history)
            
            if flight_details:
                origin_iata = amadeus_service.get_iata_code(flight_details.get('origin'))
                destination_iata = amadeus_service.get_iata_code(flight_details.get('destination'))
                
                if origin_iata and destination_iata:
                    offers = amadeus_service.search_flights(
                        originLocationCode=origin_iata,
                        destinationLocationCode=destination_iata,
                        departureDate=flight_details.get('departure_date'),
                        adults=str(flight_details.get('number_of_travelers', '1'))
                    )
                    
                    if offers:
                        response_messages.append(_format_flight_offers(offers))
                        state = "FLIGHT_SELECTION"
                        save_session(user_id, state, conversation_history, offers)
                    else:
                        response_messages.append("Sorry, I couldn't find any flights for the given criteria. Please try a different search.")
                        state = "GATHERING_INFO"
                        save_session(user_id, state, conversation_history, [])
                else:
                    response_messages.append("I'm sorry, I couldn't find the airport codes.")
                    state = "GATHERING_INFO"
                    save_session(user_id, state, conversation_history, [])
            else:
                response_messages.append("I had trouble understanding the details. Let's try again.")
                state = "GATHERING_INFO"
                save_session(user_id, state, conversation_history, [])
        else:
            ai_response, updated_history = get_ai_response(incoming_msg, conversation_history)
            response_messages.append(ai_response)
            state = "GATHERING_INFO"
            save_session(user_id, state, updated_history, [])

    elif state == "FLIGHT_SELECTION":
        if "no" in incoming_msg:
            response_messages.append("Okay, let's start over. Where would you like to go?")
            state = "GATHERING_INFO"
            save_session(user_id, state, [], [])
        else:
            try:
                selection = int(incoming_msg.strip())
                if 1 <= selection <= len(flight_offers):
                    selected_flight = flight_offers[selection - 1]
                    checkout_url = create_checkout_session(selected_flight, user_id)
                    
                    if checkout_url:
                        response_messages.append(f"Great! Please complete your payment using this secure link: {checkout_url}")
                        state = "AWAITING_PAYMENT"
                        # Save the selected flight in the session for the webhook
                        save_session(user_id, state, conversation_history, [selected_flight])
                    else:
                        response_messages.append("I'm sorry, I couldn't create a payment link. Please try again.")
                        save_session(user_id, state, conversation_history, flight_offers)
                else:
                    response_messages.append("Invalid selection. Please choose a number from the list.")
                    save_session(user_id, state, conversation_history, flight_offers)
            except (ValueError, IndexError):
                response_messages.append("I didn't understand. Please reply with the flight number.")
                save_session(user_id, state, conversation_history, flight_offers)

    else:
        # Default fallback for unhandled states
        response_messages.append("I'm not sure how to handle that right now. Let's start over. Where would you like to go?")
        state = "GATHERING_INFO"
        save_session(user_id, state, [], [])

    return response_messages 