import json
import os
import redis

# --- Redis Connection ---
# It's recommended to use a connection pool in a real application
redis_client = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
SESSION_EXPIRATION = 86400 # 24 hours in seconds
WALLET_ID_PREFIX = "wallet_id:"
WALLET_ID_EXPIRATION = 86400 # 24 hours

def save_wallet_mapping(wallet_id, user_id):
    """Saves the mapping from a Circle wallet ID to a user ID in Redis."""
    try:
        redis_client.setex(f"{WALLET_ID_PREFIX}{wallet_id}", WALLET_ID_EXPIRATION, user_id)
    except Exception as e:
        print(f"Error saving wallet mapping to Redis: {e}")

def load_user_id_from_wallet(wallet_id):
    """Loads a user ID from Redis using the Circle wallet ID."""
    try:
        return redis_client.get(f"{WALLET_ID_PREFIX}{wallet_id}")
    except Exception as e:
        print(f"Error loading user ID from wallet mapping in Redis: {e}")
        return None

def save_session(session_id, state, conversation_history, flight_offers=None, flight_details=None):
    """
    Saves the session data to Redis.
    """
    session_data = {
        "state": state,
        "conversation_history": conversation_history,
        "flight_offers": flight_offers or [],
        "flight_details": flight_details or {}
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
            details = session_data.get("flight_details", {})
            return state, history, offers, details
    except redis.exceptions.RedisError as e:
        print(f"Error loading session from Redis: {e}")
        
    # 2. If not in Redis, return a new session.
    return "GATHERING_INFO", [], [], {} 