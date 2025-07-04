import pytest
from unittest.mock import patch, MagicMock
from app.main import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# We now also need to patch the new timezone service
@patch('app.main.get_timezone_for_city')
@patch('app.session_manager.SessionLocal')
@patch('app.main.save_session')
@patch('app.main.load_session')
@patch('app.main.get_ai_response')
def test_multi_turn_conversation_with_timezone(
    mock_get_ai_response, 
    mock_load_session, 
    mock_save_session, 
    mock_db_session,
    mock_get_timezone, # Add the new mock
    client
):
    """
    Test a full, multi-turn conversation including the final timezone lookup.
    """
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

    # --- Turn 2: User provides final info, triggering timezone lookup ---
    
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
    
    # Mock the timezone service to return a specific timezone
    mock_get_timezone.return_value = "America/New_York"

    response2 = client.post('/webhook', data={'From': user_id, 'Body': 'Just 2 of us'})

    # Assert that the timezone service was called correctly
    mock_get_timezone.assert_called_once_with("New York")

    # Check for the final, formatted confirmation message including the timezone
    confirmation_text = "Great! I have all the details."
    assert confirmation_text in response2.data.decode('utf-8')
    assert "New York" in response2.data.decode('utf-8')
    assert "(Timezone detected: America/New_York)" in response2.data.decode('utf-8') 