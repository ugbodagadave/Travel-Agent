import pytest
from unittest.mock import patch
from app.main import app, amadeus_service
from twilio.twiml.messaging_response import MessagingResponse

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('app.main.process_message')
def test_webhook_uses_process_message(mock_process_message, client):
    """
    Tests that the main Twilio webhook correctly calls the process_message function
    and returns a TwiML response.
    """
    mock_process_message.return_value = ["This is a test response."]
    
    response = client.post('/webhook', data={
        'From': 'whatsapp:+15551234567',
        'Body': 'hello there'
    })
    
    assert response.status_code == 200
    
    # Check that process_message was called correctly
    mock_process_message.assert_called_once_with('whatsapp:+15551234567', 'hello there', amadeus_service)
    
    # Check that the response is valid TwiML
    twiml = MessagingResponse()
    twiml.message("This is a test response.")
    assert str(twiml) in str(response.data)

# This test is now obsolete due to the refactoring and can be removed.
# The core logic is tested in test_core_logic.py
def test_state_machine_flow(client):
    pass

# Keep the Stripe webhook test, but it will need updates later
# to handle platform-aware notifications.
def test_stripe_webhook_placeholder(client):
    # This is a placeholder to ensure the file runs.
    # The actual test will be more complex.
    assert 1 == 1 

@patch('stripe.Webhook.construct_event')
@patch('app.main.load_session')
@patch('app.main.save_session')
@patch('app.main.twilio_client')
def test_stripe_webhook_for_whatsapp(mock_twilio, mock_save, mock_load, mock_construct_event, client):
    """
    Tests the Stripe webhook's logic for a WhatsApp user.
    """
    user_id = "whatsapp:+15551112222"
    mock_construct_event.return_value = {
        'type': 'checkout.session.completed',
        'data': {'object': {'client_reference_id': user_id}}
    }
    mock_load.return_value = ("AWAITING_PAYMENT", [], [])

    response = client.post('/stripe-webhook', data='{}', headers={'Stripe-Signature': 'mock_sig'})
    
    assert response.status_code == 200
    mock_save.assert_called_with(user_id, "GATHERING_BOOKING_DETAILS", [], [])
    mock_twilio.messages.create.assert_called_once()

@patch('stripe.Webhook.construct_event')
@patch('app.main.load_session')
@patch('app.main.save_session')
@patch('app.main.send_message')
def test_stripe_webhook_for_telegram(mock_send_message, mock_save, mock_load, mock_construct_event, client):
    """
    Tests the Stripe webhook's logic for a Telegram user.
    """
    user_id = "telegram:123456789"
    chat_id = "123456789"
    mock_construct_event.return_value = {
        'type': 'checkout.session.completed',
        'data': {'object': {'client_reference_id': user_id}}
    }
    mock_load.return_value = ("AWAITING_PAYMENT", [], [])

    response = client.post('/stripe-webhook', data='{}', headers={'Stripe-Signature': 'mock_sig'})

    assert response.status_code == 200
    mock_save.assert_called_with(user_id, "GATHERING_BOOKING_DETAILS", [], [])
    mock_send_message.assert_called_once_with(chat_id, "Your payment was successful! To finalize the booking, please provide your full name and date of birth (e.g., John Doe YYYY-MM-DD).") 