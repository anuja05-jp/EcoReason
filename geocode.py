import requests

def geocode_location(place_name):
    """
    Converts a place name (city, region) into coordinates.
    Returns None if nothing found.
    """
    # Open-Meteo's geocoder wants a plain place name, not "City, Country"
    clean_name = place_name.split(",")[0].strip()

    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": clean_name, "count": 1}

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()


    results = data.get("results")
    if not results:
        return None

    top = results[0]
    return {
        "resolved_name": top.get("name"),
        "country": top.get("country"),
        "lat": top.get("latitude"),
        "lon": top.get("longitude")
    }