import pytest
import os
from unittest.mock import patch, MagicMock
import json

from app.main import app
from app.session_manager import save_session

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('app.main.get_ai_response')
@patch('app.main.amadeus_service')
@patch('app.main.create_checkout_session')
@patch('app.main.twilio_client')
def test_full_booking_e2e_flow(mock_twilio_client, mock_create_checkout_session, mock_amadeus_service, mock_get_ai_response, client):
    user_id = "whatsapp:+15551234567"
    
    # --- Test Setup: Ensure clean session ---
    save_session(user_id, "GATHERING_INFO", [], [])

    # --- Step 1 & 2: Initial Conversation and Flight Selection ---
    # Mock AI response for gathering info
    mock_get_ai_response.return_value = ("Okay, I have a one-way flight for 1 person from Paris to New York on 2024-12-25. [INFO_COMPLETE]", [("user", "flight from paris to new york tomorrow for 1"), ("assistant", "Okay, I have a one-way flight for 1 person from Paris to New York on 2024-12-25. [INFO_COMPLETE]")])

    # Mock Amadeus flight search
    mock_flight_offer = {
        "itineraries": [{"segments": [{"arrival": {"iataCode": "JFK"}}]}],
        "price": {"total": "500.00", "currency": "USD"}
    }
    mock_amadeus_service.search_flights.return_value = [mock_flight_offer]

    # Mock AI for extracting details
    with patch('app.main.extract_flight_details_from_history', return_value={
        'origin': 'Paris', 'destination': 'New York', 'departure_date': '2024-12-25', 'number_of_travelers': '1'
    }):
        # User initiates and confirms in one logical step for the test setup
        client.post('/webhook', data={'From': user_id, 'Body': 'Hi, I need a flight...'})
        response_with_flights = client.post('/webhook', data={'From': user_id, 'Body': 'Yes, correct.'})

    # Assert that the flight options were sent
    assert "I found a few options for you" in str(response_with_flights.data)

    # Mock checkout session creation
    mock_create_checkout_session.return_value = "https://checkout.stripe.com/pay/mock_session_id"
    
    # User selects a flight
    response_with_link = client.post('/webhook', data={'From': user_id, 'Body': '1'})
    
    # Assert that the user gets the payment link
    assert "https://checkout.stripe.com/pay/mock_session_id" in str(response_with_link.data)

    # --- Step 3: Stripe Webhook and Final Booking ---
    # Mock the stripe.Webhook.construct_event call
    with patch('stripe.Webhook.construct_event') as mock_construct_event:
        # Create a fake event payload as a dictionary
        mock_event = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'client_reference_id': user_id
                }
            }
        }
        mock_construct_event.return_value = mock_event

        # Call the webhook
        client.post('/stripe-webhook', data=json.dumps({'type': 'checkout.session.completed'}), content_type='application/json', headers={'Stripe-Signature': 'mock_sig'})
    
    # Assert that a message was sent asking for details
    mock_twilio_client.messages.create.assert_called_once()
    call_args = mock_twilio_client.messages.create.call_args
    assert "Your payment was successful!" in call_args[1]['body']
    assert call_args[1]['to'] == user_id
    
    # --- Step 4: User provides details and final booking ---
    # Mock AI for traveler detail extraction
    with patch('app.main.extract_traveler_details', return_value={"fullName": "John Doe", "dateOfBirth": "1990-01-01"}):
        # Mock Amadeus booking
        mock_amadeus_service.book_flight.return_value = {"id": "mock_booking_id"}
        
        # User sends their details
        response = client.post('/webhook', data={'From': user_id, 'Body': 'John Doe 1990-01-01'})

    # Assert Amadeus booking was called
    mock_amadeus_service.book_flight.assert_called_once()
    
    # Assert final confirmation message
    assert "Your flight is booked!" in str(response.data)
    assert "mock_booking_id" in str(response.data) 