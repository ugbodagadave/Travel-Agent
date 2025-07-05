import pytest
import os
from unittest.mock import patch, MagicMock
import json

from app.main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('app.main.load_session')
@patch('app.main.save_session') # Also mock save_session to do nothing
@patch('app.main.get_ai_response')
@patch('app.main.amadeus_service')
@patch('app.main.create_checkout_session')
@patch('app.main.twilio_client')
@patch('app.main.extract_traveler_details')
def test_full_booking_e2e_flow(
    mock_extract_traveler_details,
    mock_twilio_client, 
    mock_create_checkout_session, 
    mock_amadeus_service, 
    mock_get_ai_response, 
    mock_save_session,
    mock_load_session,
    client
):
    user_id = "whatsapp:+15551234567"
    mock_flight_offer = {
        "itineraries": [{"segments": [{"arrival": {"iataCode": "JFK"}}]}],
        "price": {"total": "500.00", "currency": "USD"}
    }
    
    # Let's simplify the state management to be more realistic
    # We will store the state and check it at each step
    
    # --- Step 1: Initial conversation ---
    mock_load_session.return_value = ("GATHERING_INFO", [], [])
    mock_get_ai_response.return_value = ("Okay, I have a one-way flight... [INFO_COMPLETE]", [("user", "flight...")])
    client.post('/webhook', data={'From': user_id, 'Body': 'Hi...'})
    mock_save_session.assert_called_with(user_id, "AWAITING_CONFIRMATION", [("user", "flight...")], [])

    # --- Step 2: Confirmation and Flight Search ---
    mock_load_session.return_value = ("AWAITING_CONFIRMATION", [("user", "flight...")], [])
    with patch('app.main.extract_flight_details_from_history', return_value={'origin': 'Paris', 'destination': 'New York', 'departure_date': '2024-12-25', 'number_of_travelers': '1'}):
        mock_amadeus_service.search_flights.return_value = [mock_flight_offer]
        client.post('/webhook', data={'From': user_id, 'Body': 'Yes'})
    mock_save_session.assert_called_with(user_id, "FLIGHT_SELECTION", [("user", "flight...")], [mock_flight_offer])

    # --- Step 3: Flight Selection ---
    mock_load_session.return_value = ("FLIGHT_SELECTION", [("user", "flight...")], [mock_flight_offer])
    mock_create_checkout_session.return_value = "https://checkout.stripe.com/pay/mock_session_id"
    client.post('/webhook', data={'From': user_id, 'Body': '1'})
    mock_save_session.assert_called_with(user_id, "AWAITING_PAYMENT", [("user", "flight...")], [mock_flight_offer])

    # --- Step 4: Stripe Webhook ---
    mock_load_session.return_value = ("AWAITING_PAYMENT", [("user", "flight...")], [mock_flight_offer])
    with patch('stripe.Webhook.construct_event') as mock_construct_event:
        mock_event = {'type': 'checkout.session.completed', 'data': {'object': {'client_reference_id': user_id}}}
        mock_construct_event.return_value = mock_event
        client.post('/stripe-webhook', data=json.dumps({}), headers={'Stripe-Signature': 'mock_sig'})
    mock_save_session.assert_called_with(user_id, "GATHERING_BOOKING_DETAILS", [("user", "flight...")], [mock_flight_offer])

    # --- Step 5: Final Booking ---
    mock_load_session.return_value = ("GATHERING_BOOKING_DETAILS", [("user", "flight...")], [mock_flight_offer])
    mock_extract_traveler_details.return_value = {"fullName": "John Doe", "dateOfBirth": "1990-01-01"}
    mock_amadeus_service.book_flight.return_value = {"id": "mock_booking_id"}
    response_final = client.post('/webhook', data={'From': user_id, 'Body': 'John Doe 1990-01-01'})
    
    mock_amadeus_service.book_flight.assert_called_once()
    assert "Your flight is booked!" in str(response_final.data)
    assert "mock_booking_id" in str(response_final.data)