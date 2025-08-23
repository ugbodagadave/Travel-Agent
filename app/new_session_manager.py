import json
import os
import redis
import time

# --- Redis Connection ---
# It's recommended to use a connection pool in a real application
redis_client = None

def get_redis_client():
    """Initializes and returns the Redis client."""
    global redis_client
    if redis_client is None and os.environ.get("REDIS_URL"):
        try:
            redis_url = os.environ.get("REDIS_URL")
            print(f"[Redis] Attempting to connect to Redis URL: {redis_url[:20]}...")
            redis_client = redis.from_url(redis_url, decode_responses=True)
            redis_client.ping()
            print(f"[Redis] Successfully connected to Redis")
        except redis.exceptions.ConnectionError as e:
            print(f"[Redis] Error connecting to Redis: {e}")
            redis_client = None
        except Exception as e:
            print(f"[Redis] Unexpected error connecting to Redis: {e}")
            redis_client = None
    else:
        if not os.environ.get("REDIS_URL"):
            print(f"[Redis] REDIS_URL environment variable not set")
        else:
            print(f"[Redis] Redis client already initialized")
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

# --- Circle Layer Payment Tracking ---

def save_circlelayer_payment_info(user_id: str, address: str, initial_balance: int, expected_amount: int, address_index: int, ttl_seconds: int = 3600):
    """Save Circle Layer payment tracking information to prevent false confirmations.
    
    Args:
        user_id: User identifier
        address: Deposit address
        initial_balance: Balance before payment request (in wei)
        expected_amount: Expected payment amount (in wei)
        address_index: Address derivation index
        ttl_seconds: Time to live for the tracking data
    """
    client = get_redis_client()
    if not client:
        print("Error: Redis client not available for Circle Layer payment tracking.")
        return
    try:
        payment_key = f"circlelayer_payment:{user_id}"
        payment_data = {
            "address": address.lower(),
            "initial_balance": str(initial_balance),
            "expected_amount": str(expected_amount),
            "address_index": str(address_index),
            "created_at": str(int(time.time()))
        }
        client.hset(payment_key, mapping=payment_data)
        client.expire(payment_key, ttl_seconds)
        print(f"[CircleLayer] Saved payment tracking for {user_id} at {address} (index {address_index})")
    except redis.exceptions.RedisError as e:
        print(f"Error saving Circle Layer payment tracking to Redis: {e}")

def get_circlelayer_payment_info(user_id: str) -> dict:
    """Get Circle Layer payment tracking information.
    
    Returns:
        Dictionary with payment tracking data or None if not found
    """
    client = get_redis_client()
    if not client:
        print("Error: Redis client not available for Circle Layer payment lookup.")
        return None
    try:
        payment_key = f"circlelayer_payment:{user_id}"
        payment_data = client.hgetall(payment_key)
        if not payment_data:
            return None
        
        return {
            "address": payment_data.get("address"),
            "initial_balance": int(payment_data.get("initial_balance", "0")),
            "expected_amount": int(payment_data.get("expected_amount", "0")),
            "address_index": int(payment_data.get("address_index", "0")),
            "created_at": int(payment_data.get("created_at", "0"))
        }
    except redis.exceptions.RedisError as e:
        print(f"Error retrieving Circle Layer payment tracking from Redis: {e}")
        return None

def clear_circlelayer_payment_info(user_id: str):
    """Clear Circle Layer payment tracking information after successful payment."""
    client = get_redis_client()
    if not client:
        print("Error: Redis client not available for Circle Layer payment cleanup.")
        return
    try:
        payment_key = f"circlelayer_payment:{user_id}"
        client.delete(payment_key)
        print(f"[CircleLayer] Cleared payment tracking for {user_id}")
    except redis.exceptions.RedisError as e:
        print(f"Error clearing Circle Layer payment tracking from Redis: {e}")

def get_next_address_index() -> int:
    """Get the next available address index for Circle Layer payments.
    
    Returns:
        Next available index for address derivation
    """
    client = get_redis_client()
    if not client:
        print("Error: Redis client not available for address index tracking.")
        return 0
    try:
        index_key = "circlelayer_address_index"
        current_index = client.get(index_key)
        if current_index is None:
            next_index = 0
        else:
            next_index = int(current_index) + 1
        
        # Update the index (no expiration - persistent counter)
        client.set(index_key, str(next_index))
        return next_index
    except redis.exceptions.RedisError as e:
        print(f"Error managing Circle Layer address index: {e}")
        return 0 