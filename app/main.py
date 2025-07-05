import os
import json
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse

from app.ai_service import get_ai_response, extract_flight_details_from_history, extract_traveler_details
from app.session_manager import load_session, save_session
from app.timezone_service import get_timezone_for_city
from app.amadeus_service import AmadeusService
from app.database import redis_client

load_dotenv()

app = Flask(__name__)
amadeus_service = AmadeusService()

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

@app.route("/webhook", methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').lower()
    user_id = request.values.get('From', '')
    
    state, conversation_history, flight_offers = load_session(user_id)
    
    response_msg = ""
    
    if state == "GATHERING_INFO":
        ai_response, updated_history = get_ai_response(incoming_msg, conversation_history)
        
        if "[INFO_COMPLETE]" in ai_response:
            response_msg = ai_response.replace("[INFO_COMPLETE]", "").strip() + "\n\nIs this information correct?"
            state = "AWAITING_CONFIRMATION"
        else:
            response_msg = ai_response
        
        save_session(user_id, state, updated_history, flight_offers)

    elif state == "AWAITING_CONFIRMATION":
        if "yes" in incoming_msg or "correct" in incoming_msg:
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
                    response_msg = _format_flight_offers(offers)
                    state = "FLIGHT_SELECTION"
                    save_session(user_id, state, conversation_history, offers)
                else:
                    response_msg = "I'm sorry, I couldn't find the airport codes. Please be more specific."
                    state = "GATHERING_INFO"
                    save_session(user_id, state, conversation_history, [])
            else:
                response_msg = "I had trouble understanding the details. Let's try again."
                state = "GATHERING_INFO"
                save_session(user_id, state, conversation_history, [])
        else:
            ai_response, updated_history = get_ai_response(incoming_msg, conversation_history)
            response_msg = ai_response
            state = "GATHERING_INFO"
            save_session(user_id, state, updated_history, [])

    elif state == "FLIGHT_SELECTION":
        if "no" in incoming_msg:
            response_msg = "Okay, let's start over. Where would you like to go?"
            state = "GATHERING_INFO"
            save_session(user_id, state, conversation_history, [])
        else:
            try:
                selection = int(incoming_msg.strip())
                if 1 <= selection <= len(flight_offers):
                    selected_flight = flight_offers[selection - 1]
                    response_msg = "To complete the booking, I need your full name (as on passport) and date of birth (YYYY-MM-DD)."
                    state = "GATHERING_BOOKING_DETAILS"
                    save_session(user_id, state, conversation_history, [selected_flight])
                else:
                    response_msg = "Invalid selection. Please choose a number from the list."
                    save_session(user_id, state, conversation_history, flight_offers)
            except (ValueError, IndexError):
                response_msg = "I didn't understand. Please reply with the flight number."
                save_session(user_id, state, conversation_history, flight_offers)

    elif state == "GATHERING_BOOKING_DETAILS":
        selected_flight = flight_offers[0]
        traveler_details = extract_traveler_details(incoming_msg)

        if traveler_details and "fullName" in traveler_details and "dateOfBirth" in traveler_details:
            full_name = traveler_details["fullName"].split()
            first_name = full_name[0]
            last_name = " ".join(full_name[1:]) if len(full_name) > 1 else ""

            traveler = {
                "id": "1",
                "dateOfBirth": traveler_details["dateOfBirth"],
                "name": {"firstName": first_name, "lastName": last_name},
                "contact": {
                    "emailAddress": "jorge.gonzales@example.com",
                    "phones": [{"deviceType": "MOBILE", "countryCallingCode": "34", "number": "480080072"}]
                },
                "documents": [{
                    "documentType": "PASSPORT",
                    "birthPlace": "Madrid",
                    "issuanceLocation": "Madrid",
                    "issuanceDate": "2015-04-14",
                    "number": "00000000",
                    "expiryDate": "2026-04-14",
                    "issuanceCountry": "ES",
                    "validityCountry": "ES",
                    "nationality": "ES",
                    "holder": True
                }]
            }
            
            booking_result = amadeus_service.book_flight(selected_flight, traveler)
            
            if booking_result:
                response_msg = f"Your flight is booked! Your Order ID is: {booking_result['id']}"
                state = "BOOKING_COMPLETE"
            else:
                response_msg = "There was an error booking your flight. Please try again."
                state = "GATHERING_INFO"
        else:
            response_msg = "I'm sorry, I couldn't understand your details. Please provide your full name and date of birth (YYYY-MM-DD) again."
            # State remains GATHERING_BOOKING_DETAILS
        
        save_session(user_id, state, conversation_history, flight_offers)

    resp = MessagingResponse()
    resp.message(response_msg)
    return str(resp)

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
                    formatted_flights = _format_flight_offers(flights)
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