import pytest
from unittest.mock import patch, MagicMock
from app.payment_service import create_checkout_session

@patch('app.payment_service.stripe.checkout.Session.create')
def test_create_checkout_session_success(mock_stripe_create):
    """
    Test successful creation of a Stripe Checkout session.
    """
    # Arrange
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/mock_url"
    mock_stripe_create.return_value = mock_session

    flight_offer = {
        'price': {'total': '123.45', 'currency': 'USD'},
        'itineraries': [{'segments': [{'arrival': {'iataCode': 'LHR'}}]}]
    }
    user_id = "whatsapp:+15551234567"

    # Act
    checkout_url = create_checkout_session(flight_offer, user_id)

    # Assert
    assert checkout_url == "https://checkout.stripe.com/mock_url"
    
    mock_stripe_create.assert_called_once()
    call_args, call_kwargs = mock_stripe_create.call_args
    
    assert call_kwargs['mode'] == 'payment'
    assert call_kwargs['success_url'] is not None
    assert call_kwargs['cancel_url'] is not None
    assert call_kwargs['client_reference_id'] == user_id
    assert call_kwargs['line_items'][0]['price_data']['unit_amount'] == 12345

@patch('app.payment_service.stripe.checkout.Session.create')
def test_create_checkout_session_failure(mock_stripe_create):
    """
    Test the behavior when the Stripe API call fails.
    """
    # Arrange
    mock_stripe_create.side_effect = Exception("Stripe API Error")

    flight_offer = {
        'price': {'total': '123.45', 'currency': 'USD'},
        'itineraries': [{'segments': [{'arrival': {'iataCode': 'LHR'}}]}]
    }
    user_id = "whatsapp:+15551234567"

    # Act
    checkout_url = create_checkout_session(flight_offer, user_id)

    # Assert
    assert checkout_url is None 