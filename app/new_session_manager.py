import json
from .database import SessionLocal, Conversation

def save_session(session_id, state, conversation_history, flight_offers=None):
    """
    Saves the session data (state, history, flight offers) to the PostgreSQL database.
    """
    session_data = {
        "state": state,
        "conversation_history": conversation_history,
        "flight_offers": flight_offers or []
    }
    
    db = SessionLocal()
    try:
        # Create a new Conversation record or update the existing one.
        db_conversation = Conversation(
            user_id=session_id,
            history=session_data
        )
        db.merge(db_conversation)
        db.commit()
    finally:
        db.close()

def load_session(session_id):
    """
    Loads session data directly from the PostgreSQL database.
    """
    db = SessionLocal()
    try:
        db_conversation = db.query(Conversation).filter(Conversation.user_id == session_id).first()
        if db_conversation:
            session_data = db_conversation.history
            state = session_data.get("state", "GATHERING_INFO")
            history = session_data.get("conversation_history", [])
            offers = session_data.get("flight_offers", [])
            return state, history, offers
    finally:
        db.close()
        
    # If no session is found in the database, return a new session.
    return "GATHERING_INFO", [], [] 