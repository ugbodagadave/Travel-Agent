import pytest
from unittest.mock import patch, MagicMock
from app.circle_service import CircleService
import requests

@pytest.fixture
def circle_service():
    """Fixture to provide an instance of the CircleService."""
    return CircleService()

@patch('app.circle_service.requests.post')
def test_create_payment_wallet_success(mock_post, circle_service):
    """
    Tests successful wallet creation.
    """
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "data": {
            "walletId": "test_wallet_id",
            "address": "test_address"
        }
    }
    mock_post.return_value = mock_response

    result = circle_service.create_payment_wallet()

    assert result == {"walletId": "test_wallet_id", "address": "test_address"}
    mock_post.assert_called_once()
    assert "wallets" in mock_post.call_args[0][0]

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