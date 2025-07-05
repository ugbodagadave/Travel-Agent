import json
import os

SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

def save_session(session_id, state, conversation_history, flight_offers=None):
    """Saves the session data to a JSON file."""
    session_data = {
        "state": state,
        "conversation_history": conversation_history,
        "flight_offers": flight_offers or []
    }
    session_file = os.path.join(SESSION_DIR, f"{session_id}.json")
    with open(session_file, 'w') as f:
        json.dump(session_data, f, indent=2)

def load_session(session_id):
    """Loads the session data from a JSON file."""
    session_file = os.path.join(SESSION_DIR, f"{session_id}.json")
    if os.path.exists(session_file):
        with open(session_file, 'r') as f:
            try:
                session_data = json.load(f)
                state = session_data.get("state", "GATHERING_INFO")
                history = session_data.get("conversation_history", [])
                offers = session_data.get("flight_offers", [])
                return state, history, offers
            except json.JSONDecodeError:
                pass  # Ignore corrupted or empty session files
    return "GATHERING_INFO", [], []

def store_session(session_id, session_data):
    """A compatibility function for tests that expect a single session object."""
    state = session_data.get("state", "GATHERING_INFO")
    history = session_data.get("conversation_history", [])
    offers = session_data.get("flight_offers", [])
    save_session(session_id, state, history, offers) 