import pytest
from unittest.mock import patch, MagicMock
import requests
from app.circle_service import CircleService
import json


class DummyResponse:
    """Simple stand-in for requests.Response with controllable JSON data and status code."""

    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.text = json.dumps(data)

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception("HTTP Error")

    def json(self):
        return self._data


@pytest.fixture
def circle_service():
    return CircleService()

@patch('app.circle_service.time.sleep', return_value=None) # Mock sleep to speed up test
@patch('app.circle_service.requests.get')
@patch('app.circle_service.requests.post')
def test_create_payment_intent_success(mock_post, mock_get, mock_sleep, circle_service):
    """
    Tests successful payment intent creation and polling for the address.
    """
    # Mock the POST request to create the intent
    mock_post_response = MagicMock()
    mock_post_response.raise_for_status.return_value = None
    mock_post_response.json.return_value = {"data": {"id": "test_intent_id"}}
    mock_post.return_value = mock_post_response

    # Mock the GET request for polling
    mock_get_response_pending = MagicMock()
    mock_get_response_pending.raise_for_status.return_value = None
    mock_get_response_pending.json.return_value = {"data": {"paymentMethods": [{}]}} # No address yet

    mock_get_response_success = MagicMock()
    mock_get_response_success.raise_for_status.return_value = None
    mock_get_response_success.json.return_value = {
        "data": {"paymentMethods": [{"address": "test_address"}]}
    }
    
    # Simulate polling: first call is pending, second is success
    mock_get.side_effect = [mock_get_response_pending, mock_get_response_success]

    result = circle_service.create_payment_intent(150.75)

    assert result == {"walletId": "test_intent_id", "address": "test_address"}
    assert mock_post.call_count == 1
    assert mock_get.call_count == 2
    assert "paymentIntents" in mock_post.call_args.args[0]
    assert "paymentIntents/test_intent_id" in mock_get.call_args.args[0]


@patch('app.circle_service.requests.post')
def test_create_payment_intent_fails_on_creation(mock_post, circle_service):
    """
    Tests when the initial POST to create an intent fails.
    """
    mock_post.side_effect = requests.exceptions.RequestException("API Error")
    result = circle_service.create_payment_intent(100)
    assert result is None

@patch('app.circle_service.time.sleep', return_value=None)
@patch('app.circle_service.requests.get')
@patch('app.circle_service.requests.post')
def test_create_payment_intent_polling_times_out(mock_post, mock_get, mock_sleep, circle_service):
    """
    Tests when polling for the address times out.
    """
    mock_post_response = MagicMock()
    mock_post_response.raise_for_status.return_value = None
    mock_post_response.json.return_value = {"data": {"id": "test_intent_id"}}
    mock_post.return_value = mock_post_response

    mock_get_response_pending = MagicMock()
    mock_get_response_pending.raise_for_status.return_value = None
    mock_get_response_pending.json.return_value = {"data": {"paymentMethods": [{}]}}
    mock_get.return_value = mock_get_response_pending # Always return pending

    result = circle_service.create_payment_intent(100)

    assert result is None
    assert mock_get.call_count == 30 # Should poll 30 times
    assert mock_sleep.call_count == 30 


def test_get_payment_intent_status_complete(circle_service):
    """CircleService should return the latest status from the timeline (complete)."""
    fake_timeline = [
        {"status": "created", "time": "2025-07-15T10:00:00Z"},
        {"status": "pending", "time": "2025-07-15T10:05:00Z"},
        {"status": "complete", "time": "2025-07-15T10:10:00Z"},
    ]
    fake_data = {"data": {"timeline": fake_timeline}}

    with patch("app.circle_service.requests.get", return_value=DummyResponse(fake_data)):
        status = circle_service.get_payment_intent_status("intent_123")

    assert status == "complete"


def test_get_payment_intent_status_no_timeline(circle_service):
    """Returns None when timeline is missing or empty."""
    fake_data = {"data": {"timeline": []}}

    with patch("app.circle_service.requests.get", return_value=DummyResponse(fake_data)):
        status = circle_service.get_payment_intent_status("intent_456")

    assert status is None 