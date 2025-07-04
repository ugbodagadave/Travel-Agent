import pytest
from unittest.mock import patch
from app.main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('app.main.get_ai_response')
def test_webhook_with_mocked_ai(mock_get_ai_response, client):
    """Test the webhook's integration with the AI service."""
    # Configure the mock to return a predictable response
    mock_get_ai_response.return_value = "This is a test response from the AI."

    # Simulate a Twilio request
    data = {
        'From': 'whatsapp:+15551234567',
        'Body': 'Hello AI!'
    }
    response = client.post('/webhook', data=data)

    # Assert that our AI function was called correctly
    mock_get_ai_response.assert_called_once_with('Hello AI!')

    # Assert that the response is correct
    assert response.status_code == 200
    assert 'application/xml' in response.content_type
    response_text = response.data.decode('utf-8')
    assert '<Message>This is a test response from the AI.</Message>' in response_text 