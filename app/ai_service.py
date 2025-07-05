import os
import json
import openai
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# System prompt to instruct the AI Agent on its role and how to behave.
SYSTEM_PROMPT = """
You are a friendly and helpful AI travel agent. Your goal is to fill these slots.
- If a user specifies a one-way trip or does not provide a return date, do not ask for one.
- Once you have all the required information, confirm it back to the user.
- At the very end of your confirmation message, you MUST append the special token `[INFO_COMPLETE]`.

You must collect the following "slots":
- traveler_name: The user's full name as it appears on their passport.
- origin: The departure city.
- destination: The arrival city.
- departure_date: The date the user wants to leave.
- return_date: The date the user wants to return. This is optional; assume a one-way trip if not provided.
- number_of_travelers: The number of people flying.

Example:
"I have you flying from New York to London on Dec 25th. Is this correct? [INFO_COMPLETE]"
"""

# Configure the OpenAI client for io.net
client = openai.OpenAI(
    api_key=os.getenv("IO_API_KEY"),
    base_url="https://api.intelligence.io.solutions/api/v1/",
)

def get_ai_response(user_message: str, conversation_history: list) -> (str, list):
    if not conversation_history:
        conversation_history.append({"role": "system", "content": SYSTEM_PROMPT})
    
    conversation_history.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct",
            messages=conversation_history
        )
        ai_response = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": ai_response})
        return ai_response, conversation_history
    except Exception as e:
        print(f"Error communicating with OpenAI: {e}")
        return "Sorry, I'm having trouble connecting to my brain right now. Please try again in a moment.", conversation_history

def extract_traveler_details(message: str) -> dict:
    """
    Uses OpenAI to extract traveler's full name and date of birth from a message.
    """
    prompt = f"""
    Extract the full name and date of birth (YYYY-MM-DD) from the following user message.
    The user might provide the information in various formats.
    Return a JSON object with the keys "fullName" and "dateOfBirth".

    User message: "{message}"

    JSON output:
    """
    
    try:
        response = client.chat.completions.create(
            model="google/gemma-3-27b-it",
            messages=[
                {"role": "system", "content": "You are a data extraction expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        extracted_text = response.choices[0].message.content
        return json.loads(extracted_text)
    except (json.JSONDecodeError, IndexError, Exception) as e:
        print(f"Error extracting traveler details: {e}")
        return {}

def extract_flight_details_from_history(conversation_history: list) -> dict:
    prompt = f"""
    Based on the following conversation history, extract the flight details into a JSON object.
    ...
    """
    try:
        response = client.chat.completions.create(
            model="google/gemma-3-27b-it",
            messages=[
                {"role": "system", "content": "You are a data extraction expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        extracted_text = response.choices[0].message.content
        return json.loads(extracted_text)
    except (json.JSONDecodeError, IndexError, Exception) as e:
        print(f"Error extracting flight details: {e}")
        return {} 