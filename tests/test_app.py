import pytest
from unittest.mock import patch, mock_open, MagicMock
from app.main import app, amadeus_service, send_whatsapp_pdf
from twilio.twiml.messaging_response import MessagingResponse
from requests.exceptions import RequestException

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    with patch('app.new_session_manager.get_redis_client'):
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

@patch('app.main.twilio_client.messages.create')
@patch('app.main.send_whatsapp_pdf', return_value='http://mock.url/ticket.pdf')
@patch('app.main.create_flight_itinerary', return_value=b'pdf-content')
@patch('app.main.load_session')
@patch('stripe.Webhook.construct_event')
def test_stripe_webhook_sends_whatsapp_link(mock_construct_event, mock_load_session, mock_create_pdf, mock_send_pdf, mock_twilio_create, client):
    """
    Tests that the Stripe webhook sends a download link for WhatsApp users.
    """
    mock_load_session.return_value = ('AWAITING_PAYMENT', [], [{'id': 'flight1'}], {})
    mock_event = {'type': 'checkout.session.completed', 'data': {'object': {'client_reference_id': 'whatsapp:+123'}}}
    mock_construct_event.return_value = mock_event

    response = client.post('/stripe-webhook', data='{}', headers={'Stripe-Signature': 'mock_sig'})

    assert response.status_code == 200
    assert mock_twilio_create.call_count == 2
    
    # Check the first call (download link)
    first_call_args = mock_twilio_create.call_args_list[0][1]
    assert "Kindly download your flight ticket" in first_call_args['body']
    assert "http://mock.url/ticket.pdf" in first_call_args['body']
    
    # Check the second call (confirmation)
    second_call_args = mock_twilio_create.call_args_list[1][1]
    assert "Thank you for booking with Flai" in second_call_args['body']


@patch('app.main.requests.post')
def test_send_whatsapp_pdf_returns_url(mock_requests_post):
    """
    Tests that send_whatsapp_pdf returns a URL string on successful upload.
    """
    # Mock the response from the file hosting service
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.text = 'http://mock.url/file.pdf'
    mock_requests_post.return_value = mock_response

    # Call the function and check the return value
    result_url = send_whatsapp_pdf(b"pdf-data", "test.pdf")

    assert result_url == 'http://mock.url/file.pdf'

@patch('app.main.requests.post')
def test_send_whatsapp_pdf_returns_none_on_failure(mock_requests_post):
    """
    Tests that send_whatsapp_pdf returns None if the upload fails.
    """
    # Mock a failed response
    mock_requests_post.side_effect = RequestException("Upload failed")

    # Call the function and check the return value
    result_url = send_whatsapp_pdf(b"pdf-data", "test.pdf")

    assert result_url is None 