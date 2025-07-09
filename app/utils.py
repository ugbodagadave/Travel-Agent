import re
from datetime import datetime

def _format_duration(iso_duration):
    """Converts ISO 8601 duration (e.g., 'PT8H30M') to a human-readable format."""
    if not iso_duration:
        return ""
    
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', iso_duration)
    if not match:
        return ""
    
    hours, minutes = match.groups(default='0')
    return f"{hours}h {minutes}m"

def _format_flight_offers(flights, amadeus_service):
    """Formats flight offers into a string."""
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

        response_lines.append(
            f"{i}. {origin_name} ({origin_code}) to {destination_name} ({destination_code}) for {price} {flight['price']['currency']}.\n"
            f"   Departs at: {departure_time}, Duration: {duration}, {stopover_text}"
        )

    response_lines.append("\nReply with the number of the flight you'd like to book, or say 'no' to start over.")
    return "\n".join(response_lines) 