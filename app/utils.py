import re
from datetime import datetime
import pytz

def _format_duration(iso_duration):
    """Formats an ISO 8601 duration string into a more readable format."""
    if not iso_duration or not iso_duration.startswith('PT'):
        return ""
    
    # Simple regex to parse PTxHxM format
    match = re.match(r'PT(\d+)H(?:(\d+)M)?', iso_duration)
    if not match:
        return ""
        
    hours, minutes = match.groups(default='0')
    hours, minutes = int(hours), int(minutes)
    
    return f"{hours}h {minutes}m"

def get_local_time(iata_code):
    """
    Get the current local time for a given IATA code.
    This is a simplified example; a real implementation would be more robust.
    """
    # This is a very basic mapping. A real app would use a more comprehensive library.
    timezone_map = {
        "JFK": "America/New_York",
        "LHR": "Europe/London",
        "CDG": "Europe/Paris",
        "LAX": "America/Los_Angeles",
        # ... add other common IATA codes
    }
    
    timezone_name = timezone_map.get(iata_code, "UTC")
    local_tz = pytz.timezone(timezone_name)
    return datetime.now(local_tz)

def sanitize_filename(name):
    """
    Sanitizes a string to be a valid filename.
    Replaces spaces with underscores and removes disallowed characters.
    """
    if not name:
        return "traveler"
    
    # Replace spaces with underscores
    s = name.replace(" ", "_")
    # Remove characters that are not letters, numbers, underscores, or hyphens
    s = re.sub(r'(?u)[^-\w.]', '', s)
    return s

def _format_flight_offers(flights, amadeus_service):
    """Formats flight offers into a string with full details."""
    if not flights:
        return "Sorry, I couldn't find any flights for the given criteria."

    response_lines = ["I found a few options for you:"]
    for i, flight in enumerate(flights[:5], 1):
        itinerary = flight['itineraries'][0]
        price = flight['price']['total']
        
        first_segment = itinerary['segments'][0]
        last_segment = itinerary['segments'][-1]

        origin_code = first_segment['departure']['iataCode']
        destination_code = last_segment['arrival']['iataCode']
        
        origin_name = amadeus_service.get_airport_name(origin_code)
        destination_name = amadeus_service.get_airport_name(destination_code)

        departure_time = datetime.fromisoformat(first_segment['departure']['at']).strftime('%I:%M %p')
        duration = _format_duration(itinerary.get('duration', ''))
        
        num_stops = len(itinerary['segments']) - 1
        stopover_text = "Direct" if num_stops == 0 else f"{num_stops} stop(s)"
        
        # Get travel class from the first traveler pricing details
        travel_class = "ECONOMY" # Default
        try:
            # The structure is nested, so we use .get() to avoid errors if a key is missing
            travel_class = flight.get('travelerPricings', [{}])[0].get('fareDetailsBySegment', [{}])[0].get('class', 'ECONOMY')
        except (IndexError, KeyError):
            pass # Keep the default
            
        class_text = f"[{stopover_text} - {travel_class.replace('_', ' ').title()}]"

        airline_name = flight.get('airlineName', 'Unknown Airline')

        # Format the flight details into a multi-line string
        response_lines.append(
            f"{i}. {origin_name} ({origin_code}) to {destination_name} ({destination_code}) for {price} {flight['price']['currency']}\n"
            f"Departs at: {departure_time}\n"
            f"Duration: {duration} {class_text}\n"
            f"Airline: {airline_name}\n"
        )

    response_lines.append("Reply with the number of the flight you'd like to book, or say 'no' to start over.")
    return "\n".join(response_lines) 