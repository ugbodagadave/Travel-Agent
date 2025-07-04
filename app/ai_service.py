import os
from openai import OpenAI

def get_ai_response(message: str) -> str:
    """
    Sends a message to the IO Intelligence API and returns the AI's response.
    """
    try:
        client = OpenAI(
            base_url="https://api.intelligence.io.solutions/api/v1",
            api_key=os.getenv("IO_API_KEY")
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ],
            model="meta-llama/Llama-3.1-8B-Instruct", # A capable, general-purpose model
        )
        
        response = chat_completion.choices[0].message.content
        return response.strip()

    except Exception as e:
        print(f"Error calling IO Intelligence API: {e}")
        return "Sorry, I'm having trouble connecting to my brain right now. Please try again later." 