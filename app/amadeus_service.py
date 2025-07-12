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
        self.airport_cache = {}
        self.airline_cache = {}

    def get_airline_name(self, airline_code):
        """
        Get the full airline name for a given IATA code.
        Uses a simple in-memory cache to avoid repeated API calls.
        """
        if airline_code in self.airline_cache:
            return self.airline_cache[airline_code]
        
        try:
            response = self.amadeus.reference_data.airlines.get(airlineCodes=airline_code)
            if response.data:
                name = response.data[0]['businessName']
                self.airline_cache[airline_code] = name
                return name
            else:
                self.airline_cache[airline_code] = airline_code # Cache failure
                return airline_code
        except ResponseError:
            self.airline_cache[airline_code] = airline_code # Cache failure
            return airline_code

    def get_airport_name(self, iata_code):
        """
        Get the full airport name for a given IATA code.
        Uses a simple in-memory cache to avoid repeated API calls.
        """
        if iata_code in self.airport_cache:
            return self.airport_cache[iata_code]
        
        try:
            # Use the locations API to search for the airport by its IATA code.
            response = self.amadeus.reference_data.locations.get(
                keyword=iata_code,
                subType=Location.AIRPORT
            )
            
            # If we get data back, extract the name, cache it, and return it.
            if response.data:
                name = response.data[0].get('name', iata_code)
                self.airport_cache[iata_code] = name
                return name
            else:
                # If no data, cache the failure (using the code itself) and return.
                self.airport_cache[iata_code] = iata_code
                return iata_code
        except ResponseError:
            # If the API fails, cache the failure and return the code as a fallback.
            self.airport_cache[iata_code] = iata_code
            return iata_code

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