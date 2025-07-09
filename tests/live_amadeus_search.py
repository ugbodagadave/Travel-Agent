# tests/live_amadeus_search.py
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path to allow importing from 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.amadeus_service import AmadeusService

def run_live_search():
    """
    Performs a live flight search using the Amadeus API.
    """
    print("Loading environment variables from .env file...")
    load_dotenv()
    
    # Check if credentials are loaded
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("\n" + "="*50)
        print("ERROR: AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET not found.")
        print("Please ensure they are set in your .env file in the project root.")
        print("="*50 + "\n")
        return

    print("Amadeus credentials loaded successfully. Initializing service...")
    amadeus_service = AmadeusService()

    # Flight details from the user's chat
    origin_city = "London"
    destination_city = "Paris"
    departure_date = "2025-07-13"
    
    print(f"\nStep 1: Get IATA code for origin: '{origin_city}'")
    origin_iata = amadeus_service.get_iata_code(origin_city)
    print(f"--> Result: {origin_iata}")

    print(f"\nStep 2: Get IATA code for destination: '{destination_city}'")
    destination_iata = amadeus_service.get_iata_code(destination_city)
    print(f"--> Result: {destination_iata}")

    if not origin_iata or not destination_iata:
        print("\nCould not find IATA codes. Aborting flight search.")
        return

    flight_params = {
        'originLocationCode': origin_iata,
        'destinationLocationCode': destination_iata,
        'departureDate': departure_date,
        'adults': 1,
        'nonStop': 'true'
    }
    
    print(f"\nStep 3: Searching for flights with criteria:\n{flight_params}")
    
    try:
        offers = amadeus_service.search_flights(**flight_params)
        
        print("\n" + "="*50)
        if offers:
            print(f"SUCCESS: Found {len(offers)} flight offers.")
            for i, flight in enumerate(offers[:5], 1):
                price = flight['price']['total']
                currency = flight['price']['currency']
                last_ticketing_date = flight.get('lastTicketingDate')
                print(f"  - Option {i}: {price} {currency} (Book by: {last_ticketing_date})")
        else:
            print("NO RESULTS: The search completed but found no flights for the given criteria.")
        print("="*50 + "\n")

    except Exception as e:
        print("\n" + "="*50)
        print(f"ERROR: An exception occurred during the flight search: {e}")
        print("="*50 + "\n")

if __name__ == "__main__":
    run_live_search() 