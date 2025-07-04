import os
import json
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse

from app.ai_service import get_ai_response
from app.session_manager import load_session, save_session
from app.timezone_service import get_timezone_for_city

load_dotenv()

app = Flask(__name__)

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

    # Check if the AI returned a JSON object with flight details
    try:
        flight_details = json.loads(ai_reply)
        origin_city = flight_details.get('origin')
        
        # Try to get the timezone
        timezone = get_timezone_for_city(origin_city) if origin_city else "Unknown"
        
        # Format a confirmation message
        confirmation_message = (
            f"Great! I have all the details. "
            f"Flying from {flight_details.get('origin')} to {flight_details.get('destination')} "
            f"on {flight_details.get('departure_date')} for {flight_details.get('number_of_travelers')} people."
        )
        if timezone and timezone != "Unknown":
             confirmation_message += f" (Timezone detected: {timezone})"
        
        resp.message(confirmation_message)
    except (json.JSONDecodeError, TypeError, KeyError):
        # If it's not JSON, it's a regular chat message
        resp.message(ai_reply)

    return str(resp), 200, {'Content-Type': 'application/xml'}

if __name__ == "__main__":
    app.run(debug=True) 