import pytest
from unittest.mock import patch, MagicMock
from app.main import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# We now also need to patch the new timezone service and AmadeusService
@patch('app.main.AmadeusService')
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
    mock_get_timezone,
    mock_amadeus_service, # Add the new mock
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

    # --- Turn 2: User provides final info, AI asks for confirmation ---
    
    mock_load_session.reset_mock()
    mock_get_ai_response.reset_mock()
    mock_save_session.reset_mock()

    mock_load_session.return_value = history_after_turn1

    # This is the AI's confirmation message + JSON blob
    confirmation_and_slots = (
        'I have you flying from New York to London on August 15th for 2 people. Is that correct?\n'
        '{"origin": "New York", "destination": "London", "departure_date": "2024-08-15", "number_of_travelers": 2}'
    )
    history_after_confirmation = history_after_turn1 + [
        {"role": "user", "content": "Just 2 of us"},
        {"role": "assistant", "content": confirmation_and_slots}
    ]
    mock_get_ai_response.return_value = (confirmation_and_slots, history_after_confirmation)
    
    response2 = client.post('/webhook', data={'From': user_id, 'Body': 'Just 2 of us'})
    # The app should just relay the AI's confirmation question
    assert "Is that correct?" in response2.data.decode('utf-8')
    assert '{"origin":' in response2.data.decode('utf-8') # Check that the JSON is there

    # --- Turn 3: User confirms, triggering flight search ---

    mock_load_session.reset_mock()
    mock_get_ai_response.reset_mock()
    mock_save_session.reset_mock()
    
    mock_load_session.return_value = history_after_confirmation
    
    # The AI now returns the "complete" status
    final_status_json = '{"status": "complete"}'
    history_after_completion = history_after_confirmation + [
        {"role": "user", "content": "Yes"},
        {"role": "assistant", "content": final_status_json}
    ]
    mock_get_ai_response.return_value = (final_status_json, history_after_completion)

    # Configure the mock Amadeus instance that the app will create
    mock_instance = mock_amadeus_service.return_value
    mock_instance.get_iata_code.side_effect = ['JFK', 'LHR']
    mock_instance.search_flights.return_value = [
        {
            'price': {'total': '350.00', 'currency': 'USD'},
            'itineraries': [{
                'duration': 'PT8H30M',
                'segments': [{'departure': {'at': '2024-08-15T09:00:00'}, 'arrival': {'at': '2024-08-15T21:30:00'}}]
            }]
        }
    ]

    response3 = client.post('/webhook', data={'From': user_id, 'Body': 'Yes'})

    # Assert that the Amadeus service was called correctly
    mock_instance.get_iata_code.assert_any_call("New York")
    mock_instance.get_iata_code.assert_any_call("London")
    mock_instance.search_flights.assert_called_once_with(
        origin_iata='JFK',
        destination_iata='LHR',
        departure_date='2024-08-15',
        return_date=None,
        adults=2
    )

    # Check for the formatted flight offer message
    assert "I found a few options for you:" in response3.data.decode('utf-8')
    assert "Depart at 2024-08-15T09:00:00" in response3.data.decode('utf-8')
    assert "Price: 350.00 USD" in response3.data.decode('utf-8')
    assert "Please reply with the number of the flight" in response3.data.decode('utf-8') 