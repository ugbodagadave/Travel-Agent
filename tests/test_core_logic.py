import pytest
from unittest.mock import MagicMock, patch
from app.core_logic import process_message

@pytest.fixture
def mock_amadeus_service():
    """Fixture for a mocked AmadeusService."""
    service = MagicMock()
    service.get_iata_code.return_value = "LHR"
    service.search_flights.return_value = [{"itineraries": [{"segments": [{"arrival": {"iataCode": "CDG"}}]}], "price": {"total": "250.00", "currency": "EUR"}}]
    return service

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("app.core_logic.get_ai_response")
def test_process_message_gathering_info(mock_get_ai, mock_save_session, mock_load_session, mock_amadeus_service):
    """
    Tests the GATHERING_INFO state in process_message.
    """
    mock_load_session.return_value = ("GATHERING_INFO", [], [])
    mock_get_ai.return_value = ("Hello! How can I help you?", ["user: hi", "ai: Hello! How can I help you?"])
    
    response = process_message("test_user", "hi", mock_amadeus_service)
    
    assert response == ["Hello! How can I help you?"]
    mock_load_session.assert_called_once_with("test_user")
    mock_get_ai.assert_called_once()
    mock_save_session.assert_called_once()

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("app.core_logic.get_ai_response")
def test_process_message_info_complete(mock_get_ai, mock_save_session, mock_load_session, mock_amadeus_service):
    """
    Tests the transition from GATHERING_INFO to AWAITING_CONFIRMATION.
    """
    mock_load_session.return_value = ("GATHERING_INFO", [], [])
    ai_response_text = "I have your flight to London. [INFO_COMPLETE]"
    mock_get_ai.return_value = (ai_response_text, ["history"])

    response = process_message("test_user", "I want to fly to London", mock_amadeus_service)

    assert "Is this information correct?" in response[0]
    # Check that save_session was called with the new state
    mock_save_session.assert_called_with("test_user", "AWAITING_CONFIRMATION", ["history"], [])

@patch("app.core_logic.search_flights_task.delay")
@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("app.core_logic.extract_flight_details_from_history")
def test_process_message_awaiting_confirmation_triggers_task(mock_extract_details, mock_save_session, mock_load_session, mock_search_task):
    """
    Tests that the AWAITING_CONFIRMATION state correctly triggers the Celery task.
    """
    user_id = "test_user"
    mock_load_session.return_value = ("AWAITING_CONFIRMATION", ["history"], [])
    flight_details = {
        'origin': 'London',
        'destination': 'Paris',
        'departure_date': '2024-09-15',
        'number_of_travelers': '1'
    }
    mock_extract_details.return_value = flight_details
    
    response = process_message(user_id, "yes", MagicMock())
    
    # Check for immediate user feedback
    assert response[0] == "Okay, I'm searching for the best flights for you. This might take a moment..."
    
    # Check that the task was called
    mock_search_task.assert_called_once_with(user_id, flight_details)
    
    # Check that the state was updated to SEARCH_IN_PROGRESS
    mock_save_session.assert_called_with(user_id, "SEARCH_IN_PROGRESS", ["history"], [])

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
def test_process_message_search_in_progress(mock_save_session, mock_load_session):
    """
    Tests that the agent gives a waiting message if the user messages
    during the SEARCH_IN_PROGRESS state.
    """
    user_id = "test_user_searching"
    mock_load_session.return_value = ("SEARCH_IN_PROGRESS", ["history"], [])

    response = process_message(user_id, "are you done yet?", MagicMock())

    assert len(response) == 1
    assert "I'm still looking for flights" in response[0]
    mock_save_session.assert_called_once() 