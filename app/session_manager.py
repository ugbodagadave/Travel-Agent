import os
import redis
import json

def get_redis_client():
    """Initializes and returns a Redis client."""
    return redis.from_url(os.getenv("REDIS_URL"))

def load_session(user_id: str) -> list:
    """
    Loads the conversation history for a given user from Redis.
    Returns an empty list if no history is found.
    """
    try:
        redis_client = get_redis_client()
        session_data = redis_client.get(user_id)
        if session_data:
            return json.loads(session_data)
        return []
    except Exception as e:
        print(f"Error loading session for {user_id}: {e}")
        return []

def save_session(user_id: str, conversation_history: list):
    """
    Saves the conversation history for a given user to Redis.
    The session will expire after 24 hours of inactivity.
    """
    try:
        redis_client = get_redis_client()
        # Set the session data with a 24-hour expiration (86400 seconds)
        redis_client.set(user_id, json.dumps(conversation_history), ex=86400)
    except Exception as e:
        print(f"Error saving session for {user_id}: {e}") 