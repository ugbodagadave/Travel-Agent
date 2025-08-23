from flask import Flask
import pytest
from app.main import app, amadeus_service
from unittest.mock import patch, Mock
import os
from app.telegram_service import send_pdf

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_telegram_webhook_ok(client):
    """
    Tests that the /telegram-webhook endpoint returns a 200 OK response even with no data.
    """
    response = client.post("/telegram-webhook", json={})
    assert response.status_code == 200
    assert response.data == b"OK"

@patch("app.main.process_message")
@patch("app.main.send_message")
def test_telegram_webhook_uses_process_message(mock_send_message, mock_process_message, client):
    """
    Tests that the Telegram webhook correctly calls process_message and then send_message.
    """
    mock_process_message.return_value = ["Processed response"]
    
    telegram_update = {
        "message": {
            "chat": {"id": 987654321},
            "text": "Hello Telegram"
        }
    }
    
    response = client.post("/telegram-webhook", json=telegram_update)
    
    assert response.status_code == 200
    
    # Check that process_message was called correctly
    mock_process_message.assert_called_once_with("telegram:987654321", "Hello Telegram", amadeus_service)
    
    # Check that send_message was called with the result
    mock_send_message.assert_called_once_with("987654321", "Processed response") 

@patch('requests.post')
def test_send_pdf(mock_post):
    """
    Test that the send_pdf function calls the Telegram API correctly.
    """
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {'ok': True}
    mock_post.return_value = mock_response

    chat_id = "12345"
    pdf_bytes = b"%PDF-test-data"
    
    send_pdf(chat_id, pdf_bytes, "test.pdf")

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert f"bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendDocument" in args[0]
    assert kwargs['data'] == {'chat_id': chat_id}
    assert 'document' in kwargs['files']
    assert kwargs['files']['document'][0] == "test.pdf"
    assert kwargs['files']['document'][1] == pdf_bytes
    assert kwargs['files']['document'][2] == "application/pdf" 