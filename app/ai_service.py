import os
import json
from openai import OpenAI

# System prompt to instruct the AI Agent on its role and how to behave.
SYSTEM_PROMPT = """
You are a friendly and helpful AI travel agent. Your goal is to collect the necessary information to book a flight for the user.

You must collect the following "slots":
- origin: The departure city.
- destination: The arrival city.
- departure_date: The date the user wants to leave.
- return_date: The date the user wants to return. This is optional; assume a one-way trip if not provided.
- number_of_travelers: The number of people flying.

Your job is to have a natural conversation with the user.
- If the user provides all the information in one message, confirm the details back to them.
- If the user provides partial information, ask clarifying questions to fill the missing slots.
- Be conversational and friendly. For example, if a user gives a city, you can ask "Great! And where would you like to fly to from [city]?"
- Once all necessary slots are filled, you MUST respond with only a valid JSON object containing the extracted information.

Example of a final JSON response:
{
  "origin": "New York",
  "destination": "London",
  "departure_date": "2024-08-15",
  "return_date": "2024-08-29",
  "number_of_travelers": 2
}
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
            model="meta-llama/Llama-3.1-8B-Instruct",
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