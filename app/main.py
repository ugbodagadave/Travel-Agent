import os
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse

from app.ai_service import get_ai_response

load_dotenv()

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles incoming messages from Twilio and responds using the AI service."""
    incoming_msg = request.values.get('Body', '').strip()
    resp = MessagingResponse()
    
    ai_reply = get_ai_response(incoming_msg)
    resp.message(ai_reply)

    return str(resp), 200, {'Content-Type': 'application/xml'}

if __name__ == "__main__":
    app.run(debug=True) 