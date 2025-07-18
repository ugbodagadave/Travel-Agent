
import pytest
from unittest.mock import patch, MagicMock
from redis import StrictRedis
import json
from app.new_session_manager import save_session, load_session, save_wallet_mapping, get_user_id_from_wallet

@pytest.fixture
def mock_redis_client():
    """Fixture to mock the Redis client and use an in-memory store."""
    session_store = {}
    with patch('app.new_session_manager.get_redis_client') as mock_get_redis_client:
        mock_client = MagicMock(spec=StrictRedis)

        def hgetall(key):
            return session_store.get(key, {})

        def hset(key, mapping):
            if key not in session_store:
                session_store[key] = {}
            session_store[key].update(mapping)
            return True

        def get(key):
            return session_store.get(key)

        def set(key, value, ex=None):
            session_store[key] = value
            return True

        mock_client.hgetall.side_effect = hgetall
        mock_client.hset.side_effect = hset
        mock_client.get.side_effect = get
        mock_client.set.side_effect = set
        
        mock_get_redis_client.return_value = mock_client
        yield mock_client

def test_save_and_load_session(mock_redis_client):
    """Tests basic session saving and loading."""
    user_id = "test_user_1"
    state = "FLIGHT_SELECTION"
    history = [{"role": "user", "content": "hello"}]
    offers = [{"id": "flight1"}]
    details = {"origin": "LHR"}

    save_session(user_id, state, history, offers, details)
    loaded_state, loaded_history, loaded_offers, loaded_details = load_session(user_id)

    assert loaded_state == state
    assert loaded_history == history
    assert loaded_offers == offers
    assert loaded_details == details

def test_load_new_session(mock_redis_client):
    """Tests loading a session for a new user."""
    state, history, offers, details = load_session("new_user_2")
    assert state == "GATHERING_INFO"
    assert history == []
    assert offers == []
    assert details == {}

def test_wallet_mapping(mock_redis_client):
    """Tests saving and retrieving a wallet mapping."""
    payment_intent_id = "pi_123"
    user_id = "user_abc"
    save_wallet_mapping(payment_intent_id, user_id)
    retrieved_user_id = get_user_id_from_wallet(payment_intent_id)
    assert retrieved_user_id == user_id 