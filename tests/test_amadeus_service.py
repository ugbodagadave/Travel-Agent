import pytest
from unittest.mock import MagicMock, patch
from app.amadeus_service import AmadeusService, ResponseError, Location

@pytest.fixture
def mock_amadeus_client():
    """Fixture to provide a mocked Amadeus client instance."""
    with patch('app.amadeus_service.Client') as MockClient:
        mock_instance = MockClient.return_value
        yield mock_instance

def test_get_iata_code_success(mock_amadeus_client):
    """ Test successful IATA code lookup. """
    mock_response = MagicMock()
    mock_response.data = [{'iataCode': 'LHR'}]
    mock_amadeus_client.reference_data.locations.get.return_value = mock_response

    service = AmadeusService()
    iata_code = service.get_iata_code('London')
    
    mock_amadeus_client.reference_data.locations.get.assert_called_once_with(
        keyword='London',
        subType='CITY,AIRPORT'
    )
    assert iata_code == 'LHR'

def test_get_iata_code_not_found(mock_amadeus_client):
    """ Test IATA code lookup when no code is found. """
    mock_response = MagicMock()
    mock_response.data = [{'name': 'Nowhere Land'}] # No iataCode key
    mock_amadeus_client.reference_data.locations.get.return_value = mock_response

    service = AmadeusService()
    iata_code = service.get_iata_code('Nowhere')
    
    assert iata_code is None

def test_get_airport_name_success_and_cached(mock_amadeus_client):
    """ Test successful airport name lookup and that the result is cached. """
    mock_response = MagicMock()
    mock_response.data = [{'name': 'HEATHROW'}]
    mock_amadeus_client.reference_data.locations.get.return_value = mock_response

    service = AmadeusService()
    
    # First call - should trigger API call
    name = service.get_airport_name('LHR')
    assert name == 'HEATHROW'
    mock_amadeus_client.reference_data.locations.get.assert_called_once_with(
        keyword='LHR',
        subType=Location.AIRPORT
    )
    
    # Second call - should use cache, no new API call
    name2 = service.get_airport_name('LHR')
    assert name2 == 'HEATHROW'
    mock_amadeus_client.reference_data.locations.get.assert_called_once() # Still called only once

def test_get_airport_name_api_failure_and_fallback(mock_amadeus_client):
    """ Test that the function falls back to the IATA code on API error and caches the failure. """
    mock_amadeus_client.reference_data.locations.get.side_effect = ResponseError(MagicMock())

    service = AmadeusService()

    # First call - should fail and return the code
    name = service.get_airport_name('BADCODE')
    assert name == 'BADCODE'
    mock_amadeus_client.reference_data.locations.get.assert_called_once_with(
        keyword='BADCODE',
        subType=Location.AIRPORT
    )

    # Second call - should use cache and not call the API again
    name2 = service.get_airport_name('BADCODE')
    assert name2 == 'BADCODE'
    mock_amadeus_client.reference_data.locations.get.assert_called_once() # Still called only once

def test_search_flights_success(mock_amadeus_client):
    """ Test successful flight search. """
    mock_response = MagicMock()
    mock_response.data = [{'id': 'flight1'}, {'id': 'flight2'}]
    mock_amadeus_client.shopping.flight_offers_search.get.return_value = mock_response

    search_params = {
        'originLocationCode': 'JFK',
        'destinationLocationCode': 'LAX',
        'departureDate': '2024-12-25',
        'adults': 1
    }

    service = AmadeusService()
    flights = service.search_flights(**search_params)
    
    mock_amadeus_client.shopping.flight_offers_search.get.assert_called_once_with(**search_params)
    assert len(flights) == 2
    assert flights[0]['id'] == 'flight1'

def test_search_flights_api_error(mock_amadeus_client):
    """ Test flight search with an API error. """
    mock_amadeus_client.shopping.flight_offers_search.get.side_effect = ResponseError(MagicMock())
    
    service = AmadeusService()
    flights = service.search_flights(originLocationCode='JFK', destinationLocationCode='LAX', departureDate='2024-12-25', adults=1)

    assert flights is None

def test_book_flight_success(mock_amadeus_client):
    """ Test successful flight booking. """
    # Mock for the pricing call
    mock_pricing_response = MagicMock()
    mock_pricing_response.data = {'flightOffers': [{'id': 'priced_offer'}]}
    mock_amadeus_client.shopping.flight_offers.pricing.post.return_value = mock_pricing_response
    
    # Mock for the final booking call
    mock_order_response = MagicMock()
    mock_order_response.data = {'id': 'booking_confirmation'}
    mock_amadeus_client.post.return_value = mock_order_response

    flight_offer = {'id': 'original_offer'}
    traveler = {'id': '1', 'name': {'firstName': 'John', 'lastName': 'Doe'}}

    service = AmadeusService()
    booking_confirmation = service.book_flight(flight_offer, traveler)

    # Assert pricing call
    mock_amadeus_client.shopping.flight_offers.pricing.post.assert_called_once_with(flight_offer)
    
    # Assert booking call
    expected_order_body = {
        'data': {
            'type': 'flight-order',
            'flightOffers': [{'id': 'priced_offer'}],
            'travelers': [traveler]
        }
    }
    mock_amadeus_client.post.assert_called_once_with('/v1/booking/flight-orders', expected_order_body)
    
    assert booking_confirmation == {'id': 'booking_confirmation'}

def test_book_flight_pricing_error(mock_amadeus_client):
    """ Test flight booking failure at the pricing stage. """
    mock_amadeus_client.shopping.flight_offers.pricing.post.side_effect = ResponseError(MagicMock())

    service = AmadeusService()
    result = service.book_flight({'id': 'offer1'}, {'id': 'traveler1'})
    
    assert result is None
    mock_amadeus_client.post.assert_not_called()

def test_book_flight_order_error(mock_amadeus_client):
    """ Test flight booking failure at the final ordering stage. """
    mock_pricing_response = MagicMock()
    mock_pricing_response.data = {'flightOffers': [{'id': 'priced_offer'}]}
    mock_amadeus_client.shopping.flight_offers.pricing.post.return_value = mock_pricing_response
    
    mock_amadeus_client.post.side_effect = ResponseError(MagicMock())

    service = AmadeusService()
    result = service.book_flight({'id': 'offer1'}, {'id': 'traveler1'})

    assert result is None 