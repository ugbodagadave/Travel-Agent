
import pytest
from unittest.mock import patch, MagicMock
from app.new_session_manager import save_session, load_session

# This is an in-memory dictionary to simulate Redis for testing
mock_redis_store = {}

@pytest.fixture(autouse=True)
def mock_redis():
    """Mocks the redis client and its get/setex methods for all tests in this file."""
    global mock_redis_store
    mock_redis_store.clear()

    def mock_setex(key, ttl, value):
        mock_redis_store[key] = value

    def mock_get(key):
        return mock_redis_store.get(key)

    with patch('app.new_session_manager.redis_client') as mock_client:
        mock_client.setex.side_effect = mock_setex
        mock_client.get.side_effect = mock_get
        yield mock_client

def test_save_and_load_session_with_flight_details():
    """
    Tests that flight_details are correctly saved and loaded from the session.
    """
    session_id = "test_user_123"
    state = "AWAITING_CONFIRMATION"
    history = [{"role": "user", "content": "hi"}]
    offers = [{"id": "offer1"}]
    details = {"origin": "LHR", "destination": "JFK", "number_of_travelers": 2}

    # Save the session with flight details
    save_session(session_id, state, history, offers, details)

    # Load the session and verify all components are correct
    loaded_state, loaded_history, loaded_offers, loaded_details = load_session(session_id)

    assert loaded_state == state
    assert loaded_history == history
    assert loaded_offers == offers
    assert loaded_details == details

def test_load_new_session_returns_empty_details():
    """
    Tests that loading a non-existent session returns an empty flight_details dictionary.
    """
    # Attempt to load a session that hasn't been saved
    _, _, _, details = load_session("new_user_id")

    # Assert that the details are an empty dictionary
    assert details == {}

def test_save_session_without_details_or_offers():
    """
    Tests that saving a session with only state and history works correctly.
    """
    session_id = "test_user_456"
    state = "GATHERING_INFO"
    history = [{"role": "user", "content": "hello"}]

    # Save session with None for offers and details
    save_session(session_id, state, history, None, None)

    # Load and check the defaults
    _, _, loaded_offers, loaded_details = load_session(session_id)
    
    assert loaded_offers == []
    assert loaded_details == {} 