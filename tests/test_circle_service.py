import pytest
from unittest.mock import patch, MagicMock
import requests
from app.circle_service import CircleService

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
    assert mock_get.call_count == 10 # Should poll 10 times 