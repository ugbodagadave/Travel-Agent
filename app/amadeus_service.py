import os
from amadeus import Client, ResponseError, Location
from amadeus.client.errors import ClientError
import json

class AmadeusService:
    def __init__(self):
        self.amadeus = Client(
            client_id=os.getenv("AMADEUS_CLIENT_ID"),
            client_secret=os.getenv("AMADEUS_CLIENT_SECRET"),
            hostname='production' if os.getenv("APP_ENV") == "production" else "test"
        )

    def get_iata_code(self, city_name):
        """
        Get the IATA code for a given city name.
        Returns the first airport IATA code found.
        """
        try:
            response = self.amadeus.reference_data.locations.get(
                keyword=city_name,
                subType='CITY,AIRPORT'
            )
            # Find the first entry with an IATA code
            for location in response.data:
                if 'iataCode' in location:
                    return location['iataCode']
            return None
        except ResponseError as error:
            print(f"Amadeus API Error (get_iata_code): {error}")
            return None

    def search_flights(self, **kwargs):
        """
        Searches for flights with the given parameters.
        :param kwargs: Dictionary of parameters for the flight search.
                       (e.g., originLocationCode, destinationLocationCode, departureDate, adults)
        :return: A list of flight offers.
        """
        try:
            print(f"DEBUG: Amadeus search_flights params: {kwargs}") # DEBUG PRINT
            response = self.amadeus.shopping.flight_offers_search.get(**kwargs)
            return response.data
        except ResponseError as error:
            # Log the full error for debugging, but return None to prevent crash
            print(f"Amadeus API Error (search_flights): {error.response.result if hasattr(error, 'response') else error}")
            return None

    def book_flight(self, flight_offer, traveler):
        """
        Confirms the flight price and books it.
        :param flight_offer: The flight offer object from the search.
        :param traveler: The traveler information object.
        :return: The booking confirmation details or None if booking fails.
        """
        try:
            # First, confirm the price of the flight offer
            price_confirm_response = self.amadeus.shopping.flight_offers.pricing.post(
                flight_offer
            )
            priced_offer = price_confirm_response.data['flightOffers'][0]

            # Then, book the flight with the traveler's information
            flight_order_body = {
                'data': {
                    'type': 'flight-order',
                    'flightOffers': [priced_offer],
                    'travelers': [traveler]
                }
            }

            # Use the generic client post method to send the raw body
            order_response = self.amadeus.post('/v1/booking/flight-orders', flight_order_body)
            
            return order_response.data
        except ResponseError as error:
            # We can log the full error for debugging
            # print(f"Amadeus booking failed. Response: {error.response.result}")
            return None