import json
import os
import redis
from . import database
from .database import Conversation

# --- Redis Connection ---
# It's recommended to use a connection pool in a real application
redis_client = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
SESSION_EXPIRATION = 86400 # 24 hours in seconds

def save_session(session_id, state, conversation_history, flight_offers=None):
    """
    Saves the session data to both Redis (for caching) and PostgreSQL (for persistence).
    """
    session_data = {
        "state": state,
        "conversation_history": conversation_history,
        "flight_offers": flight_offers or []
    }
    
    # Save to Redis
    try:
        redis_client.setex(session_id, SESSION_EXPIRATION, json.dumps(session_data))
    except redis.exceptions.RedisError as e:
        print(f"Error saving session to Redis: {e}")

    # Save to PostgreSQL
    db = database.SessionLocal()
    try:
        db_conversation = database.Conversation(
            user_id=session_id,
            history=session_data
        )
        db.merge(db_conversation)
        db.commit()
    finally:
        db.close()

def load_session(session_id):
    """
    Loads session data, checking Redis first (cache) and then falling back to PostgreSQL.
    """
    # 1. Try to load from Redis
    try:
        cached_session = redis_client.get(session_id)
        if cached_session:
            session_data = json.loads(cached_session)
            state = session_data.get("state", "GATHERING_INFO")
            history = session_data.get("conversation_history", [])
            offers = session_data.get("flight_offers", [])
            return state, history, offers
    except redis.exceptions.RedisError as e:
        print(f"Error loading session from Redis: {e}")

    # 2. If cache miss, load from PostgreSQL
    db = database.SessionLocal()
    try:
        db_conversation = db.query(database.Conversation).filter(database.Conversation.user_id == session_id).first()
        if db_conversation:
            session_data = db_conversation.history
            state = session_data.get("state", "GATHERING_INFO")
            history = session_data.get("conversation_history", [])
            offers = session_data.get("flight_offers", [])
            
            # 3. Cache the loaded session in Redis for next time
            try:
                redis_client.setex(session_id, SESSION_EXPIRATION, json.dumps(session_data))
            except redis.exceptions.RedisError as e:
                print(f"Error caching session to Redis after DB load: {e}")

            return state, history, offers
    finally:
        db.close()
        
    # 4. If not in DB either, return a new session.
    return "GATHERING_INFO", [], [] 