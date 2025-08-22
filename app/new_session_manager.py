import json
import os
import redis

# --- Redis Connection ---
# It's recommended to use a connection pool in a real application
redis_client = None

def get_redis_client():
    """Initializes and returns the Redis client."""
    global redis_client
    if redis_client is None and os.environ.get("REDIS_URL"):
        try:
            redis_client = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)
            redis_client.ping()
        except redis.exceptions.ConnectionError as e:
            print(f"Error connecting to Redis: {e}")
            redis_client = None
    return redis_client

SESSION_EXPIRATION = 86400 # 24 hours in seconds
WALLET_ID_PREFIX = "wallet_id:"
WALLET_ID_EXPIRATION = 86400 # 24 hours

EVM_MAPPING_PREFIX = "evm_mapping:"

def save_wallet_mapping(payment_intent_id, user_id):
    """Saves a mapping from payment_intent_id to user_id."""
    client = get_redis_client()
    if not client:
        print("Error: Redis client not available for wallet mapping.")
        return
    try:
        # Set with a 24-hour expiry
        client.set(f"wallet_mapping:{payment_intent_id}", user_id, ex=86400)
    except redis.exceptions.RedisError as e:
        print(f"Error saving wallet mapping to Redis: {e}")

def load_user_id_from_wallet(wallet_id):
    """Loads a user ID from Redis using the Circle wallet ID."""
    try:
        return redis_client.get(f"{WALLET_ID_PREFIX}{wallet_id}")
    except Exception as e:
        print(f"Error loading user ID from wallet mapping in Redis: {e}")
        return None

def save_session(user_id, state, conversation_history, flight_offers, flight_details):
    """Saves the user's session to Redis."""
    client = get_redis_client()
    if not client:
        print("Error: Redis client not available for saving session.")
        return
    try:
        session_data = {
            "state": json.dumps(state),
            "conversation_history": json.dumps(conversation_history),
            "flight_offers": json.dumps(flight_offers),
            "flight_details": json.dumps(flight_details)
        }
        client.hset(f"session:{user_id}", mapping=session_data)
    except redis.exceptions.RedisError as e:
        print(f"Error saving session to Redis: {e}")

def load_session(user_id):
    """Loads the user's session from Redis."""
    client = get_redis_client()
    if not client:
        # Return a default session if Redis is not available
        return "GATHERING_INFO", [], [], {}
    try:
        session_data = client.hgetall(f"session:{user_id}")
        if not session_data:
            return "GATHERING_INFO", [], [], {}
        state = json.loads(session_data.get("state", '"GATHERING_INFO"'))
        history = json.loads(session_data.get("conversation_history", "[]"))
        offers = json.loads(session_data.get("flight_offers", "[]"))
        details = json.loads(session_data.get("flight_details", "{}"))
        return state, history, offers, details
    except redis.exceptions.RedisError as e:
        print(f"Error loading session from Redis: {e}")
        return "GATHERING_INFO", [], [], {}

def get_user_id_from_wallet(payment_intent_id):
    """Retrieves a user_id from a payment_intent_id mapping."""
    client = get_redis_client()
    if not client:
        print("Error: Redis client not available for wallet lookup.")
        return None
    try:
        return client.get(f"wallet_mapping:{payment_intent_id}")
    except redis.exceptions.RedisError as e:
        print(f"Error retrieving wallet mapping from Redis: {e}")
        return None

# --- Circle Layer EVM helpers ---

def save_evm_mapping(address: str, user_id: str, ttl_seconds: int = 86400):
    client = get_redis_client()
    if not client:
        print("Error: Redis client not available for EVM mapping.")
        return
    try:
        client.set(f"{EVM_MAPPING_PREFIX}{address.lower()}", user_id, ex=ttl_seconds)
    except redis.exceptions.RedisError as e:
        print(f"Error saving EVM mapping to Redis: {e}")

def get_user_id_from_evm_address(address: str) -> str:
    client = get_redis_client()
    if not client:
        print("Error: Redis client not available for EVM lookup.")
        return None
    try:
        return client.get(f"{EVM_MAPPING_PREFIX}{address.lower()}")
    except redis.exceptions.RedisError as e:
        print(f"Error retrieving EVM mapping from Redis: {e}")
        return None 