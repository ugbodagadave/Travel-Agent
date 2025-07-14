import threading
from app.new_session_manager import load_session, save_session
from app.ai_service import get_ai_response, extract_flight_details_from_history, extract_traveler_details, extract_traveler_names
from app.amadeus_service import AmadeusService
from app.payment_service import create_checkout_session
from app.tasks import search_flights_task
from app.circle_service import CircleService
from app.currency_service import CurrencyService
from app.new_session_manager import save_wallet_mapping

# Initialize services
circle_service = CircleService()
currency_service = CurrencyService()
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
    state, conversation_history, flight_offers, flight_details = load_session(user_id)
    response_messages = []

    # NOTE: This is a simplified version of the logic from app/main.py's webhook.
    # It does not yet include payment or final booking logic.
    if state == "GATHERING_INFO":
        ai_response, updated_history = get_ai_response(incoming_msg, conversation_history, state)
        
        if "[INFO_COMPLETE]" in ai_response:
            flight_details = extract_flight_details_from_history(updated_history)
            
            # Try to get the number of travelers, default to 1 if not found or invalid
            try:
                num_travelers = int(flight_details.get("number_of_travelers", 1))
            except (ValueError, TypeError):
                num_travelers = 1

            if num_travelers > 1:
                state = "GATHERING_NAMES"
                response_messages.append(f"It looks like there are {num_travelers} travelers. Please provide their full names, separated by commas.")
                save_session(user_id, state, updated_history, flight_offers, flight_details)
            else:
                response_messages.append(ai_response.replace("[INFO_COMPLETE]", "").strip() + "\n\nIs this information correct?")
                state = "AWAITING_CONFIRMATION"
                save_session(user_id, state, updated_history, flight_offers, flight_details)
        else:
            response_messages.append(ai_response)
            save_session(user_id, state, updated_history, flight_offers, flight_details)

    elif state == "GATHERING_NAMES":
        num_travelers = int(flight_details.get("number_of_travelers", 1))
        names = extract_traveler_names(incoming_msg, num_travelers)

        if names:
            flight_details["traveler_names"] = names
            state = "AWAITING_CONFIRMATION"
            
            # Create a confirmation message listing all details
            confirmation_text = "Great, I have all the names. Please confirm the details one last time:\n"
            # This is a simplified summary. A real app might format this more nicely.
            for key, value in flight_details.items():
                if key != "traveler_names":
                    confirmation_text += f"- {key.replace('_', ' ').title()}: {value}\n"
            
            confirmation_text += f"- Travelers: {', '.join(names)}"
            confirmation_text += "\n\nIs this all correct?"
            response_messages.append(confirmation_text)
            
            # Save the updated details and new state
            conversation_history.append({"role": "user", "content": incoming_msg})
            conversation_history.append({"role": "assistant", "content": confirmation_text})
            save_session(user_id, state, conversation_history, flight_offers, flight_details)
        else:
            response_messages.append(f"I'm sorry, I couldn't understand the names. Please provide exactly {num_travelers} full names, separated by commas.")
            save_session(user_id, state, conversation_history, flight_offers, flight_details)

    elif state == "AWAITING_CONFIRMATION":
        ai_response, updated_history = get_ai_response(incoming_msg, conversation_history, state)

        if "[CONFIRMED]" in ai_response:
            # Re-load details from session in case this is the second confirmation
            _, _, _, flight_details = load_session(user_id)
            
            if flight_details:
                # Immediately respond to the user
                response_messages.append("Okay, I'm searching for the best flights for you. This might take a moment...")
                
                # Trigger the background task in a separate thread
                task_thread = threading.Thread(target=search_flights_task, args=(user_id, flight_details))
                task_thread.start()
                
                # Update state to prevent other inputs during search
                state = "SEARCH_IN_PROGRESS"
                save_session(user_id, state, updated_history, [], flight_details)
            else:
                # This should rarely happen, but it's a safe fallback.
                response_messages.append("I seem to have lost the details. Let's start over.")
                state = "GATHERING_INFO"
                save_session(user_id, state, [], [], {})
        
        elif "[INFO_COMPLETE]" in ai_response:
            # This means the user made a correction and the AI has re-confirmed.
            response_messages.append(ai_response.replace("[INFO_COMPLETE]", "").strip() + "\n\nIs this information correct?")
            state = "AWAITING_CONFIRMATION" # Stay in this state
            save_session(user_id, state, updated_history, [], flight_details)

        else:
            # Fallback for unexpected AI responses
            response_messages.append(ai_response)
            save_session(user_id, state, updated_history, flight_offers, flight_details)

    elif state == "SEARCH_IN_PROGRESS":
        response_messages.append("I'm still looking for flights for you. I'll send them over as soon as they're ready.")
        save_session(user_id, state, conversation_history, flight_offers, flight_details)

    elif state == "FLIGHT_SELECTION":
        if "no" in incoming_msg.lower():
            response_messages.append("Okay, let's start over. Where would you like to go?")
            state = "GATHERING_INFO"
            save_session(user_id, state, [], [], {})
        else:
            try:
                selection = int(incoming_msg.strip())
                if 1 <= selection <= len(flight_offers):
                    selected_flight = flight_offers[0] # The user selected the first flight
                    
                    state = "AWAITING_PAYMENT_SELECTION"
                    response_messages.append("You've selected a great flight. How would you like to pay? (Reply with 'Card' or 'USDC')")
                    
                    # Save the selected flight in the session for the next step
                    save_session(user_id, state, conversation_history, [selected_flight], flight_details)
                else:
                    response_messages.append("Invalid selection. Please choose a number from the list.")
                    save_session(user_id, state, conversation_history, flight_offers, flight_details)
            except (ValueError, IndexError):
                response_messages.append("I didn't understand. Please reply with the flight number.")
                save_session(user_id, state, conversation_history, flight_offers, flight_details)

    elif state == "AWAITING_PAYMENT_SELECTION":
        # Ensure there is a selected flight in the session
        if not flight_offers:
            response_messages.append("Something went wrong, I don't have a flight selected. Let's start over.")
            state = "GATHERING_INFO"
            save_session(user_id, state, [], [], {})
            return response_messages

        selected_flight = flight_offers[0]

        if "card" in incoming_msg.lower():
            checkout_url = create_checkout_session(selected_flight, user_id)
            if checkout_url:
                response_messages.append(f"Great! Please complete your payment using this secure link: {checkout_url}")
                state = "AWAITING_PAYMENT"
                save_session(user_id, state, conversation_history, [selected_flight], flight_details)
            else:
                response_messages.append("I'm sorry, I couldn't create a payment link. Please try again.")
                save_session(user_id, state, conversation_history, flight_offers, flight_details)
        
        elif "usdc" in incoming_msg.lower():
            price_str = selected_flight.get('price', {}).get('total')
            currency = selected_flight.get('price', {}).get('currency', 'USD')
            
            try:
                usd_amount = currency_service.convert_to_usd(float(price_str), currency)
                if usd_amount:
                    wallet_info = circle_service.create_payment_wallet()
                    if wallet_info:
                        wallet_id = wallet_info.get('walletId')
                        wallet_address = wallet_info.get('address')
                        
                        # Save the wallet_id -> user_id mapping
                        save_wallet_mapping(wallet_id, user_id)
                        
                        response_messages.append(f"To pay with USDC, please send exactly {usd_amount:.2f} USDC to the following address:\n\n`{wallet_address}`\n\nI will notify you once the payment is confirmed.")
                        state = "AWAITING_USDC_PAYMENT"
                        
                        # Add the expected amount to flight_details for verification later
                        flight_details['expected_usd_amount'] = usd_amount
                        save_session(user_id, state, conversation_history, [selected_flight], flight_details)
                    else:
                        response_messages.append("Sorry, I couldn't generate a USDC payment address at the moment. Please try again or select 'Card'.")
                        save_session(user_id, state, conversation_history, [selected_flight], flight_details)
                else:
                    response_messages.append("Sorry, I couldn't convert the flight price to USD. Please try again or select 'Card'.")
                    save_session(user_id, state, conversation_history, [selected_flight], flight_details)
            except (ValueError, TypeError):
                response_messages.append("Sorry, there was an issue processing the flight price. Please try again.")
                save_session(user_id, state, conversation_history, [selected_flight], flight_details)

        else:
            response_messages.append("I didn't understand. Please reply with 'Card' or 'USDC'.")
            save_session(user_id, state, conversation_history, flight_offers, flight_details)

    else:
        # Default fallback for unhandled states
        response_messages.append("I'm not sure how to handle that right now. Let's start over. Where would you like to go?")
        state = "GATHERING_INFO"
        save_session(user_id, state, [], [], {})

    return response_messages 