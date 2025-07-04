import pytest
from unittest.mock import patch, MagicMock
from app.main import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('app.main.save_session')
@patch('app.main.load_session')
@patch('app.main.get_ai_response')
def test_multi_turn_conversation(mock_get_ai_response, mock_load_session, mock_save_session, client):
    """
    Test a full, multi-turn conversation from initial query to final confirmation.
    """
    user_id = 'whatsapp:+15551234567'
    
    # --- Turn 1: User provides partial information ---
    
    # Mock the session manager to return an empty history for the first message
    mock_load_session.return_value = []
    
    # Mock the AI to ask a clarifying question and return the updated history
    clarifying_question = "That sounds like a great trip! How many people will be traveling?"
    history_after_turn1 = [
        {"role": "user", "content": "I want to fly from New York to London on August 15th"},
        {"role": "assistant", "content": clarifying_question}
    ]
    mock_get_ai_response.return_value = (clarifying_question, history_after_turn1)

    # Send the first message
    response1 = client.post('/webhook', data={'From': user_id, 'Body': 'I want to fly from New York to London on August 15th'})
    
    # Verify behavior for Turn 1
    mock_load_session.assert_called_once_with(user_id)
    mock_get_ai_response.assert_called_once_with("I want to fly from New York to London on August 15th", [])
    mock_save_session.assert_called_once_with(user_id, history_after_turn1)
    assert clarifying_question in response1.data.decode('utf-8')

    # --- Turn 2: User provides the final piece of information ---
    
    # Reset mocks for the second call
    mock_load_session.reset_mock()
    mock_get_ai_response.reset_mock()
    mock_save_session.reset_mock()

    # Mock the session manager to return the history from the first turn
    mock_load_session.return_value = history_after_turn1

    # Mock the AI to return the final JSON and the complete history
    final_details = {
        "origin": "New York", "destination": "London", "departure_date": "August 15th", "number_of_travelers": 2
    }
    history_after_turn2 = history_after_turn1 + [
        {"role": "user", "content": "Just 2 of us"},
        {"role": "assistant", "content": json.dumps(final_details)}
    ]
    mock_get_ai_response.return_value = (json.dumps(final_details), history_after_turn2)

    # Send the second message
    response2 = client.post('/webhook', data={'From': user_id, 'Body': 'Just 2 of us'})

    # Verify behavior for Turn 2
    mock_load_session.assert_called_once_with(user_id)
    mock_get_ai_response.assert_called_once_with("Just 2 of us", history_after_turn1)
    mock_save_session.assert_called_once_with(user_id, history_after_turn2)
    
    # Check for the final, formatted confirmation message
    confirmation_text = "Great! I have all the details."
    assert confirmation_text in response2.data.decode('utf-8')
    assert "New York" in response2.data.decode('utf-8')
    assert "2 people" in response2.data.decode('utf-8') 