import threading
import os
from app.new_session_manager import load_session, save_session
from app.ai_service import get_ai_response, extract_flight_details_from_history, extract_traveler_details, extract_traveler_names
from app.amadeus_service import AmadeusService
from app.payment_service import create_checkout_session
from app.tasks import search_flights_task, poll_usdc_payment_task, poll_circlelayer_payment_task
from app.circle_service import CircleService
from app.currency_service import CurrencyService
from app.new_session_manager import save_wallet_mapping, save_evm_mapping, get_next_address_index, save_circlelayer_payment_info
import app.circlelayer_service as circlelayer_service
from dateutil import parser

TRAVEL_CLASSES = ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"]

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
    try:
        state, conversation_history, flight_offers, flight_details = load_session(user_id)
        print(f"[Core Logic] Loaded session for {user_id}: state={state}")
    except Exception as e:
        print(f"[Core Logic] ERROR loading session for {user_id}: {e}")
        # Fallback to default state if Redis fails
        state, conversation_history, flight_offers, flight_details = "GATHERING_INFO", [], [], {}
    
    response_messages = []

    # NOTE: This is a simplified version of the logic from app/main.py's webhook.
    # It does not yet include payment or final booking logic.
    if state == "GATHERING_INFO":
        ai_response, updated_history = get_ai_response(incoming_msg, conversation_history, state)
        
        if "[INFO_COMPLETE]" in ai_response:
            # The AI service should return a dictionary, but we safeguard against it returning a list.
            extracted_data = extract_flight_details_from_history(updated_history)
            if isinstance(extracted_data, list) and extracted_data:
                flight_details = extracted_data[0] # Take the first element if it's a list
            elif isinstance(extracted_data, dict):
                flight_details = extracted_data
            else:
                flight_details = {} # Default to empty dict if something is wrong

            # Try to get the number of travelers, default to 1 if not found or invalid
            try:
                num_travelers = int(flight_details.get("number_of_travelers", 1))
            except (ValueError, TypeError):
                num_travelers = 1

            if num_travelers > 1:
                state = "GATHERING_NAMES"
                response_messages.append(f"It looks like there are {num_travelers} travelers. Please provide their full names, separated by commas.")
                try:
                    save_session(user_id, state, updated_history, flight_offers, flight_details)
                    print(f"[Core Logic] Session saved for {user_id}")
                except Exception as e:
                    print(f"[Core Logic] WARNING: Could not save session for {user_id}: {e}")
                    # Continue processing even if session save fails
            else:
                # For a single traveler, go directly to class selection
                state = "AWAITING_CLASS_SELECTION"
                class_options_text = "What class would you like to fly? You can choose from: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST."
                response_messages.append(class_options_text)
                # Also add user's last message and our prompt to history
                updated_history.append({"role": "assistant", "content": class_options_text})
                try:
                    save_session(user_id, state, updated_history, flight_offers, flight_details)
                    print(f"[Core Logic] Session saved for {user_id}")
                except Exception as e:
                    print(f"[Core Logic] WARNING: Could not save session for {user_id}: {e}")
                    # Continue processing even if session save fails
        else:
            response_messages.append(ai_response)
            try:
                save_session(user_id, state, updated_history, flight_offers, flight_details)
                print(f"[Core Logic] Session saved for {user_id}")
            except Exception as e:
                print(f"[Core Logic] WARNING: Could not save session for {user_id}: {e}")
                # Continue processing even if session save fails

    elif state == "GATHERING_NAMES":
        num_travelers = int(flight_details.get("number_of_travelers", 1))
        names = extract_traveler_names(incoming_msg, num_travelers)

        if names:
            flight_details["traveler_names"] = names
            state = "AWAITING_CLASS_SELECTION"
            
            class_options_text = "What class would you like to fly? You can choose from: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST."
            response_messages.append("Great, I have all the names.")
            response_messages.append(class_options_text)
            
            # Save the updated details and new state
            conversation_history.append({"role": "user", "content": incoming_msg})
            conversation_history.append({"role": "assistant", "content": "Great, I have all the names.\n" + class_options_text})
            save_session(user_id, state, conversation_history, flight_offers, flight_details)
        else:
            response_messages.append(f"I'm sorry, I couldn't understand the names. Please provide exactly {num_travelers} full names, separated by commas.")
            save_session(user_id, state, conversation_history, flight_offers, flight_details)

    elif state == "AWAITING_CLASS_SELECTION":
        selected_class = incoming_msg.strip().upper()

        if selected_class in TRAVEL_CLASSES:
            flight_details['travel_class'] = selected_class
            state = "AWAITING_CONFIRMATION"

            # Build the final confirmation message
            confirmation_text = "Great. Please confirm the details for your flight search:\n"
            details_summary = []
            # Use a specific order for readability
            order = ['origin', 'destination', 'departure_date', 'return_date', 'number_of_travelers', 'traveler_name', 'travel_class', 'traveler_names']
            
            for key in order:
                if key in flight_details:
                    value = flight_details[key]
                    if key == "traveler_names":
                        details_summary.append(f"- Travelers: {', '.join(value)}")
                    elif key == "traveler_name":
                        details_summary.append(f"- Traveler: {value}")
                    elif key == "travel_class":
                        details_summary.append(f"- Class: {value.title()}")
                    else:
                        details_summary.append(f"- {key.replace('_', ' ').title()}: {value}")

            confirmation_text += "\n".join(details_summary)
            confirmation_text += "\n\nIs this all correct?"
            response_messages.append(confirmation_text)

            # Update history and save session
            conversation_history.append({"role": "user", "content": incoming_msg})
            conversation_history.append({"role": "assistant", "content": confirmation_text})
            save_session(user_id, state, conversation_history, flight_offers, flight_details)
        else:
            # Handle invalid class selection
            response_messages.append("That's not a valid class. Please choose from: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST.")
            save_session(user_id, state, conversation_history, flight_offers, flight_details)

    elif state == "AWAITING_CONFIRMATION":
        ai_response, updated_history = get_ai_response(incoming_msg, conversation_history, state)

        if "[CONFIRMED]" in ai_response:
            # Re-load details from session in case this is the second confirmation
            _, _, _, flight_details = load_session(user_id)
            
            if flight_details:
                # --- Date Formatting ---
                # The AI may return a human-readable date, so we must parse and reformat it.
                try:
                    departure_date_str = flight_details.get("departure_date")
                    if departure_date_str:
                        # Parse the date string and reformat to YYYY-MM-DD
                        dt_object = parser.parse(departure_date_str)
                        flight_details["departure_date"] = dt_object.strftime('%Y-%m-%d')
                except (ValueError, TypeError) as e:
                    print(f"[{user_id}] - WARNING: Could not parse departure_date '{flight_details.get('departure_date')}'. Error: {e}")
                    # If parsing fails, we might send an error message or let the Amadeus API handle it.
                    # For now, we'll proceed and let Amadeus validate.
                
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
            # This means the user made a correction. Re-extract details.
            extracted_data = extract_flight_details_from_history(updated_history)
            if isinstance(extracted_data, list) and extracted_data:
                flight_details = extracted_data[0] # Safeguard
            elif isinstance(extracted_data, dict):
                flight_details = extracted_data
            else:
                flight_details = {} # Default

            # We must re-ask for class if it was part of the correction.
            if 'travel_class' not in flight_details:
                state = "AWAITING_CLASS_SELECTION"
                class_options_text = "It looks like the details were updated. What class would you like to fly? You can choose from: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST."
                response_messages.append(class_options_text)
                updated_history.append({"role": "assistant", "content": class_options_text})
            else:
                # If class is still present, re-confirm all details
                confirmation_text = "Got it. Please confirm the updated details:\n"
                details_summary = []
                order = ['origin', 'destination', 'departure_date', 'return_date', 'number_of_travelers', 'traveler_name', 'travel_class', 'traveler_names']
                for key in order:
                    if key in flight_details:
                        value = flight_details[key]
                        if key == "traveler_names":
                            details_summary.append(f"- Travelers: {', '.join(value)}")
                        elif key == "traveler_name":
                            details_summary.append(f"- Traveler: {value}")
                        elif key == "travel_class":
                            details_summary.append(f"- Class: {value.title()}")
                        else:
                            details_summary.append(f"- {key.replace('_', ' ').title()}: {value}")
                
                confirmation_text += "\n".join(details_summary)
                confirmation_text += "\n\nIs this correct?"
                response_messages.append(confirmation_text)
                updated_history.append({"role": "assistant", "content": confirmation_text})

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
                    selected_flight = flight_offers[selection - 1] # Correctly index the selected flight
                    
                    state = "AWAITING_PAYMENT_SELECTION"
                    response_messages.append("You've selected a great flight. How would you like to pay? (Reply with 'Card', 'USDC', or 'Pay on-chain (Circle Layer)')")
                    
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
            try:
                # TODO: This is a temporary override for testing with the Circle Testnet Faucet,
                # which only allows sending a maximum of 10 USDC at a time.
                # In production, the actual converted amount should be used.
                usd_amount = 10.00
                
                # The original currency conversion logic is left here for future reference.
                # price_str = selected_flight.get('price', {}).get('total')
                # currency = selected_flight.get('price', {}).get('currency', 'USD')
                # usd_amount = currency_service.convert_to_usd(float(price_str), currency)

                if usd_amount:
                    wallet_info = circle_service.create_payment_intent(usd_amount)
                    if wallet_info:
                        payment_intent_id = wallet_info.get('walletId') # Correct key is walletId
                        wallet_address = wallet_info.get('address')
                        
                        # Save the payment_intent_id -> user_id mapping
                        if payment_intent_id and wallet_address:
                            save_wallet_mapping(payment_intent_id, user_id)
                            
                            # Using a hardcoded test amount in the message
                            response_messages.append(f"To pay with USDC, please send exactly {usd_amount:.2f} USDC (test amount) to the address below. I will notify you once the payment is confirmed.")
                            # Send the address in a separate message with no formatting for easy copying.
                            response_messages.append(wallet_address)
                            state = "AWAITING_USDC_PAYMENT"
                            
                            # Add the expected amount to flight_details for verification later
                            flight_details['expected_usd_amount'] = usd_amount
                            save_session(user_id, state, conversation_history, [selected_flight], flight_details)

                            # ------------------------------------------------
                            # Start background polling for the USDC payment
                            # ------------------------------------------------
                            try:
                                poll_thread = threading.Thread(target=poll_usdc_payment_task, args=(user_id, payment_intent_id))
                                poll_thread.start()
                                print(f"[{user_id}] - INFO: Started polling thread for payment intent {payment_intent_id}.")
                            except Exception as e:
                                print(f"[{user_id}] - ERROR: Could not start polling thread: {e}")
                        else:
                            response_messages.append("Sorry, I couldn't generate a USDC payment address at the moment. Please try again or select 'Card'.")
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

        elif "circle layer" in incoming_msg.lower() or "clayer" in incoming_msg.lower() or "circlelayer" in incoming_msg.lower():
            try:
                # Native token configuration
                token_symbol = os.getenv("CIRCLE_LAYER_TOKEN_SYMBOL", "CLAYER")
                decimals = int(os.getenv("CIRCLE_LAYER_TOKEN_DECIMALS", "18"))
                token_address = None  # Native token - no contract address needed
                
                # Calculate amount in wei (smallest unit)
                amount_in_tokens = 1.0  # 1 CLAYER
                amount_units = int(amount_in_tokens * (10 ** decimals))
                
                # Get unique address index to prevent reuse
                address_index = get_next_address_index()
                
                # Derive a unique deposit address
                deposit = circlelayer_service.CircleLayerService.create_deposit_address(index=address_index)
                deposit_address = deposit.get("address")

                if deposit_address:
                    # Get initial balance to track payment increase
                    try:
                        circlelayer_svc = circlelayer_service.CircleLayerService()
                        initial_balance = circlelayer_svc.check_native_balance(deposit_address)
                        print(f"[{user_id}] - INFO: Initial balance at {deposit_address}: {initial_balance} wei")
                    except Exception as e:
                        print(f"[{user_id}] - WARNING: Could not get initial balance: {e}")
                        initial_balance = 0
                    
                    # Save payment tracking information
                    save_circlelayer_payment_info(
                        user_id=user_id,
                        address=deposit_address,
                        initial_balance=initial_balance,
                        expected_amount=amount_units,
                        address_index=address_index
                    )
                    
                    save_evm_mapping(deposit_address, user_id)

                    # Persist details for verification
                    flight_details["circlelayer"] = {
                        "address": deposit_address,
                        "token_address": token_address,  # None for native token
                        "amount": amount_units,
                        "decimals": decimals,
                        "address_index": address_index,
                        "initial_balance": initial_balance,
                    }
                    state = "AWAITING_CIRCLE_LAYER_PAYMENT"
                    save_session(user_id, state, conversation_history, [selected_flight], flight_details)

                    # Notify user (two messages for easy copy of address)
                    response_messages.append(
                        f"To pay on Circle Layer Testnet, please send exactly {amount_in_tokens:.2f} {token_symbol} to the address below. I will notify you once the payment is confirmed."
                    )
                    response_messages.append(deposit_address)

                    # Start background poller for native token balance
                    try:
                        poll_thread = threading.Thread(
                            target=poll_circlelayer_payment_task,
                            args=(user_id, deposit_address, token_address, amount_units, decimals),
                        )
                        poll_thread.start()
                        print(f"[{user_id}] - INFO: Started Circle Layer polling for payment at {deposit_address} (index {address_index})")
                    except Exception as e:
                        print(f"[{user_id}] - ERROR: Could not start Circle Layer polling thread: {e}")
                else:
                    response_messages.append("Sorry, I couldn't generate a Circle Layer address right now. Please try again or choose 'Card'.")
                    save_session(user_id, state, conversation_history, [selected_flight], flight_details)
            except Exception as e:
                print(f"[{user_id}] - ERROR in Circle Layer payment flow: {e}")
                response_messages.append("Sorry, something went wrong initializing Circle Layer payment. Please try again or choose 'Card'.")
                save_session(user_id, state, conversation_history, [selected_flight], flight_details)

        else:
            response_messages.append("I didn't understand. Please reply with 'Card', 'USDC', or 'Pay on-chain (Circle Layer)'.")
            save_session(user_id, state, conversation_history, flight_offers, flight_details)

    elif state == "BOOKING_CONFIRMED":
        # If the user wants to start a new booking, reset the state.
        if "start over" in incoming_msg.lower() or "new booking" in incoming_msg.lower():
            state = "GATHERING_INFO"
            response_messages.append("Of course. I can help with a new flight search. Where would you like to go?")
            # Clear previous flight data for the new session
            save_session(user_id, state, [], [], {})
        else:
            # Otherwise, inform them that the booking is complete.
            response_messages.append("Your previous booking is complete. If you'd like to search for a new flight, please say 'start over' or 'new booking'.")
            save_session(user_id, state, conversation_history, flight_offers, flight_details)

    else:
        # Default fallback for unhandled states
        response_messages.append("I'm not sure how to handle that right now. Let's start over. Where would you like to go?")
        state = "GATHERING_INFO"
        save_session(user_id, state, [], [], {})

    return response_messages
