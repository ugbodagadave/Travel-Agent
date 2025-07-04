import pytest
from unittest.mock import patch, MagicMock
from app.main import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# We now need to patch the database session as well
@patch('app.session_manager.SessionLocal')
@patch('app.main.save_session')
@patch('app.main.load_session')
@patch('app.main.get_ai_response')
def test_multi_turn_conversation(
    mock_get_ai_response, 
    mock_load_session, 
    mock_save_session, 
    mock_db_session, # Add the new mock to the function signature
    client
):
    """
    Test a full, multi-turn conversation. The core logic remains the same,
    but we ensure the database is mocked out.
    """
    # This test doesn't need to interact with the DB mock directly,
    # as we are mocking the higher-level load/save session functions.
    # We just need to ensure the mock is in place to prevent real DB calls.
    
    user_id = 'whatsapp:+15551234567'
    
    # --- Turn 1: User provides partial information ---
    
    mock_load_session.return_value = []
    
    clarifying_question = "That sounds like a great trip! How many people will be traveling?"
    history_after_turn1 = [
        {"role": "user", "content": "I want to fly from New York to London on August 15th"},
        {"role": "assistant", "content": clarifying_question}
    ]
    mock_get_ai_response.return_value = (clarifying_question, history_after_turn1)

    response1 = client.post('/webhook', data={'From': user_id, 'Body': 'I want to fly from New York to London on August 15th'})
    
    mock_load_session.assert_called_once_with(user_id)
    mock_get_ai_response.assert_called_once_with("I want to fly from New York to London on August 15th", [])
    mock_save_session.assert_called_once_with(user_id, history_after_turn1)
    assert clarifying_question in response1.data.decode('utf-8')

    # --- Turn 2: User provides the final piece of information ---
    
    mock_load_session.reset_mock()
    mock_get_ai_response.reset_mock()
    mock_save_session.reset_mock()

    mock_load_session.return_value = history_after_turn1

    final_details = {
        "origin": "New York", "destination": "London", "departure_date": "August 15th", "number_of_travelers": 2
    }
    history_after_turn2 = history_after_turn1 + [
        {"role": "user", "content": "Just 2 of us"},
        {"role": "assistant", "content": json.dumps(final_details)}
    ]
    mock_get_ai_response.return_value = (json.dumps(final_details), history_after_turn2)

    response2 = client.post('/webhook', data={'From': user_id, 'Body': 'Just 2 of us'})

    mock_load_session.assert_called_once_with(user_id)
    mock_get_ai_response.assert_called_once_with("Just 2 of us", history_after_turn1)
    mock_save_session.assert_called_once_with(user_id, history_after_turn2)
    
    confirmation_text = "Great! I have all the details."
    assert confirmation_text in response2.data.decode('utf-8')
    assert "New York" in response2.data.decode('utf-8')
    assert "2 people" in response2.data.decode('utf-8') 