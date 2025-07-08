import json
import os
import redis

# --- Redis Connection ---
# It's recommended to use a connection pool in a real application
redis_client = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
SESSION_EXPIRATION = 86400 # 24 hours in seconds

def save_session(session_id, state, conversation_history, flight_offers=None):
    """
    Saves the session data to Redis.
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

def load_session(session_id):
    """
    Loads session data from Redis.
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
        
    # 2. If not in Redis, return a new session.
    return "GATHERING_INFO", [], [] 