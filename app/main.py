import os
import json
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse

from app.ai_service import get_ai_response, extract_flight_details_from_history
from app.session_manager import load_session, save_session
from app.timezone_service import get_timezone_for_city
from app.amadeus_service import AmadeusService
from app.database import redis_client

load_dotenv()

app = Flask(__name__)
amadeus_service = AmadeusService()

def _format_flight_offers(user_id, flights):
    """Formats flight offers into a string and saves them to Redis."""
    if not flights:
        return "Sorry, I couldn't find any flights for the given criteria."

    response_lines = ["I found a few options for you:"]
    for i, flight in enumerate(flights[:5], 1):
        flight_id = f"flight_{i}"
        
        # Simplified flight details for demonstration
        itinerary = flight['itineraries'][0]
        price = flight['price']['total']
        
        # Save full flight details to Redis for booking
        if redis_client:
            redis_key = f"{user_id}:{flight_id}"
            redis_client.set(redis_key, json.dumps(flight), ex=3600)

        response_lines.append(f"{i}. Flight to {flight['itineraries'][0]['segments'][0]['arrival']['iataCode']} for {price} {flight['price']['currency']}. (Choose {flight_id})")

    return "\n".join(response_lines)

@app.route("/webhook", methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').lower()
    user_id = request.values.get('From', '')
    
    state, conversation_history = load_session(user_id)
    
    response_msg = ""
    
    if state == "GATHERING_INFO":
        ai_response, conversation_history = get_ai_response(incoming_msg, conversation_history)
        
        # Check if the AI has finished gathering information
        if "[INFO_COMPLETE]" in ai_response:
            response_msg = ai_response.replace("[INFO_COMPLETE]", "").strip()
            state = "AWAITING_CONFIRMATION"
        else:
            response_msg = ai_response
            
    elif state == "AWAITING_CONFIRMATION":
        if "yes" in incoming_msg or "correct" in incoming_msg:
            # User confirmed, now extract details and search for flights
            flight_details = extract_flight_details_from_history(conversation_history)
            
            if flight_details:
                origin_iata = amadeus_service.get_iata_code(flight_details.get('origin'))
                destination_iata = amadeus_service.get_iata_code(flight_details.get('destination'))

                if origin_iata and destination_iata:
                    flights = amadeus_service.search_flights(
                        origin_iata=origin_iata,
                        destination_iata=destination_iata,
                        departure_date=flight_details.get('departure_date'),
                        return_date=flight_details.get('return_date'),
                        adults=str(flight_details.get('number_of_travelers', '1'))
                    )
                    response_msg = _format_flight_offers(user_id, flights)
                    state = "FLIGHT_SELECTION" # Next state
                else:
                    response_msg = "I'm sorry, I couldn't find the airport codes for the cities you provided. Could you please be more specific?"
                    state = "GATHERING_INFO" # Go back to gathering
            else:
                response_msg = "I'm sorry, I had trouble understanding the flight details. Let's try again."
                state = "GATHERING_INFO"
        else:
            # User wants to correct information
            response_msg, conversation_history = get_ai_response(incoming_msg, conversation_history)
            state = "GATHERING_INFO"

    save_session(user_id, state, conversation_history)

    resp = MessagingResponse()
    resp.message(response_msg)
    return str(resp), 200, {'Content-Type': 'application/xml'}

if __name__ == "__main__":
    # Temporary test block to bypass pytest issues
    print("--- RUNNING TEMPORARY VALIDATION SCRIPT ---")
    
    # Simulate the conversation flow
    user_id = "test_user_123"
    
    # Turn 1: Initial message
    print("\n--- Turn 1: Initial Query ---")
    initial_message = "Hi, I want to book a one-way flight for John Doe from New York to London on 2024-12-25 for 1 adult."
    ai_reply_1, history_1 = get_ai_response(initial_message, [])
    print(f"AI Reply 1 (Confirmation):\n{ai_reply_1}")

    # Turn 2: User confirmation
    print("\n--- Turn 2: User Confirmation ---")
    ai_reply_2, history_2 = get_ai_response("Yes, that's correct.", history_1)
    print(f"AI Reply 2 (Trigger phrase):\n{ai_reply_2}")

    # Turn 3: Flight Search Logic
    print("\n--- Turn 3: JSON Extraction and Flight Search ---")
    if "start the search" in ai_reply_2:
        print("Trigger phrase detected. Extracting details...")
        flight_details = extract_flight_details_from_history(history_2)
        
        if flight_details:
            print(f"Successfully extracted flight details: {flight_details}")

            origin_iata = amadeus_service.get_iata_code(flight_details.get('origin'))
            destination_iata = amadeus_service.get_iata_code(flight_details.get('destination'))
            print(f"Found IATA codes: Origin={origin_iata}, Destination={destination_iata}")

            if origin_iata and destination_iata:
                flights = amadeus_service.search_flights(
                    origin_iata=origin_iata,
                    destination_iata=destination_iata,
                    departure_date=flight_details.get('departure_date'),
                    return_date=flight_details.get('return_date'),
                    adults=str(flight_details.get('number_of_travelers', '1'))
                )
                
                if flights:
                    formatted_flights = _format_flight_offers(user_id, flights)
                    print("\n--- Flight Search Result ---")
                    print(formatted_flights)
                else:
                    print("\n--- Flight Search Result ---")
                    print("Amadeus service returned no flights for the given criteria.")
            else:
                print("Could not find IATA codes for one or both cities.")
        else:
            print("Failed to extract flight details from the conversation.")
    else:
        print("Trigger phrase not detected in AI response.")

    print("\n--- TEMPORARY VALIDATION SCRIPT COMPLETE ---") 