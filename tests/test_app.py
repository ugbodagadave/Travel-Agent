import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from app.main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('app.main.amadeus_service')
@patch('app.main.extract_flight_details_from_history')
@patch('app.main.save_session')
@patch('app.main.load_session')
@patch('app.main.get_ai_response')
def test_state_machine_flow(
    mock_get_ai_response,
    mock_load_session,
    mock_save_session,
    mock_extract_details,
    mock_amadeus_service_instance,
    client
):
    """
    Test the full state machine flow from gathering info to flight search.
    """
    user_id = 'whatsapp:+15559998888'

    # --- Turn 1: GATHERING_INFO state ---
    # Simulate a new session
    mock_load_session.return_value = ("GATHERING_INFO", [])
    
    # AI asks a clarifying question
    ai_response_1 = "How many people are traveling?"
    history_1 = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": ai_response_1}]
    mock_get_ai_response.return_value = (ai_response_1, history_1)

    response1 = client.post('/webhook', data={'From': user_id, 'Body': 'Hi'})
    
    assert response1.status_code == 200
    # Check that we saved the new state and history
    mock_save_session.assert_called_with(user_id, "GATHERING_INFO", history_1)

    # --- Turn 2: User provides final info, AI confirms ---
    # The session now contains the history from turn 1
    mock_load_session.return_value = ("GATHERING_INFO", history_1)
    
    # AI confirms and signals completion
    ai_response_2 = "Got it. Flying from NYC to LON for 2 people. Is this correct? [INFO_COMPLETE]"
    history_2 = history_1 + [{"role": "user", "content": "2 people from NYC to LON"}, {"role": "assistant", "content": ai_response_2}]
    mock_get_ai_response.return_value = (ai_response_2, history_2)
    
    response2 = client.post('/webhook', data={'From': user_id, 'Body': '2 people from NYC to LON'})
    
    assert response2.status_code == 200
    # The state should have transitioned to AWAITING_CONFIRMATION
    mock_save_session.assert_called_with(user_id, "AWAITING_CONFIRMATION", history_2)
    assert "Is this correct?" in str(response2.data) # Check the user sees the confirmation question

    # --- Turn 3: User confirms, triggers flight search ---
    # The session is now awaiting confirmation
    mock_load_session.return_value = ("AWAITING_CONFIRMATION", history_2)
    
    # Mock the extracted flight details
    flight_details = {
        'origin': 'NYC', 'destination': 'LON', 'departure_date': '2024-12-25', 
        'return_date': None, 'number_of_travelers': "2"
    }
    mock_extract_details.return_value = flight_details
    
    # Configure the patched amadeus_service instance directly
    mock_amadeus_service_instance.get_iata_code.side_effect = ['JFK', 'LHR']
    mock_amadeus_service_instance.search_flights.return_value = [{'price': {'total': '500', 'currency': 'USD'}, 'itineraries': [{'segments': [{'arrival': {'iataCode': 'LHR'}}]}]}]
    
    response3 = client.post('/webhook', data={'From': user_id, 'Body': 'Yes, that is correct'})

    assert response3.status_code == 200
    mock_extract_details.assert_called_with(history_2)
    mock_amadeus_service_instance.search_flights.assert_called_once()
    # Check that the final state is FLIGHT_SELECTION
    mock_save_session.assert_called_with(user_id, "FLIGHT_SELECTION", history_2)
    assert "I found a few options for you" in str(response3.data) 