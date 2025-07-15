import pytest
from unittest.mock import MagicMock, patch, ANY
from app.core_logic import process_message, TRAVEL_CLASSES

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

@patch("app.core_logic.load_session")
@patch("app.core_logic.save_session")
@patch("app.core_logic.currency_service")
@patch("app.core_logic.circle_service")
@patch("app.core_logic.save_wallet_mapping")
def test_awaiting_payment_selection_usdc(mock_save_wallet, mock_circle, mock_currency, mock_save_session, mock_load_session):
    """
    Tests the 'USDC' payment path from AWAITING_PAYMENT_SELECTION.
    """
    user_id = "test_user_usdc"
    selected_flight = [{'id': 'flight1', 'price': {'total': '120.50', 'currency': 'EUR'}}]
    flight_details = {"some_detail": "value"}
    mock_load_session.return_value = ("AWAITING_PAYMENT_SELECTION", ["history"], selected_flight, flight_details)
    
    mock_currency.convert_to_usd.return_value = 130.00
    mock_circle.create_payment_intent.return_value = {"walletId": "mock-wallet-id", "address": "mock-usdc-address"}

    response = process_message(user_id, "USDC", MagicMock())

    assert len(response) == 2
    assert "To pay with USDC, please send exactly 130.00 USDC to the address below." in response[0]
    assert response[1] == "`mock-usdc-address`"
    
    mock_currency.convert_to_usd.assert_called_once_with(120.50, 'EUR')
    mock_circle.create_payment_intent.assert_called_once_with(130.00)
    mock_save_wallet.assert_called_once_with("mock-wallet-id", user_id)
    
    # Check that the session is saved with the new state and updated details
    updated_flight_details = flight_details.copy()
    updated_flight_details['expected_usd_amount'] = 130.00
    mock_save_session.assert_called_once_with(user_id, "AWAITING_USDC_PAYMENT", ["history"], selected_flight, updated_flight_details)

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

    assert "I didn't understand. Please reply with 'Card' or 'USDC'." in response[0]
    mock_save_session.assert_called_once_with(user_id, "AWAITING_PAYMENT_SELECTION", ["history"], selected_flight, {}) 