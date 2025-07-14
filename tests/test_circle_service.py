import pytest
from unittest.mock import patch, MagicMock
from app.circle_service import CircleService
import requests

@pytest.fixture
def circle_service():
    """Fixture to provide an instance of the CircleService."""
    return CircleService()

@patch('app.circle_service.requests.get')
@patch('app.circle_service.requests.post')
def test_create_payment_wallet_success(mock_post, mock_get, circle_service):
    """
    Tests successful wallet creation.
    """
    # Mock the first API call (POST to /wallets)
    mock_post_response = MagicMock()
    mock_post_response.raise_for_status.return_value = None
    mock_post_response.json.return_value = {"data": {"walletId": "test_wallet_id"}}
    mock_post.return_value = mock_post_response

    # Mock the second API call (GET to /wallets/{id}/addresses)
    mock_get_response = MagicMock()
    mock_get_response.raise_for_status.return_value = None
    mock_get_response.json.return_value = {"data": [{"address": "test_address"}]}
    mock_get.return_value = mock_get_response

    result = circle_service.create_payment_wallet()

    assert result == {"walletId": "test_wallet_id", "address": "test_address"}
    mock_post.assert_called_once()
    mock_get.assert_called_once_with(
        "https://api-sandbox.circle.com/v1/wallets/test_wallet_id/addresses",
        headers=circle_service.headers
    )

@patch('app.circle_service.requests.post')
def test_create_payment_wallet_api_error(mock_post, circle_service):
    """
    Tests handling of a Circle API error during wallet creation.
    """
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")
    mock_response.text = '{"error": "Invalid API Key"}'
    mock_post.return_value = mock_response

    result = circle_service.create_payment_wallet()

    assert result is None
    mock_post.assert_called_once()

@patch('app.circle_service.requests.post')
def test_create_payment_wallet_missing_data(mock_post, circle_service):
    """
    Tests handling of a successful API response that is missing expected data.
    """
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"data": {}} # Missing walletId and address
    mock_post.return_value = mock_response

    result = circle_service.create_payment_wallet()

    assert result is None
    mock_post.assert_called_once() 