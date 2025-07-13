from unittest.mock import Mock
from app.utils import _format_flight_offers

def test_format_flight_offers_direct_flight():
    # Mock AmadeusService
    mock_amadeus_service = Mock()
    mock_amadeus_service.get_airport_name.side_effect = lambda code: {
        "LHR": "London Heathrow",
        "JFK": "New York JFK"
    }.get(code, code)

    mock_flights = [
        {
            "airlineName": "Test Airline",
            "itineraries": [
                {
                    "duration": "PT5H",
                    "segments": [
                        {
                            "departure": {"iataCode": "LHR", "at": "2024-12-25T09:00:00"},
                            "arrival": {"iataCode": "JFK"}
                        }
                    ]
                }
            ],
            "price": {"total": "500.00", "currency": "USD"},
            "travelerPricings": [{"fareDetailsBySegment": [{"cabin": "ECONOMY"}]}]
        }
    ]
    formatted_string = _format_flight_offers(mock_flights, mock_amadeus_service)
    
    # Assert the new multi-line format
    assert "1. London Heathrow (LHR) to New York JFK (JFK) for 500.00 USD" in formatted_string
    assert "Departs at: 09:00 AM" in formatted_string
    assert "Duration: 5h 0m [Direct - Economy]" in formatted_string
    assert "Airline: Test Airline" in formatted_string


def test_format_flight_offers_with_stopover():
    """
    This test ensures that for a multi-segment flight, the final destination
    is shown, not the stopover airport.
    """
    # Mock AmadeusService
    mock_amadeus_service = Mock()
    mock_amadeus_service.get_airport_name.side_effect = lambda code: {
        "LHR": "London Heathrow",
        "IST": "Istanbul Airport",
        "JFK": "New York JFK"
    }.get(code, code)

    mock_flights = [
        {
            "airlineName": "Test Airline",
            "itineraries": [
                {
                    "duration": "PT12H15M",
                    "segments": [
                        {
                            "departure": {"iataCode": "LHR", "at": "2024-12-25T11:00:00"},
                            "arrival": {"iataCode": "IST"}
                        },
                        {
                            "departure": {"iataCode": "IST", "at": "2024-12-25T15:00:00"},
                            "arrival": {"iataCode": "JFK"}
                        }
                    ]
                }
            ],
            "price": {"total": "750.00", "currency": "EUR"},
            "travelerPricings": [{"fareDetailsBySegment": [{"cabin": "BUSINESS"}]}]
        }
    ]
    formatted_string = _format_flight_offers(mock_flights, mock_amadeus_service)
    
    # Assert the new multi-line format
    assert "1. London Heathrow (LHR) to New York JFK (JFK) for 750.00 EUR" in formatted_string
    assert "Departs at: 11:00 AM" in formatted_string
    assert "Duration: 12h 15m [1 stop(s) - Business]" in formatted_string
    assert "Airline: Test Airline" in formatted_string


def test_format_flight_offers_no_flights():
    # Mock AmadeusService is needed for the call signature
    mock_amadeus_service = Mock()
    formatted_string = _format_flight_offers([], mock_amadeus_service)
    assert "Sorry, I couldn't find any flights" in formatted_string

def test_format_flight_offers_with_full_details():
    # Mock AmadeusService
    mock_amadeus_service = Mock()
    mock_amadeus_service.get_airport_name.side_effect = lambda code: {
        "CDG": "Charles de Gaulle",
        "JFK": "New York JFK"
    }.get(code, code)

    mock_flights = [
        {
            "airlineName": "Test Airline",
            "itineraries": [
                {
                    "duration": "PT8H30M",
                    "segments": [
                        {
                            "departure": {"iataCode": "CDG", "at": "2024-12-25T10:30:00"},
                            "arrival": {"iataCode": "JFK"}
                        }
                    ]
                }
            ],
            "price": {"total": "1200.50", "currency": "USD"},
            "travelerPricings": [{"fareDetailsBySegment": [{"cabin": "FIRST"}]}]
        }
    ]
    formatted_string = _format_flight_offers(mock_flights, mock_amadeus_service)

    # Assert the new multi-line format
    assert "1. Charles de Gaulle (CDG) to New York JFK (JFK) for 1200.50 USD" in formatted_string
    assert "Departs at: 10:30 AM" in formatted_string
    assert "Duration: 8h 30m [Direct - First]" in formatted_string
    assert "Airline: Test Airline" in formatted_string

def test_format_flight_offers_new_format():
    """
    Tests the new multi-line format for flight offers.
    """
    # Mock AmadeusService
    mock_amadeus_service = Mock()
    mock_amadeus_service.get_airport_name.side_effect = lambda code: {
        "LGW": "GATWICK",
        "JFK": "JOHN F KENNEDY INTL"
    }.get(code, code)

    mock_flights = [
        {
            "airlineName": "A.P.G. DISTRIBUTION SYSTEM",
            "itineraries": [
                {
                    "duration": "PT7H50M",
                    "segments": [
                        {
                            "departure": {"iataCode": "LGW", "at": "2024-12-25T13:05:00"},
                            "arrival": {"iataCode": "JFK"}
                        }
                    ]
                }
            ],
            "price": {"total": "303.08", "currency": "EUR"},
            "travelerPricings": [{"fareDetailsBySegment": [{"cabin": "PREMIUM_ECONOMY"}]}]
        }
    ]
    formatted_string = _format_flight_offers(mock_flights, mock_amadeus_service)
    
    expected_lines = [
        "1. GATWICK (LGW) to JOHN F KENNEDY INTL (JFK) for 303.08 EUR",
        "Departs at: 01:05 PM",
        "Duration: 7h 50m [Direct - Premium Economy]",
        "Airline: A.P.G. DISTRIBUTION SYSTEM"
    ]
    
    actual_lines = [line.strip() for line in formatted_string.split('\n') if line.strip()]

    # We are looking for the formatted block, so we'll check if the expected lines are a subset of the actual lines
    assert "I found a few options for you:" in actual_lines
    
    # Clean actual_lines to only contain the flight offer
    flight_offer_lines = [line for line in actual_lines if "Reply with the number" not in line and "I found a few options" not in line]

    # The new implementation adds an extra empty line between offers, so we filter that out
    flight_offer_lines = [line for line in flight_offer_lines if line]
    
    assert expected_lines == flight_offer_lines 