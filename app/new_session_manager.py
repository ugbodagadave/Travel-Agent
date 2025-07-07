import json
from .database import redis_client, SessionLocal, Conversation

def save_session(session_id, state, conversation_history, flight_offers=None):
    """
    Saves the session data to Redis for caching and PostgreSQL for persistence.
    """
    session_data = {
        "state": state,
        "conversation_history": conversation_history,
        "flight_offers": flight_offers or []
    }
    
    # Save to Redis cache
    if redis_client:
        redis_client.set(session_id, json.dumps(session_data))

    # Save to PostgreSQL
    db = SessionLocal()
    try:
        # Use merge to either insert a new record or update an existing one
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
    Loads session data, checking Redis cache first, then falling back to PostgreSQL.
    """
    # Try to load from Redis cache first
    if redis_client:
        cached_session = redis_client.get(session_id)
        if cached_session:
            session_data = json.loads(cached_session)
            state = session_data.get("state", "GATHERING_INFO")
            history = session_data.get("conversation_history", [])
            offers = session_data.get("flight_offers", [])
            return state, history, offers

    # If not in cache, load from PostgreSQL
    db = SessionLocal()
    try:
        db_conversation = db.query(Conversation).filter(Conversation.user_id == session_id).first()
        if db_conversation:
            session_data = db_conversation.history
            # Cache the loaded session in Redis for next time
            if redis_client:
                redis_client.set(session_id, json.dumps(session_data))
            
            state = session_data.get("state", "GATHERING_INFO")
            history = session_data.get("conversation_history", [])
            offers = session_data.get("flight_offers", [])
            return state, history, offers
    finally:
        db.close()
        
    # If not found in either, return a new session
    return "GATHERING_INFO", [], [] 