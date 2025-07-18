
import pytest
from unittest.mock import patch, MagicMock
from app.tasks import search_flights_task
from app.new_session_manager import save_session
import time

@pytest.fixture
def mock_amadeus_fixture():
    """Fixture for a mocked AmadeusService."""
    service = MagicMock()
    service.get_iata_code.side_effect = lambda city: "LHR" if city == "London" else "CDG"
    service.get_airport_name.side_effect = lambda code: "London Heathrow" if code == "LHR" else "Charles de Gaulle"
    service.get_airline_name.return_value = "Test Airline"
    service.search_flights.return_value = [
        {
            "itineraries": [
                {
                    "duration": "PT2H30M",
                    "segments": [
                        {
                            "carrierCode": "TA",
                            "departure": {"iataCode": "LHR", "at": "2024-10-26T10:00:00"},
                            "arrival": {"iataCode": "CDG"}
                        }
                    ]
                }
            ],
            "price": {"total": "250.00", "currency": "EUR"}
        }
    ]
    return service

@pytest.fixture
def mock_user_id():
    return "telegram:12345"

@patch("app.tasks.AmadeusService")
@patch("app.tasks.load_session")
@patch("app.tasks.save_session")
@patch("app.tasks.twilio_client")
@patch("app.tasks.send_message")
def test_search_flights_task_flights_found_telegram(mock_send_telegram, mock_twilio, mock_save_session, mock_load_session, MockAmadeusService, mock_amadeus_fixture):
    """
    Tests the search_flights_task when flights are found for a Telegram user.
    """
    MockAmadeusService.return_value = mock_amadeus_fixture
    user_id = "telegram:123456"
    flight_details = {'origin': 'London', 'destination': 'Paris', 'departure_date': '2024-10-26', 'number_of_travelers': '1'}
    mock_load_session.return_value = ("SEARCH_IN_PROGRESS", ["history"], [], {})
    
    # Run the task
    search_flights_task(user_id, flight_details)
    
    # Verify behavior
    mock_load_session.assert_called_once_with(user_id)
    mock_amadeus_fixture.search_flights.assert_called_once()
    
    # Check that the correct message was sent
    mock_send_telegram.assert_called_once()
    # Get the arguments passed to send_message
    call_args = mock_send_telegram.call_args[0]
    assert call_args[0] == "123456" # chat_id
    assert "I found a few options for you" in call_args[1]
    assert "Test Airline" in call_args[1]
    mock_twilio.messages.create.assert_not_called()

    # Check that the session was updated correctly
    mock_save_session.assert_called_once()
    save_args = mock_save_session.call_args[0]
    assert save_args[0] == user_id
    assert save_args[1] == "FLIGHT_SELECTION"
    assert save_args[3] is not None # offers
    assert save_args[4] == flight_details

@patch("app.tasks.AmadeusService")
@patch("app.tasks.load_session")
@patch("app.tasks.save_session")
@patch("app.tasks.twilio_client")
@patch("app.tasks.send_message")
def test_search_flights_task_no_flights_whatsapp(mock_send_telegram, mock_twilio, mock_save_session, mock_load_session, MockAmadeusService, mock_amadeus_fixture):
    """
    Tests the search_flights_task when NO flights are found for a WhatsApp user.
    """
    # Make the mock return no flights for this test
    mock_amadeus_fixture.search_flights.return_value = []
    MockAmadeusService.return_value = mock_amadeus_fixture
    
    user_id = "whatsapp:+15551234567"
    flight_details = {'origin': 'London', 'destination': 'Mars', 'departure_date': '2024-10-26', 'number_of_travelers': '1'}
    mock_load_session.return_value = ("SEARCH_IN_PROGRESS", ["history"], [], {})
    
    # Run the task
    search_flights_task(user_id, flight_details)
    
    # Verify behavior
    mock_load_session.assert_called_once_with(user_id)
    mock_amadeus_fixture.search_flights.assert_called_once()
    
    # Check that the correct message was sent
    mock_twilio.messages.create.assert_called_once()
    call_kwargs = mock_twilio.messages.create.call_args[1]
    assert call_kwargs['to'] == user_id
    assert "Sorry, I couldn't find any flights" in call_kwargs['body']
    mock_send_telegram.assert_not_called()

    # Check that the session was updated correctly
    mock_save_session.assert_called_once()
    save_args = mock_save_session.call_args[0]
    assert save_args[0] == user_id
    assert save_args[1] == "GATHERING_INFO"
    assert save_args[3] == [] # No offers
    assert save_args[4] == flight_details

def test_search_flights_task_catastrophic_failure(mocker, mock_user_id):
    """
    Test that the task handles a critical failure gracefully (e.g., Amadeus outage),
    sends an error message, and resets the state.
    """
    # Mock dependencies
    mocker.patch('app.tasks.load_session', return_value=("SEARCH_IN_PROGRESS", [], [], {}))
    mocker.patch('app.tasks.AmadeusService.get_iata_code', side_effect=Exception("Major API Outage"))
    mock_send_message = mocker.patch('app.tasks.send_message')
    mock_save_session = mocker.patch('app.tasks.save_session')

    flight_details = {'origin': 'London', 'destination': 'Paris', 'departure_date': '2025-12-01'}

    # Run the task
    search_flights_task(mock_user_id, flight_details)

    # Assert that a user-friendly error message was sent
    mock_send_message.assert_called_with('12345', "I'm sorry, but I encountered an unexpected error while searching for flights. Please try again in a moment.")
    
    # Assert that the session was reset to GATHERING_INFO
    mock_save_session.assert_called_with(mock_user_id, "GATHERING_INFO", [], [], flight_details)

@patch("app.tasks.AmadeusService")
@patch("app.tasks.load_session")
@patch("app.tasks.save_session")
@patch("app.tasks.send_message")
def test_search_flights_task_attaches_traveler_name(mock_send_telegram, mock_save_session, mock_load_session, MockAmadeusService, mock_amadeus_fixture):
    """
    Tests that the traveler's name is correctly attached to the flight offers.
    """
    MockAmadeusService.return_value = mock_amadeus_fixture
    user_id = "telegram:123456"
    flight_details = {
        'origin': 'London', 
        'destination': 'Paris', 
        'departure_date': '2024-10-26', 
        'number_of_travelers': '1',
        'traveler_name': 'David Ugbodaga'  # The name to be attached
    }
    mock_load_session.return_value = ("SEARCH_IN_PROGRESS", ["history"], [], {})
    
    # Run the task
    search_flights_task(user_id, flight_details)
    
    # Check that the session was updated correctly
    mock_save_session.assert_called_once()
    save_args = mock_save_session.call_args[0]
    
    # The flight offers are the 4th argument to save_session
    saved_offers = save_args[3]
    
    # Assert that the traveler_name is present in the saved offers
    assert len(saved_offers) > 0
    assert saved_offers[0].get('traveler_name') == 'David Ugbodaga'

@patch("app.tasks.AmadeusService")
@patch("app.tasks.load_session")
@patch("app.tasks.save_session")
@patch("app.tasks.send_message")
def test_search_flights_task_uses_travel_class(mock_send_telegram, mock_save_session, mock_load_session, MockAmadeusService, mock_amadeus_fixture):
    """
    Tests that the search_flights_task correctly uses the travel_class parameter.
    """
    MockAmadeusService.return_value = mock_amadeus_fixture
    user_id = "telegram:789012"
    flight_details = {
        'origin': 'London', 
        'destination': 'Paris', 
        'departure_date': '2024-10-26', 
        'travel_class': 'BUSINESS'
    }
    mock_load_session.return_value = ("SEARCH_IN_PROGRESS", ["history"], [], {})
    
    # Run the task
    search_flights_task(user_id, flight_details)
    
    # Verify that AmadeusService's search_flights was called with the travelClass
    mock_amadeus_fixture.search_flights.assert_called_once()
    call_kwargs = mock_amadeus_fixture.search_flights.call_args[1]
    
    assert 'travelClass' in call_kwargs
    assert call_kwargs['travelClass'] == 'BUSINESS' 

import pytest
from unittest.mock import patch, MagicMock
from app.tasks import poll_usdc_payment_task


@pytest.fixture
def mock_circle_service(monkeypatch):
    """Fixture to mock the CircleService and its methods."""
    mock_instance = MagicMock()
    mock_class = MagicMock(return_value=mock_instance)
    # Patch CircleService where it's defined so the local import in the task gets the mock.
    monkeypatch.setattr("app.circle_service.CircleService", mock_class)
    return mock_instance


def test_poll_usdc_payment_task_success(monkeypatch, mock_circle_service):
    """Polling task should call handle_successful_payment when status becomes complete."""
    # Configure the mock to return different statuses on consecutive calls
    mock_circle_service.get_payment_intent_status.side_effect = ["pending", "pending", "complete"]

    # Spy on the successful payment handler
    mock_handle_payment = MagicMock()
    monkeypatch.setattr("app.main.handle_successful_payment", mock_handle_payment)

    # Mock time.sleep to avoid delays during the test
    monkeypatch.setattr("time.sleep", lambda x: None)

    # Run the task
    poll_usdc_payment_task("telegram:123", "intent_abc", poll_interval=0.01)

    # Assertions
    assert mock_circle_service.get_payment_intent_status.call_count == 3
    mock_handle_payment.assert_called_once_with("telegram:123")


def test_poll_usdc_payment_task_timeout(monkeypatch, mock_circle_service):
    """Polling task should exit gracefully after timeout if payment never completes."""
    # Configure the mock to always return 'pending'
    mock_circle_service.get_payment_intent_status.return_value = "pending"

    # Spy on the successful payment handler to ensure it's not called
    mock_handle_payment = MagicMock()
    monkeypatch.setattr("app.main.handle_successful_payment", mock_handle_payment)

    # Mock time.sleep to avoid delays
    monkeypatch.setattr("time.sleep", lambda x: None)

    # Run the task with a very short timeout
    poll_usdc_payment_task("telegram:456", "intent_def", poll_interval=0.01, timeout_seconds=0.05)

    # The handler should never be called
    mock_handle_payment.assert_not_called()
    # The status should have been checked multiple times
    assert mock_circle_service.get_payment_intent_status.call_count > 1 