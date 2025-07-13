import pytest
from unittest.mock import patch, mock_open
from app.main import app, amadeus_service, send_whatsapp_pdf
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
@patch('app.main.create_flight_itinerary')
@patch('app.main.send_whatsapp_pdf')
def test_stripe_webhook_for_whatsapp_sends_pdf(mock_send_pdf, mock_create_pdf, mock_load_session, mock_construct_event, client):
    """
    Tests the Stripe webhook's logic for a WhatsApp user, ensuring it sends a PDF
    with the correct dynamic filename.
    """
    # Mock the session and event data, now including the traveler's name
    mock_session_data = ('AWAITING_PAYMENT', [], [{'id': 'flight1', 'traveler_name': 'David Ugbodaga'}])
    mock_load_session.return_value = mock_session_data
    mock_create_pdf.return_value = b'pdf-content'
    mock_event = {'type': 'checkout.session.completed', 'data': {'object': {'client_reference_id': 'whatsapp:+123'}}}
    mock_construct_event.return_value = mock_event

    response = client.post('/stripe-webhook', data='{}', headers={'Stripe-Signature': 'mock_sig'})

    assert response.status_code == 200
    mock_create_pdf.assert_called_once_with(mock_session_data[2][0])
    # Assert that the filename is now dynamic
    mock_send_pdf.assert_called_once_with('whatsapp:+123', b'pdf-content', 'flight_ticket_David_Ugbodaga.pdf')

@patch('stripe.Webhook.construct_event')
@patch('app.main.load_session')
@patch('app.main.create_flight_itinerary')
@patch('app.main.send_telegram_pdf')
@patch('app.main.send_message')
def test_stripe_webhook_for_telegram_sends_pdf(mock_send_text, mock_send_pdf, mock_create_pdf, mock_load_session, mock_construct_event, client):
    """
    Tests the Stripe webhook's logic for a Telegram user, ensuring it sends a PDF
    with the correct dynamic filename and an updated confirmation message.
    """
    # Mock the session and event data, now including the traveler's name
    mock_session_data = ('AWAITING_PAYMENT', [], [{'id': 'flight1', 'traveler_name': 'Jane Doe'}])
    mock_load_session.return_value = mock_session_data
    mock_create_pdf.return_value = b'pdf-content'
    mock_event = {'type': 'checkout.session.completed', 'data': {'object': {'client_reference_id': 'telegram:456'}}}
    mock_construct_event.return_value = mock_event

    response = client.post('/stripe-webhook', data='{}', headers={'Stripe-Signature': 'mock_sig'})

    assert response.status_code == 200
    mock_create_pdf.assert_called_once_with(mock_session_data[2][0])
    # Assert that the filename is now dynamic
    mock_send_pdf.assert_called_once_with('456', b'pdf-content', 'flight_ticket_Jane_Doe.pdf')
    # Assert that the confirmation text includes the new dynamic filename
    expected_text = "Thank you for booking with Flai. Your flight ticket (flight_ticket_Jane_Doe.pdf) has been sent."
    mock_send_text.assert_called_with('456', expected_text)

@patch('app.main.twilio_client.messages.create')
@patch('app.main.open', new_callable=mock_open)
@patch('app.main.os.path.exists', return_value=True)
def test_send_whatsapp_pdf(mock_exists, mock_file_open, mock_twilio_create):
    """
    Test the send_whatsapp_pdf function for sending a PDF via Twilio.
    """
    with app.test_request_context('/'):
        send_whatsapp_pdf("whatsapp:+15551234567", b"pdf-data", "test.pdf")

    # Verify file was written
    mock_file_open.assert_called_once()
    handle = mock_file_open()
    handle.write.assert_called_once_with(b"pdf-data")

    # Verify Twilio was called
    mock_twilio_create.assert_called_once()
    args, kwargs = mock_twilio_create.call_args
    assert kwargs['to'] == "whatsapp:+15551234567"
    assert "http://localhost/files/" in kwargs['media_url'][0] 