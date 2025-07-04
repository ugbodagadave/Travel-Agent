import os
import redis
import json
from .database import SessionLocal, Conversation, redis_client

def get_redis_client():
    """Initializes and returns a Redis client."""
    # The Render Redis URL for internal connections might not have a password
    redis_url = os.getenv("REDIS_URL")
    return redis.from_url(redis_url, decode_responses=True)

def load_session(user_id: str) -> (str, list):
    """
    Loads session (state and history) from Redis cache first.
    If it's a miss, assumes a new conversation.
    Returns the conversation state and history.
    """
    if redis_client:
        try:
            cached_session = redis_client.get(user_id)
            if cached_session:
                session_data = json.loads(cached_session)
                return session_data.get("state", "GATHERING_INFO"), session_data.get("history", [])
        except Exception as e:
            print(f"Error loading from Redis: {e}")

    # Default to a new conversation if nothing is found
    return "GATHERING_INFO", []

def save_session(user_id: str, state: str, conversation_history: list):
    """
    Saves the conversation state and history to Redis.
    """
    if redis_client:
        try:
            session_data = {
                "state": state,
                "history": conversation_history
            }
            redis_client.set(user_id, json.dumps(session_data), ex=86400)
        except Exception as e:
            print(f"Error saving session to Redis: {e}") 