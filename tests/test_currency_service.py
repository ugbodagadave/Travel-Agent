import pytest
from unittest.mock import patch, MagicMock
from app.currency_service import CurrencyService
import requests

@pytest.fixture
def currency_service():
    """Fixture to provide an instance of the CurrencyService."""
    return CurrencyService()

@patch('app.currency_service.requests.get')
def test_convert_to_usd_success(mock_get, currency_service):
    """
    Tests successful currency conversion to USD.
    """
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"rates": {"USD": 108.5}}
    mock_get.return_value = mock_response

    result = currency_service.convert_to_usd(100, "EUR")

    assert result == 108.5
    mock_get.assert_called_once_with("https://api.frankfurter.app/latest?amount=100&from=EUR&to=USD")

def test_convert_to_usd_same_currency(currency_service):
    """
    Tests that conversion from USD to USD returns the same amount without an API call.
    """
    with patch('app.currency_service.requests.get') as mock_get:
        result = currency_service.convert_to_usd(150, "USD")
        assert result == 150
        mock_get.assert_not_called()

@patch('app.currency_service.requests.get')
def test_convert_to_usd_api_error(mock_get, currency_service):
    """
    Tests handling of an API error during currency conversion.
    """
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")
    mock_get.return_value = mock_response

    result = currency_service.convert_to_usd(100, "EUR")

    assert result is None
    mock_get.assert_called_once() 