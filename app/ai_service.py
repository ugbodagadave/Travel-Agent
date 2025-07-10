import os
import json
import openai
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# System prompt to instruct the AI Agent on its role and how to behave.
SYSTEM_PROMPT_GATHER_INFO = """
You are Flai a friendly and helpful AI travel agent.
You are precise and concise; you can use emojis to feel friendly and engaging.
Emojis that are relatable with travel are: 🛫, 🛬, 🛩, 🛩️, 🛩️️, 🛩️️️, 🛩️️️️, 🛩️️️️️, 🛩️️️️️️, 🛩️️️️️️️, 🛩️️️️️️️️, 🛩️️️️️️️️️, 🛩️️️️️️️️️️, 🛩️️️️️️️️️️️, 🛩️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, 🛩️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️️, f you're not sure which city the user means (e.g., they say "London" but there are multiple), ask for clarification.
 Your goal is to fill these slots.
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

SYSTEM_PROMPT_CONFIRMATION = """
You are a helpful AI travel agent. The user has been presented with a summary of their flight details and asked to confirm.
Your task is to determine if the user's response is a confirmation or a correction.

- If the user's message is a confirmation (e.g., "yes", "correct", "yup", "yeap", "that's right"), you MUST respond with only the special token: `[CONFIRMED]`
- If the user's message is a correction (e.g., "no, to Rome", "actually 2 people"), you must integrate the correction and restate the updated information, then ask for confirmation again. End this message with the `[INFO_COMPLETE]` token.
- Do not be conversational unless making a correction.

Example 1:
User: "Yeap, that's correct"
Your response: `[CONFIRMED]`

Example 2:
User: "no, there will be 3 of us"
Your response: "My mistake! So that's 3 travelers in total. I have you flying from New York to London on Dec 25th. Is this correct? [INFO_COMPLETE]"
"""

# Configure the OpenAI client for io.net
client = openai.OpenAI(
    api_key=os.getenv("IO_API_KEY"),
    base_url="https://api.intelligence.io.solutions/api/v1/",
)

def get_ai_response(user_message: str, conversation_history: list, state: str) -> (str, list):
    if not conversation_history:
        # Start of a new conversation
        system_prompt = SYSTEM_PROMPT_GATHER_INFO
        conversation_history.append({"role": "system", "content": system_prompt})
    
    # Check if the last system message is outdated for the current state
    last_system_message = next((msg for msg in reversed(conversation_history) if msg['role'] == 'system'), None)

    if state == "AWAITING_CONFIRMATION" and (not last_system_message or last_system_message['content'] != SYSTEM_PROMPT_CONFIRMATION):
        conversation_history.append({"role": "system", "content": SYSTEM_PROMPT_CONFIRMATION})
    elif state == "GATHERING_INFO" and (not last_system_message or last_system_message['content'] != SYSTEM_PROMPT_GATHER_INFO):
        conversation_history.append({"role": "system", "content": SYSTEM_PROMPT_GATHER_INFO})
    
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
        # Check if the exception has response data to get more details
        if hasattr(e, 'response') and e.response and e.response.text:
            print(f"Error communicating with OpenAI API. Status: {e.response.status_code}, Response: {e.response.text}")
        else:
            print(f"An unexpected error occurred with the OpenAI API: {e}")
            
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
            model="meta-llama/Llama-3.3-70B-Instruct",
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
    # Limit the history to the last 10 messages to keep the prompt concise
    recent_history = conversation_history[-10:]
    
    # Convert the list of dicts into a clean string representation
    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_history if msg['role'] != 'system'])

    prompt = f"""
    Based on the following conversation history, extract the flight details into a JSON object.
    The current year is {datetime.now().year}.
    The JSON object should have these exact keys: "origin", "destination", "departure_date", "return_date", "number_of_travelers".
    - "departure_date" and "return_date" must be in YYYY-MM-DD format.
    - "return_date" should be null if it's a one-way trip.
    - "number_of_travelers" should be an integer.

    Conversation:
    {history_str}

    JSON output:
    """
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct",
            messages=[
                {"role": "system", "content": "You are a data extraction expert that always returns JSON."},
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