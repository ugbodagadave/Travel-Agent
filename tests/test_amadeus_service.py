import pytest
from unittest.mock import MagicMock, patch
from app.amadeus_service import AmadeusService

@pytest.fixture
def amadeus_service():
    """ Fixture to initialize AmadeusService with a mocked client. """
    with patch('amadeus.Client') as MockClient:
        # We don't need to mock the client instance details here
        # as we will mock the specific API call responses in each test.
        service = AmadeusService()
        # Replace the real client with a MagicMock instance for testing
        service.client = MagicMock()
        yield service

def test_get_iata_code_success(amadeus_service):
    """ Test successful IATA code lookup. """
    mock_response = MagicMock()
    mock_response.data = [{'iataCode': 'LHR'}]
    amadeus_service.client.reference_data.locations.get.return_value = mock_response

    iata_code = amadeus_service.get_iata_code('London')
    
    amadeus_service.client.reference_data.locations.get.assert_called_once_with(
        keyword='London',
        subType='CITY,AIRPORT'
    )
    assert iata_code == 'LHR'

def test_get_iata_code_not_found(amadeus_service):
    """ Test IATA code lookup when no code is found. """
    mock_response = MagicMock()
    mock_response.data = [{'name': 'Nowhere Land'}] # No iataCode key
    amadeus_service.client.reference_data.locations.get.return_value = mock_response

    iata_code = amadeus_service.get_iata_code('Nowhere')
    
    assert iata_code is None

def test_search_flights_one_way_success(amadeus_service):
    """ Test successful one-way flight search. """
    mock_response = MagicMock()
    mock_response.data = [{'id': 'flight1'}, {'id': 'flight2'}]
    amadeus_service.client.shopping.flight_offers_search.get.return_value = mock_response

    flights = amadeus_service.search_flights(
        origin_iata='JFK',
        destination_iata='LAX',
        departure_date='2024-12-25',
        adults=1
    )
    
    expected_params = {
        'originLocationCode': 'JFK',
        'destinationLocationCode': 'LAX',
        'departureDate': '2024-12-25',
        'adults': 1,
        'currencyCode': 'USD',
        'max': 5
    }
    amadeus_service.client.shopping.flight_offers_search.get.assert_called_once_with(**expected_params)
    assert len(flights) == 2
    assert flights[0]['id'] == 'flight1'

def test_search_flights_round_trip_success(amadeus_service):
    """ Test successful round-trip flight search. """
    mock_response = MagicMock()
    mock_response.data = [{'id': 'flight_round'}]
    amadeus_service.client.shopping.flight_offers_search.get.return_value = mock_response

    flights = amadeus_service.search_flights(
        origin_iata='SFO',
        destination_iata='MIA',
        departure_date='2025-01-10',
        return_date='2025-01-20',
        adults=2
    )

    expected_params = {
        'originLocationCode': 'SFO',
        'destinationLocationCode': 'MIA',
        'departureDate': '2025-01-10',
        'returnDate': '2025-01-20',
        'adults': 2,
        'currencyCode': 'USD',
        'max': 5
    }
    amadeus_service.client.shopping.flight_offers_search.get.assert_called_once_with(**expected_params)
    assert len(flights) == 1
    assert flights[0]['id'] == 'flight_round'

def test_search_flights_api_error(amadeus_service):
    # This test case is not provided in the original file or the code block
    # It's assumed to exist as it's called in the original file
    pass 