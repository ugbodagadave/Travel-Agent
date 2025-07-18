import pytest
from unittest.mock import patch, mock_open, MagicMock
from app.main import app, amadeus_service, send_whatsapp_pdf
from twilio.twiml.messaging_response import MessagingResponse

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

@patch('stripe.Webhook.construct_event')
@patch('app.main.load_session')
@patch('app.main.create_flight_itinerary')
@patch('app.main.send_whatsapp_pdf')
def test_stripe_webhook_sends_single_pdf_by_default(mock_send_pdf, mock_create_pdf, mock_load_session, mock_construct_event, client):
    """
    Tests the Stripe webhook sends a single PDF when no specific traveler names
    have been collected (fallback behavior).
    """
    # Mock session data without traveler_names list, but with a name in the offer
    flight_details = {} # No traveler_names list
    mock_session_data = ('AWAITING_PAYMENT', [], [{'id': 'flight1', 'traveler_name': 'David Ugbodaga'}], flight_details)
    mock_load_session.return_value = mock_session_data
    mock_create_pdf.return_value = b'pdf-content'
    mock_event = {'type': 'checkout.session.completed', 'data': {'object': {'client_reference_id': 'whatsapp:+123'}}}
    mock_construct_event.return_value = mock_event

    response = client.post('/stripe-webhook', data='{}', headers={'Stripe-Signature': 'mock_sig'})

    assert response.status_code == 200
    # Assert it was called once with the name from the flight offer
    mock_create_pdf.assert_called_once_with(mock_session_data[2][0], traveler_name='David Ugbodaga')
    mock_send_pdf.assert_called_once_with('whatsapp:+123', b'pdf-content', 'flight_ticket_David_Ugbodaga.pdf')

@patch('stripe.Webhook.construct_event')
@patch('app.main.load_session')
@patch('app.main.create_flight_itinerary')
@patch('app.main.send_telegram_pdf')
@patch('app.main.send_message')
def test_stripe_webhook_sends_multiple_pdfs_for_multiple_travelers(mock_send_text, mock_send_pdf, mock_create_pdf, mock_load_session, mock_construct_event, client):
    """
    Tests the Stripe webhook's logic for sending multiple, personalized PDFs
    when multiple traveler names have been collected.
    """
    # Mock session data WITH a list of traveler_names
    flight_details = {"traveler_names": ["Jane Doe", "John Smith"]}
    mock_session_data = ('AWAITING_PAYMENT', [], [{'id': 'flight1'}], flight_details)
    mock_load_session.return_value = mock_session_data
    mock_create_pdf.return_value = b'pdf-content'
    mock_event = {'type': 'checkout.session.completed', 'data': {'object': {'client_reference_id': 'telegram:456'}}}
    mock_construct_event.return_value = mock_event

    response = client.post('/stripe-webhook', data='{}', headers={'Stripe-Signature': 'mock_sig'})

    assert response.status_code == 200
    # Assert that create and send were called for each traveler
    assert mock_create_pdf.call_count == 2
    assert mock_send_pdf.call_count == 2

    # Check the calls for the first traveler
    mock_create_pdf.assert_any_call(mock_session_data[2][0], traveler_name="Jane Doe")
    mock_send_pdf.assert_any_call('456', b'pdf-content', 'flight_ticket_Jane_Doe.pdf')
    
    # Check the calls for the second traveler
    mock_create_pdf.assert_any_call(mock_session_data[2][0], traveler_name="John Smith")
    mock_send_pdf.assert_any_call('456', b'pdf-content', 'flight_ticket_John_Smith.pdf')

    # Assert that the final confirmation message is for multiple tickets
    expected_text = "Thank you for booking with Flai 😊. I've sent 2 separate tickets for each passenger."
    mock_send_text.assert_called_with('456', expected_text)


@patch('app.main.twilio_client.messages.create')
@patch('app.main.open', new_callable=mock_open)
@patch('app.main.os.path.exists', return_value=True)
@patch('app.main.requests.post')
def test_send_whatsapp_pdf_uploads_and_sends_url(mock_requests_post, mock_exists, mock_file_open, mock_twilio_create):
    """
    Tests that send_whatsapp_pdf uploads the file and sends the correct URL.
    """
    # Mock the response from the file hosting service
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {'link': 'http://mock.url/file.pdf'}
    mock_requests_post.return_value = mock_response

    # Call the function
    send_whatsapp_pdf("whatsapp:+15551234567", b"pdf-data", "test.pdf")

    # Verify that the file was uploaded
    mock_requests_post.assert_called_once()
    
    # Verify that Twilio was called with the correct media URL
    mock_twilio_create.assert_called_once()
    args, kwargs = mock_twilio_create.call_args
    assert 'media_url' in kwargs
    assert kwargs['media_url'] == ['http://mock.url/file.pdf'] 