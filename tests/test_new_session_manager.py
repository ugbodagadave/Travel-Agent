import pytest
import json
from unittest.mock import patch, MagicMock

from app.new_session_manager import save_session, load_session
from app.database import Conversation

@pytest.fixture
def mock_redis_client():
    with patch('app.new_session_manager.redis_client') as mock_redis:
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        yield mock_redis

@pytest.fixture
def mock_db_session():
    with patch('app.new_session_manager.SessionLocal') as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        yield mock_db

def test_load_session_cache_hit(mock_redis_client, mock_db_session):
    """
    Tests that the session is loaded from Redis cache if available.
    """
    user_id = "test_user_cache_hit"
    session_data = {
        "state": "FLIGHT_SELECTION",
        "conversation_history": [("user", "hello")],
        "flight_offers": ["offer1"]
    }
    mock_redis_client.get.return_value = json.dumps(session_data)

    state, history, offers = load_session(user_id)

    mock_redis_client.get.assert_called_once_with(user_id)
    mock_db_session.query.assert_not_called()
    assert state == "FLIGHT_SELECTION"
    assert history == [["user", "hello"]] # JSON dump converts tuples to lists
    assert offers == ["offer1"]

def test_load_session_cache_miss(mock_redis_client, mock_db_session):
    """
    Tests that the session is loaded from PostgreSQL on a cache miss and then cached in Redis.
    """
    user_id = "test_user_cache_miss"
    session_data = {
        "state": "AWAITING_PAYMENT",
        "conversation_history": [["user", "book it"]],
        "flight_offers": ["offer2"]
    }
    
    # Mock database result
    mock_conversation = Conversation(user_id=user_id, history=session_data)
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_conversation

    state, history, offers = load_session(user_id)

    mock_redis_client.get.assert_called_once_with(user_id)
    mock_db_session.query.assert_called_once()
    mock_redis_client.set.assert_called_once_with(user_id, json.dumps(session_data))
    assert state == "AWAITING_PAYMENT"
    assert history == [["user", "book it"]]
    assert offers == ["offer2"]

def test_load_session_not_found(mock_redis_client, mock_db_session):
    """
    Tests that a new session is returned when the user is not found in cache or DB.
    """
    user_id = "test_user_not_found"
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    state, history, offers = load_session(user_id)

    mock_redis_client.get.assert_called_once_with(user_id)
    mock_db_session.query.assert_called_once()
    mock_redis_client.set.assert_not_called()
    assert state == "GATHERING_INFO"
    assert history == []
    assert offers == []

def test_save_session(mock_redis_client, mock_db_session):
    """
    Tests that the session is saved to both Redis and PostgreSQL.
    """
    user_id = "test_user_save"
    state = "BOOKING_COMPLETE"
    conversation_history = [("user", "thanks")]
    flight_offers = ["offer3"]

    save_session(user_id, state, conversation_history, flight_offers)
    
    expected_data = {
        "state": state,
        "conversation_history": [["user", "thanks"]],
        "flight_offers": flight_offers
    }

    mock_redis_client.set.assert_called_once_with(user_id, json.dumps(expected_data))
    mock_db_session.merge.assert_called_once()
    mock_db_session.commit.assert_called_once() 