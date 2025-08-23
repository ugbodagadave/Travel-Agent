import pytest
from unittest.mock import MagicMock, patch, ANY
from app.core_logic import process_message, TRAVEL_CLASSES
from app.new_session_manager import save_session, load_session
import os

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
    mock_load_session.return_value = ("GATHERING_INFO", [], [], {})
    mock_get_ai.return_value = ("Hello! How can I help you?", ["user: hi", "ai: Hello! How can I help you?"])
    
    response = process_message("test_user", "hi", mock_amadeus_service)
    
    assert response == ["Hello! How can I help you?"]
    mock_load_session.assert_called_once_with("test_user")
    mock_get_ai.assert_called_once()
    mock_save_session.assert_called_once_with("test_user", "GATHERING_INFO", ANY, [], {})

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("app.core_logic.extract_flight_details_from_history")
@patch("app.core_logic.get_ai_response")
def test_info_complete_transitions_to_class_selection_for_single_traveler(mock_get_ai, mock_extract, mock_save_session, mock_load_session):
    """
    Tests that after info is complete for a single traveler, the state transitions
    to AWAITING_CLASS_SELECTION.
    """
    mock_load_session.return_value = ("GATHERING_INFO", [{"role": "user", "content": "hi"}], [], {})
    mock_get_ai.return_value = ("[INFO_COMPLETE]", [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "[INFO_COMPLETE]"}])
    flight_details = {"origin": "BOS", "destination": "LHR", "number_of_travelers": 1}
    mock_extract.return_value = flight_details

    response = process_message("user1", "I want to fly to London", MagicMock())

    assert "What class would you like to fly?" in response[0]
    assert "ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST" in response[0]
    mock_save_session.assert_called_with("user1", "AWAITING_CLASS_SELECTION", ANY, [], flight_details)

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("app.core_logic.extract_traveler_names")
def test_name_gathering_complete_transitions_to_class_selection(mock_extract_names, mock_save_session, mock_load_session):
    """
    Tests that after gathering names, the state transitions to AWAITING_CLASS_SELECTION.
    """
    flight_details = {"number_of_travelers": 2}
    mock_load_session.return_value = ("GATHERING_NAMES", [], [], flight_details)
    mock_extract_names.return_value = ["David Ugbodaga", "Esther Ugbodaga"]

    response = process_message("user1", "David, Esther", MagicMock())

    assert "Great, I have all the names." in response[0]
    assert "What class would you like to fly?" in response[1]
    
    saved_args, _ = mock_save_session.call_args
    assert saved_args[1] == "AWAITING_CLASS_SELECTION"
    assert saved_args[4]["traveler_names"] == ["David Ugbodaga", "Esther Ugbodaga"]

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
def test_awaiting_class_selection_valid_input(mock_save_session, mock_load_session):
    """
    Tests the AWAITING_CLASS_SELECTION state with a valid class and traveler name.
    """
    flight_details = {
        "origin": "BOS", 
        "destination": "LHR", 
        "number_of_travelers": 1,
        "traveler_name": "John Doe" # Add traveler name for the test
    }
    mock_load_session.return_value = ("AWAITING_CLASS_SELECTION", [], [], flight_details)

    response = process_message("user1", "BUSINESS", MagicMock())

    assert "Please confirm the details" in response[0]
    assert "Class: Business" in response[0]
    assert "Traveler: John Doe" in response[0] # Assert the name is in the output
    assert "Origin: BOS" in response[0]
    
    saved_args, _ = mock_save_session.call_args
    assert saved_args[1] == "AWAITING_CONFIRMATION"
    assert saved_args[4]["travel_class"] == "BUSINESS"

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
def test_awaiting_class_selection_invalid_input(mock_save_session, mock_load_session):
    """
    Tests the AWAITING_CLASS_SELECTION state with an invalid class.
    """
    flight_details = {"origin": "BOS", "destination": "LHR", "number_of_travelers": 1}
    mock_load_session.return_value = ("AWAITING_CLASS_SELECTION", ["history"], [], flight_details)

    response = process_message("user1", "invalid class", MagicMock())

    assert "That's not a valid class." in response[0]
    assert "ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST" in response[0]
    
    mock_save_session.assert_called_with("user1", "AWAITING_CLASS_SELECTION", ["history"], [], flight_details)

@patch("threading.Thread")
@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("app.core_logic.get_ai_response")
def test_process_message_awaiting_confirmation_triggers_task_on_confirm(mock_get_ai, mock_save_session, mock_load_session, mock_thread):
    """
    Tests that the AWAITING_CONFIRMATION state triggers the task when the AI confirms.
    """
    user_id = "test_user"
    # Flight details now include the travel class selected in the previous step
    flight_details = {'origin': 'London', 'destination': 'Paris', 'travel_class': 'ECONOMY'}
    mock_load_session.return_value = ("AWAITING_CONFIRMATION", ["history"], [], flight_details)
    mock_get_ai.return_value = ("[CONFIRMED]", ["history", {"role": "assistant", "content": "[CONFIRMED]"}])
    
    # Mock the thread object
    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance

    response = process_message(user_id, "yeap", MagicMock())
    
    mock_get_ai.assert_called_once_with("yeap", ["history"], "AWAITING_CONFIRMATION")
    
    # Check for immediate user feedback
    assert response[0] == "Okay, I'm searching for the best flights for you. This might take a moment..."
    
    # Check that a thread was created with the correct target and arguments
    mock_thread.assert_called_once_with(target=ANY, args=(user_id, flight_details))
    
    # Check that the thread was started
    mock_thread_instance.start.assert_called_once()
    
    # Check that the state was updated to SEARCH_IN_PROGRESS
    mock_save_session.assert_called_with(user_id, "SEARCH_IN_PROGRESS", ["history", {"role": "assistant", "content": "[CONFIRMED]"}], [], flight_details)

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("app.core_logic.get_ai_response")
@patch("app.core_logic.extract_flight_details_from_history")
def test_process_message_awaiting_confirmation_handles_correction_and_re_asks_class(mock_extract_details, mock_get_ai, mock_save_session, mock_load_session):
    """
    Tests that if a user correction removes travel class, the agent re-asks for it.
    """
    user_id = "test_user_correcting"
    # Initial state has a travel class
    initial_details = {'origin': 'LHR', 'destination': 'CDG', 'travel_class': 'BUSINESS'}
    mock_load_session.return_value = ("AWAITING_CONFIRMATION", ["history"], [], initial_details)
    
    # Simulate the AI re-parsing details, but this time without a travel_class
    ai_correction_response = "You are right, to JFK. [INFO_COMPLETE]"
    updated_history = ["history", {"role": "assistant", "content": ai_correction_response}]
    mock_get_ai.return_value = (ai_correction_response, updated_history)
    
    # The new extracted details do NOT have a travel class
    corrected_details = {'origin': 'LHR', 'destination': 'JFK'}
    mock_extract_details.return_value = corrected_details
    
    response = process_message(user_id, "no, to JFK", MagicMock())

    # Check that the agent now asks for the class again
    assert "What class would you like to fly?" in response[0]
    
    # Check that the state is now AWAITING_CLASS_SELECTION
    mock_save_session.assert_called_with(user_id, "AWAITING_CLASS_SELECTION", ANY, [], corrected_details)

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
def test_process_message_search_in_progress(mock_save_session, mock_load_session):
    """
    Tests that the agent gives a waiting message if the user messages
    during the SEARCH_IN_PROGRESS state.
    """
    user_id = "test_user_searching"
    mock_load_session.return_value = ("SEARCH_IN_PROGRESS", ["history"], [], {})

    response = process_message(user_id, "are you done yet?", MagicMock())

    assert len(response) == 1
    assert "I'm still looking for flights" in response[0]
    mock_save_session.assert_called_once_with(user_id, "SEARCH_IN_PROGRESS", ["history"], [], {})

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("app.core_logic.create_checkout_session")
def test_flight_selection_creates_payment_link(mock_create_checkout, mock_save_session, mock_load_session):
    """
    Tests that a valid flight selection transitions to the AWAITING_PAYMENT_SELECTION state.
    """
    user_id = "test_user_selecting"
    flight_offers = [
        {'id': 'flight1', 'traveler_name': 'David Ugbodaga'},
        {'id': 'flight2', 'traveler_name': 'David Ugbodaga'}
    ]
    mock_load_session.return_value = ("FLIGHT_SELECTION", ["history"], flight_offers, {})

    response = process_message(user_id, "1", MagicMock())

    # Check that create_checkout_session is NOT called
    mock_create_checkout.assert_not_called()
    
    # Check for the correct user response
    assert "You've selected a great flight" in response[0]
    assert "How would you like to pay?" in response[0]
    
    # Check that the session was updated correctly to the new state
    mock_save_session.assert_called_once_with(user_id, "AWAITING_PAYMENT_SELECTION", ["history"], [flight_offers[0]], {})

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("app.core_logic.extract_flight_details_from_history")
@patch("app.core_logic.get_ai_response")
def test_process_message_starts_name_gathering_for_multiple_travelers(mock_get_ai, mock_extract_details, mock_save_session, mock_load_session):
    """
    Tests that the state transitions to GATHERING_NAMES when multiple travelers are detected.
    """
    mock_load_session.return_value = ("GATHERING_INFO", [], [], {})
    mock_get_ai.return_value = ("Info complete [INFO_COMPLETE]", ["history"])
    # Simulate the AI extracting details for 2 travelers
    flight_details = {"number_of_travelers": 2, "origin": "LHR"}
    mock_extract_details.return_value = flight_details

    response = process_message("user1", "a message", MagicMock())

    assert "Please provide their full names" in response[0]
    mock_save_session.assert_called_with("user1", "GATHERING_NAMES", ["history"], [], flight_details)

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("app.core_logic.extract_traveler_names")
def test_process_message_handles_incorrect_name_count(mock_extract_names, mock_save_session, mock_load_session):
    """
    Tests that the agent asks for names again if the wrong number is provided.
    """
    flight_details = {"number_of_travelers": 3, "origin": "LHR"}
    mock_load_session.return_value = ("GATHERING_NAMES", ["history"], [], flight_details)
    # Simulate the AI failing to extract the correct number of names
    mock_extract_names.return_value = []

    response = process_message("user1", "John Doe, Jane Smith", MagicMock())

    assert "provide exactly 3 full names" in response[0]
    mock_save_session.assert_called_with("user1", "GATHERING_NAMES", ["history"], [], flight_details) 

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("app.core_logic.create_checkout_session")
def test_awaiting_payment_selection_card(mock_create_checkout, mock_save_session, mock_load_session):
    """
    Tests the 'Card' payment path from AWAITING_PAYMENT_SELECTION.
    """
    user_id = "test_user_card"
    selected_flight = [{'id': 'flight1', 'price': {'total': '100', 'currency': 'USD'}}]
    mock_load_session.return_value = ("AWAITING_PAYMENT_SELECTION", ["history"], selected_flight, {})
    mock_create_checkout.return_value = "http://mock.stripe.url"

    response = process_message(user_id, "Card", MagicMock())

    assert "Great! Please complete your payment" in response[0]
    assert "http://mock.stripe.url" in response[0]
    mock_create_checkout.assert_called_once_with(selected_flight[0], user_id)
    mock_save_session.assert_called_once_with(user_id, "AWAITING_PAYMENT", ["history"], selected_flight, {})

@patch("threading.Thread")
@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("app.core_logic.get_ai_response")
def test_process_message_confirmation_parses_date_before_task(mock_get_ai, mock_save_session, mock_load_session, mock_thread, monkeypatch):
    """
    Tests that a human-readable date is correctly parsed and reformatted
    to YYYY-MM-DD before being passed to the flight search task.
    """
    user_id = "test_user_date_parsing"
    flight_details = {'origin': 'LHR', 'destination': 'JFK', 'departure_date': 'July 19th, 2025'}
    mock_load_session.return_value = ("AWAITING_CONFIRMATION", [], [], flight_details)
    mock_get_ai.return_value = ("[CONFIRMED]", [])

    # We need to correctly mock the thread's target function to inspect its arguments
    mock_search_task = MagicMock()
    # Configure the mock_thread to use our mock task as the target
    mock_thread.side_effect = lambda target, args: target(*args) # This allows the task to run in the test thread
    monkeypatch.setattr("app.core_logic.search_flights_task", mock_search_task)


    # Action
    process_message(user_id, "yes", MagicMock())

    # Assertion
    # Verify that the search task was called with the correctly formatted date
    mock_search_task.assert_called_once()
    call_args, _ = mock_search_task.call_args
    passed_flight_details = call_args[1]
    assert passed_flight_details['departure_date'] == '2025-07-19'


def test_awaiting_payment_selection_usdc(monkeypatch):
    """Core logic should generate a USDC payment address and be fully isolated."""
    user_id = "test_user_usdc"
    initial_state = "AWAITING_PAYMENT_SELECTION"
    selected_flight = [{"price": {"total": "150.00", "currency": "EUR"}}]
    
    # 1. Mock all session management functions to isolate from Redis
    mock_load_session = MagicMock(return_value=(initial_state, [], selected_flight, {}))
    mock_save_session = MagicMock()
    mock_save_wallet = MagicMock()
    monkeypatch.setattr("app.core_logic.load_session", mock_load_session)
    monkeypatch.setattr("app.core_logic.save_session", mock_save_session)
    monkeypatch.setattr("app.core_logic.save_wallet_mapping", mock_save_wallet)

    # 2. Mock external services (Circle, Currency, Threading)
    mock_circle_service = MagicMock()
    mock_circle_service.create_payment_intent.return_value = {
        "walletId": "mock-wallet-id",
        "address": "mock-usdc-address"
    }
    monkeypatch.setattr("app.core_logic.circle_service", mock_circle_service)
    
    mock_currency_service = MagicMock()
    mock_currency_service.convert_to_usd.return_value = 165.00
    monkeypatch.setattr("app.core_logic.currency_service", mock_currency_service)
    
    mock_thread = MagicMock()
    monkeypatch.setattr("threading.Thread", mock_thread)

    # Action
    responses = process_message(user_id, "usdc", amadeus_service=MagicMock())

    # Assertions
    assert len(responses) == 2, "Should return two messages: instructions and the address."
    assert "please send exactly 10.00 USDC" in responses[0]
    # The address is now sent without backticks for easy copying
    assert responses[1] == "mock-usdc-address"

    # Verify mocks were called correctly
    mock_load_session.assert_called_once_with(user_id)
    mock_circle_service.create_payment_intent.assert_called_once_with(10.00)
    mock_save_wallet.assert_called_once_with("mock-wallet-id", user_id)
    mock_thread.assert_called_once()
    
    # Verify the final state was saved correctly
    mock_save_session.assert_called_with(
        user_id,
        "AWAITING_USDC_PAYMENT",
        [],
        selected_flight,
        {'expected_usd_amount': 10.00}
    )

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("threading.Thread")
@patch("app.core_logic.save_evm_mapping")
@patch("app.core_logic.save_circlelayer_payment_info")
@patch("app.core_logic.get_next_address_index", return_value=0)
@patch("app.core_logic.circlelayer_service.CircleLayerService")
def test_awaiting_payment_selection_circle_layer(mock_circlelayer_service, mock_get_index, mock_save_payment_info, mock_save_evm, mock_thread, mock_save_session, mock_load_session):
    user_id = "test_user_clayer"
    selected_flight = [{"price": {"total": "200.00", "currency": "USD"}}]
    mock_load_session.return_value = ("AWAITING_PAYMENT_SELECTION", [], selected_flight, {})
    
    # Mock the CircleLayerService instance and its methods
    mock_service_instance = MagicMock()
    mock_service_instance.check_native_balance.return_value = 0
    mock_circlelayer_service.return_value = mock_service_instance
    
    # Mock the create_deposit_address class method
    mock_deposit = MagicMock()
    mock_deposit.get.return_value = "0xDEPOSIT"
    mock_circlelayer_service.create_deposit_address.return_value = mock_deposit

    responses = process_message(user_id, "Circle Layer", MagicMock())

    assert len(responses) == 2
    assert "please send exactly 1.00 CLAYER" in responses[0]
    assert responses[1] == "0xDEPOSIT"
    
    # Verify payment tracking was saved
    mock_save_payment_info.assert_called_once_with(
        user_id=user_id,
        address="0xDEPOSIT",
        initial_balance=0,
        expected_amount=1000000000000000000,
        address_index=0
    )
    
    # Verify session was saved with new fields
    mock_save_session.assert_called_with(user_id, "AWAITING_CIRCLE_LAYER_PAYMENT", [], selected_flight, {
        'circlelayer': {
            'address': '0xDEPOSIT',
            'token_address': None,  # Native token - no contract address
            'amount': 1000000000000000000,  # 1 CLAYER in wei (18 decimals)
            'decimals': 18,
            'address_index': 0,
            'initial_balance': 0
        }
    })

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
def test_awaiting_payment_selection_invalid(mock_save_session, mock_load_session):
    """
    Tests an invalid input in the AWAITING_PAYMENT_SELECTION state.
    """
    user_id = "test_user_invalid"
    selected_flight = [{'id': 'flight1'}]
    mock_load_session.return_value = ("AWAITING_PAYMENT_SELECTION", ["history"], selected_flight, {})

    response = process_message(user_id, "Bitcoin", MagicMock())

    assert "I didn't understand. Please reply with 'Card', 'USDC', or 'Pay on-chain (Circle Layer)'." in response[0]
    mock_save_session.assert_called_once_with(user_id, "AWAITING_PAYMENT_SELECTION", ["history"], selected_flight, {}) 