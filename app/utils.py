import re
from datetime import datetime
import pytz

def _format_duration(iso_duration):
    """Converts ISO 8601 duration (e.g., 'PT8H30M') to a human-readable format."""
    if not iso_duration:
        return ""
    
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', iso_duration)
    if not match:
        return ""
    
    hours, minutes = match.groups(default='0')
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

def _format_flight_offers(flights):
    """Formats flight offers into a string."""
    if not flights:
        return "Sorry, I couldn't find any flights for the given criteria."

    response_lines = ["I found a few options for you:"]
    for i, flight in enumerate(flights[:5], 1):
        itinerary = flight['itineraries'][0]
        price = flight['price']['total']
        
        # Get local time for departure and arrival airports
        dep_time = get_local_time(itinerary['segments'][0]['departure']['iataCode']).strftime('%H:%M')
        arr_time = get_local_time(itinerary['segments'][-1]['arrival']['iataCode']).strftime('%H:%M')
        
        response_lines.append(
            f"{i}. Flight to {itinerary['segments'][-1]['arrival']['iataCode']} "
            f"({dep_time} -> {arr_time}) "
            f"for {price} {flight['price']['currency']}."
        )

    response_lines.append("\nReply with the number of the flight you'd like to book, or say 'no' to start over.")
    return "\n".join(response_lines) 