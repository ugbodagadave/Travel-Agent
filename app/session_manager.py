import os
import redis
import json
from .database import SessionLocal, Conversation

def get_redis_client():
    """Initializes and returns a Redis client."""
    # The Render Redis URL for internal connections might not have a password
    redis_url = os.getenv("REDIS_URL")
    return redis.from_url(redis_url, decode_responses=True)

def load_session(user_id: str) -> list:
    """
    Loads session from Redis cache first. If it's a miss, loads from
    PostgreSQL DB and caches the result in Redis.
    """
    try:
        # Try to load from Redis cache
        redis_client = get_redis_client()
        cached_session = redis_client.get(user_id)
        if cached_session:
            return json.loads(cached_session)
    except Exception as e:
        print(f"Error loading from Redis: {e}")

    # If cache miss, load from PostgreSQL
    db = SessionLocal()
    try:
        db_conversation = db.query(Conversation).filter(Conversation.user_id == user_id).first()
        if db_conversation and db_conversation.history:
            # Cache the result in Redis for next time
            try:
                redis_client.set(user_id, json.dumps(db_conversation.history), ex=86400)
            except Exception as e:
                print(f"Error saving to Redis after DB read: {e}")
            return db_conversation.history
        return []
    finally:
        db.close()

def save_session(user_id: str, conversation_history: list):
    """
    Saves the conversation history to both PostgreSQL for persistence
    and Redis for caching.
    """
    # Save to PostgreSQL
    db = SessionLocal()
    try:
        db_conversation = db.query(Conversation).filter(Conversation.user_id == user_id).first()
        if db_conversation:
            db_conversation.history = conversation_history
        else:
            db_conversation = Conversation(user_id=user_id, history=conversation_history)
            db.add(db_conversation)
        db.commit()
    finally:
        db.close()

    # Save to Redis cache
    try:
        redis_client = get_redis_client()
        redis_client.set(user_id, json.dumps(conversation_history), ex=86400)
    except Exception as e:
        print(f"Error saving session to Redis: {e}") 