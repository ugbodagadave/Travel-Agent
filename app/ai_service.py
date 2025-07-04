import os
import json
from openai import OpenAI

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

def get_ai_response(user_message: str, conversation_history: list) -> (str, list):
    """
    Sends the entire conversation history to the IO Intelligence API 
    and returns the AI's response and the updated history.
    """
    try:
        client = OpenAI(
            base_url="https://api.intelligence.io.solutions/api/v1",
            api_key=os.getenv("IO_API_KEY")
        )

        # Start with the system prompt, then add the existing history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(conversation_history)
        
        # Add the new user message
        messages.append({"role": "user", "content": user_message})

        chat_completion = client.chat.completions.create(
            messages=messages,
            model="google/gemma-3-27b-it",
        )
        
        ai_response = chat_completion.choices[0].message.content.strip()

        # Add the AI's response to the history for the next turn
        updated_history = messages[1:] # Exclude system prompt before saving
        updated_history.append({"role": "assistant", "content": ai_response})

        return ai_response, updated_history

    except Exception as e:
        print(f"Error calling IO Intelligence API: {e}")
        error_message = "Sorry, I'm having trouble connecting to my brain right now. Please try again later."
        return error_message, conversation_history

def extract_flight_details_from_history(conversation_history: list) -> dict:
    """
    Sends the conversation history to the AI with a specific prompt
    to extract flight details into a structured JSON object.
    """
    try:
        client = OpenAI(
            base_url="https://api.intelligence.io.solutions/api/v1",
            api_key=os.getenv("IO_API_KEY")
        )

        extraction_prompt = (
            "The following is a conversation with a user who wants to book a flight. "
            "Please extract the final, confirmed details for the traveler_name, origin, "
            "destination, departure_date, return_date, and number_of_travelers. "
            "Respond with ONLY a valid JSON object containing these fields. Do not add any other text."
        )

        messages = [{"role": "system", "content": extraction_prompt}]
        messages.extend(conversation_history)

        chat_completion = client.chat.completions.create(
            messages=messages,
            model="google/gemma-3-27b-it",
            response_format={"type": "json_object"},
        )
        
        json_response = chat_completion.choices[0].message.content.strip()
        return json.loads(json_response)

    except Exception as e:
        print(f"Error during JSON extraction: {e}")
        return None 