import os
from amadeus import Client, ResponseError

class AmadeusService:
    def __init__(self):
        self.client = Client(
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
            response = self.client.reference_data.locations.get(
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

    def search_flights(self, origin_iata, destination_iata, departure_date, return_date=None, adults=1):
        """
        Search for flight offers.
        """
        try:
            params = {
                'originLocationCode': origin_iata,
                'destinationLocationCode': destination_iata,
                'departureDate': departure_date,
                'adults': adults,
                'nonStop': 'true',
                'currencyCode': 'USD',
                'max': 5 # Limit to 5 results for now
            }
            if return_date:
                params['returnDate'] = return_date

            response = self.client.shopping.flight_offers_search.get(**params)
            return response.data
        except ResponseError as error:
            print(f"Amadeus API Error (search_flights): {error}")
            return None 