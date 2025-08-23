import os
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/"

def send_message(chat_id, text, parse_mode=None):
    """
    Sends a message to a given chat_id via the Telegram Bot API.
    """
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
        
    try:
        response = requests.post(f"{TELEGRAM_API_URL}sendMessage", json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Telegram: {e}")
        return None

def send_pdf(chat_id, pdf_bytes, filename="itinerary.pdf"):
    """
    Sends a PDF document to a Telegram user.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    files = {'document': (filename, pdf_bytes, 'application/pdf')}
    data = {'chat_id': chat_id}
    
    try:
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()
        print(f"PDF sent to Telegram chat_id {chat_id}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending PDF to Telegram: {e}")
        return None 

def send_telegram_pdf(chat_id, pdf_bytes, filename):
    """Sends a PDF file to a given Telegram chat ID."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    
    files = {'document': (filename, pdf_bytes, 'application/pdf')}
    data = {'chat_id': chat_id}
    
    try:
        response = requests.post(url, files=files, data=data, timeout=20)
        response.raise_for_status()
        print(f"PDF sent to Telegram chat {chat_id}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending PDF to {chat_id}: {e}")
        if e.response:
            print(f"Response: {e.response.text}") 