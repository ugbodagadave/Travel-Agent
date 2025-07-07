from flask import Flask
import pytest
from app.main import app, amadeus_service
from unittest.mock import patch

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
    mock_process_message.return_value = "Processed response"
    
    telegram_update = {
        "message": {
            "chat": {"id": 987654321},
            "text": "Hello Telegram"
        }
    }
    
    response = client.post("/telegram-webhook", json=telegram_update)
    
    assert response.status_code == 200
    
    # Check that process_message was called correctly
    mock_process_message.assert_called_once_with("telegram:987654321", "hello telegram", amadeus_service)
    
    # Check that send_message was called with the result
    mock_send_message.assert_called_once_with(987654321, "Processed response") 