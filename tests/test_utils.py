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
            "price": {"total": "500.00", "currency": "USD"}
        }
    ]
    formatted_string = _format_flight_offers(mock_flights, mock_amadeus_service)
    
    # Assert the exact format including bolding and spacing
    expected_main_line = "*1. Test Airline: London Heathrow (LHR) to New York JFK (JFK) for 500.00 USD.*"
    expected_details_line = "   Departs at: 09:00 AM, Duration: 5h 0m, Direct"
    
    assert expected_main_line in formatted_string
    assert expected_details_line in formatted_string
    # Check for the newline that separates entries
    assert f"{expected_details_line}\n\n" in formatted_string


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
            "price": {"total": "750.00", "currency": "EUR"}
        }
    ]
    formatted_string = _format_flight_offers(mock_flights, mock_amadeus_service)
    
    expected_main_line = "*1. Test Airline: London Heathrow (LHR) to New York JFK (JFK) for 750.00 EUR.*"
    expected_details_line = "   Departs at: 11:00 AM, Duration: 12h 15m, 1 stop(s)"

    assert expected_main_line in formatted_string
    assert expected_details_line in formatted_string
    assert f"{expected_details_line}\n\n" in formatted_string


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
            "price": {"total": "1200.50", "currency": "USD"}
        }
    ]
    formatted_string = _format_flight_offers(mock_flights, mock_amadeus_service)

    expected_main_line = "*1. Test Airline: Charles de Gaulle (CDG) to New York JFK (JFK) for 1200.50 USD.*"
    expected_details_line = "   Departs at: 10:30 AM, Duration: 8h 30m, Direct"

    assert expected_main_line in formatted_string
    assert expected_details_line in formatted_string
    assert f"{expected_details_line}\n\n" in formatted_string 