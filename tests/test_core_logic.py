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

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("app.core_logic.extract_flight_details_from_history")
def test_process_message_awaiting_confirmation_yes(mock_extract_details, mock_save_session, mock_load_session, mock_amadeus_service):
    """
    Tests the AWAITING_CONFIRMATION state when the user says 'yes'.
    """
    mock_load_session.return_value = ("AWAITING_CONFIRMATION", ["history"], [])
    mock_extract_details.return_value = {
        'origin': 'London',
        'destination': 'Paris',
        'departure_date': '2024-09-15',
        'number_of_travelers': '1'
    }
    
    response = process_message("test_user", "yes", mock_amadeus_service)
    
    assert len(response) == 2
    assert response[0] == "Okay, let me get the best flight options for you."
    assert "Flight to CDG" in response[1]
    
    mock_load_session.assert_called_once_with("test_user")
    mock_extract_details.assert_called_once_with(["history"])
    mock_amadeus_service.search_flights.assert_called_once()
    mock_save_session.assert_called_with("test_user", "FLIGHT_SELECTION", ["history"], mock_amadeus_service.search_flights.return_value)

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("app.core_logic.extract_flight_details_from_history")
def test_process_message_awaiting_confirmation_no_flights_found(mock_extract_details, mock_save_session, mock_load_session, mock_amadeus_service):
    """
    Tests the AWAITING_CONFIRMATION state when no flights are found.
    """
    # Configure the mock Amadeus service to return no flights
    mock_amadeus_service.search_flights.return_value = []
    
    mock_load_session.return_value = ("AWAITING_CONFIRMATION", ["history"], [])
    mock_extract_details.return_value = {
        'origin': 'London',
        'destination': 'Mars',
        'departure_date': '2024-09-15',
        'number_of_travelers': '1'
    }
    
    response = process_message("test_user", "yes", mock_amadeus_service)
    
    # The first message is the acknowledgment
    assert response[0] == "Okay, let me get the best flight options for you."
    # The second message should be the "no flights found" message
    assert "Sorry, I couldn't find any flights" in response[1]
    
    mock_load_session.assert_called_once_with("test_user")
    mock_amadeus_service.search_flights.assert_called_once()
    # Check that the state is reset to GATHERING_INFO
    mock_save_session.assert_called_with("test_user", "GATHERING_INFO", ["history"], []) 