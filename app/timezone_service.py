from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# Initialize the geolocator and timezone finder
geolocator = Nominatim(user_agent="ai-travel-agent")
tf = TimezoneFinder()

def get_timezone_for_city(city_name: str) -> str | None:
    """
    Finds the IANA timezone name for a given city.
    Returns None if the city cannot be found or has no timezone.
    """
    try:
        # Get the location (latitude, longitude) of the city
        location = geolocator.geocode(city_name)
        if location:
            # Find the timezone for that location
            timezone = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            return timezone
    except Exception as e:
        print(f"Error finding timezone for {city_name}: {e}")
    
    return None 