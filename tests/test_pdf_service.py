import pytest
from unittest.mock import patch
from app.pdf_service import create_flight_itinerary
from pypdf import PdfReader
import io

@pytest.fixture
def mock_flight_offer_with_class():
    """Provides a mock flight offer including travel class details."""
    return {
        'price': {'total': '250.00', 'currency': 'EUR'},
        'itineraries': [
            {
                'segments': [
                    {
                        'departure': {'iataCode': 'JFK', 'at': '2024-10-01T10:00:00'},
                        'arrival': {'iataCode': 'LHR', 'at': '2024-10-01T22:00:00'}
                    }
                ]
            }
        ],
        'travelerPricings': [{'fareDetailsBySegment': [{'cabin': 'BUSINESS'}]}]
    }

def test_create_flight_itinerary_contains_travel_class(mock_flight_offer_with_class):
    """
    Tests that the generated PDF contains the correct travel class.
    """
    pdf_bytes = create_flight_itinerary(mock_flight_offer_with_class)
    
    # Use PyPDF2 to read the content of the generated PDF
    pdf_file = io.BytesIO(pdf_bytes)
    reader = PdfReader(pdf_file)
    page = reader.pages[0]
    text = page.extract_text()
    
    # Assert that the travel class is present in the PDF text
    assert "Class: Business" in text
    assert "Total Price: 250.00 EUR" in text

def test_create_flight_itinerary_no_data():
    """
    Tests that a PDF is still generated when the flight offer is None.
    """
    pdf_bytes = create_flight_itinerary(None)
    
    pdf_file = io.BytesIO(pdf_bytes)
    reader = PdfReader(pdf_file)
    page = reader.pages[0]
    text = page.extract_text()
    
    assert "No flight details available." in text 