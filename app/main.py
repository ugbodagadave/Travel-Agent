import os
import json
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse

from app.ai_service import get_ai_response
from app.session_manager import load_session, save_session
from app.timezone_service import get_timezone_for_city
from app.amadeus_service import AmadeusService
from app.database import redis_client

load_dotenv()

app = Flask(__name__)
amadeus_service = AmadeusService()

def _format_flight_offers(user_id, flights):
    """ Formats flight offers and stores them in Redis. """
    if not flights:
        return "Sorry, I couldn't find any flights for your request. Would you like to try different dates?"
    
    response_lines = ["I found a few options for you:"]
    for i, flight in enumerate(flights, 1):
        # Clear previous flight options for the user
        if i == 1:
            keys = redis_client.keys(f"flight_option:{user_id}:*")
            if keys:
                redis_client.delete(*keys)

        price = flight['price']['total']
        # Get the first itinerary and segment for flight details
        itinerary = flight['itineraries'][0]
        segment = itinerary['segments'][0]
        departure_time = segment['departure']['at']
        arrival_time = segment['arrival']['at']
        duration = itinerary['duration'].replace('PT', '').replace('H', ' hours ').replace('M', ' minutes')

        line = (
            f"{i}. Depart at {departure_time}, Arrive at {arrival_time}. "
            f"Duration: {duration}. Price: {price} {flight['price']['currency']}"
        )
        response_lines.append(line)

        # Store the full flight data in Redis for later booking
        redis_client.set(f"flight_option:{user_id}:{i}", json.dumps(flight), ex=3600) # Expires in 1 hour

    response_lines.append("\nPlease reply with the number of the flight you'd like to book (e.g., '1').")
    return "\n".join(response_lines)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles stateful conversations using Redis for session management."""
    incoming_msg = request.values.get('Body', '').strip()
    user_id = request.values.get('From', '').strip()
    resp = MessagingResponse()

    # Load previous conversation history
    conversation_history = load_session(user_id)

    # Get the new AI response and updated history
    ai_reply, updated_history = get_ai_response(incoming_msg, conversation_history)

    # Save the updated history for the next interaction
    save_session(user_id, updated_history)

    # Check if the AI returned a JSON object indicating the conversation is complete
    try:
        data = json.loads(ai_reply)
        if data.get("status") == "complete":
            # The user has confirmed the details. The slots are in the AI's previous message.
            # History is: [..., assistant_slots, user_confirmation, assistant_complete_status]
            # The 'updated_history' includes the final "complete" status, so we look at [-3].
            if len(updated_history) >= 3:
                # The message content from the assistant could be "Confirmation message\n{json...}"
                content = updated_history[-3].get('content', '')
                json_str = content[content.find('{'):] # Extract JSON part of the string
                
                try:
                    flight_details = json.loads(json_str)
                except json.JSONDecodeError:
                    resp.message("I seem to have lost the flight details. Could you please start over?")
                    return str(resp), 200, {'Content-Type': 'application/xml'}
            else:
                resp.message("Something went wrong. Could you please try again?")
                return str(resp), 200, {'Content-Type': 'application/xml'}

            origin_city = flight_details.get('origin')
            destination_city = flight_details.get('destination')
            
            # Get IATA codes
            origin_iata = amadeus_service.get_iata_code(origin_city)
            destination_iata = amadeus_service.get_iata_code(destination_city)

            if not origin_iata or not destination_iata:
                resp.message("Sorry, I couldn't find one of the cities you mentioned. Please be more specific.")
                return str(resp), 200, {'Content-Type': 'application/xml'}
            
            # Search for flights
            flights = amadeus_service.search_flights(
                origin_iata=origin_iata,
                destination_iata=destination_iata,
                departure_date=flight_details.get('departure_date'),
                return_date=flight_details.get('return_date'),
                adults=flight_details.get('number_of_travelers')
            )
            
            # Format and send the flight offers to the user
            response_message = _format_flight_offers(user_id, flights)
            resp.message(response_message)
        else:
            # It's a regular chat message from the AI (e.g., asking a question or for confirmation)
            resp.message(ai_reply)

    except (json.JSONDecodeError, TypeError):
        # If it's not JSON, it's the AI asking a question or confirming slots.
        # This will include the flight details in a JSON block for the user to confirm.
        resp.message(ai_reply)

    return str(resp), 200, {'Content-Type': 'application/xml'}

if __name__ == "__main__":
    app.run(debug=True) 