import unittest
from app.pdf_service import create_flight_itinerary

class TestPdfService(unittest.TestCase):

    def test_create_flight_itinerary_with_data(self):
        """
        Test that a PDF can be generated with a mock flight offer.
        """
        # A mock flight offer that resembles the Amadeus API response structure
        mock_flight_offer = {
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
            ]
        }
        
        pdf_bytes = create_flight_itinerary(mock_flight_offer)
        
        # Check that the output is bytes
        self.assertIsInstance(pdf_bytes, bytes)
        
        # Check that the PDF is not empty
        self.assertTrue(len(pdf_bytes) > 0)
        
        # A simple "magic number" check for PDF files
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))

    def test_create_flight_itinerary_no_data(self):
        """
        Test that a PDF is still generated when the flight offer is empty.
        """
        pdf_bytes = create_flight_itinerary(None)
        
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 0)
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))
        # You could also check for the "No flight details available" text if needed
        # self.assertIn(b"No flight details available", pdf_bytes)

if __name__ == '__main__':
    unittest.main() 