import pytest
import os
from app.amadeus_service import AmadeusService
import json

@pytest.fixture(scope="module")
def amadeus_service():
    """Fixture to provide an instance of the AmadeusService for integration tests."""
    # Ensure that environment variables are set
    assert os.getenv("AMADEUS_CLIENT_ID"), "AMADEUS_CLIENT_ID not set"
    assert os.getenv("AMADEUS_CLIENT_SECRET"), "AMADEUS_CLIENT_SECRET not set"
    return AmadeusService()

@pytest.mark.integration
def test_search_and_book_flight(amadeus_service):
    """
    Integration test to search for a flight and then book it.
    This test makes real calls to the Amadeus API.
    """
    # 1. Search for flights
    flights = amadeus_service.search_flights(
        originLocationCode='MAD',
        destinationLocationCode='ATH',
        departureDate='2025-07-07',
        adults=1
    )
    assert flights is not None
    assert len(flights) > 0

    # 3. Book the first flight
    first_flight_offer = flights[0]
    
    traveler = {
        "id": "1",
        "dateOfBirth": "1990-01-01",
        "name": {"firstName": "John", "lastName": "Doe"},
        "contact": {
            "emailAddress": "john.doe@example.com",
            "phones": [{"deviceType": "MOBILE", "countryCallingCode": "1", "number": "5555555555"}]
        },
        "documents": [{
            "documentType": "PASSPORT",
            "birthPlace": "New York",
            "issuanceLocation": "New York",
            "issuanceDate": "2018-08-01",
            "number": "000000000",
            "expiryDate": "2028-08-01",
            "issuanceCountry": "US",
            "validityCountry": "US",
            "nationality": "US",
            "holder": True
        }]
    }

    booking_confirmation = amadeus_service.book_flight(first_flight_offer, traveler)

    # 4. Assert the booking was successful
    assert booking_confirmation is not None
    assert 'id' in booking_confirmation
    assert 'associatedRecords' in booking_confirmation
    print(f"Successfully booked flight. Order ID: {booking_confirmation['id']}") 