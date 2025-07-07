import pytest
from unittest.mock import patch, MagicMock

from app.new_session_manager import save_session, load_session
from app.database import Conversation

@pytest.fixture
def mock_db_session():
    """Mocks the database session to isolate tests from the actual database."""
    with patch('app.new_session_manager.SessionLocal') as mock_session_local:
        mock_db = MagicMock()
        # When a query is made, make it return a filterable object
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        # The result of the filter should be chainable to first()
        mock_query.filter.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        yield mock_db

def test_save_session(mock_db_session):
    """
    Tests that `save_session` correctly merges and commits a Conversation object.
    """
    user_id = "test_user_save"
    state = "BOOKING_COMPLETE"
    history = [("user", "thanks")]
    offers = ["offer3"]

    save_session(user_id, state, history, offers)
    
    # Check that a session was created and the database functions were called
    mock_db_session.merge.assert_called_once()
    mock_db_session.commit.assert_called_once()
    
    # Verify the object passed to merge has the correct data
    merged_object = mock_db_session.merge.call_args[0][0]
    assert isinstance(merged_object, Conversation)
    assert merged_object.user_id == user_id
    assert merged_object.history['state'] == state
    assert merged_object.history['conversation_history'] == [("user", "thanks")]
    assert merged_object.history['flight_offers'] == offers

def test_load_session_found(mock_db_session):
    """
    Tests that a session is correctly loaded from the database when it exists.
    """
    user_id = "test_user_found"
    session_data = {
        "state": "AWAITING_PAYMENT",
        "conversation_history": [["user", "book it"]],
        "flight_offers": ["offer2"]
    }
    
    # Configure the mock to return a conversation object
    mock_conversation = Conversation(user_id=user_id, history=session_data)
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_conversation

    state, history, offers = load_session(user_id)

    mock_db_session.query.assert_called_once_with(Conversation)
    assert state == "AWAITING_PAYMENT"
    assert history == [["user", "book it"]]
    assert offers == ["offer2"]

def test_load_session_not_found(mock_db_session):
    """
    Tests that a new, default session is returned when the user is not found in the database.
    """
    user_id = "test_user_not_found"
    
    # Configure the mock to simulate the user not being found
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    state, history, offers = load_session(user_id)

    mock_db_session.query.assert_called_once_with(Conversation)
    assert state == "GATHERING_INFO"
    assert history == []
    assert offers == [] 