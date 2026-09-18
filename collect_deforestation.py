import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()  # reads your .env file
API_KEY = os.getenv("GFW_API_KEY")

def get_deforestation_data(lat, lon, location_name, box_degrees=0.05):
    """
    Queries GFW's tree cover loss dataset for a small box around a point,
    asking: how many hectares of tree cover were lost, broken down by year?
    """
    url = "https://data-api.globalforestwatch.org/dataset/umd_tree_cover_loss/latest/query"

    # Build a small square polygon around our point (GeoJSON format)
    min_lon, max_lon = lon - box_degrees, lon + box_degrees
    min_lat, max_lat = lat - box_degrees, lat + box_degrees

    geometry = {
        "type": "Polygon",
        "coordinates": [[
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat]
        ]]
    }

    payload = {
        "sql": "SELECT umd_tree_cover_loss__year, SUM(area__ha) as loss_ha FROM data GROUP BY umd_tree_cover_loss__year",
        "geometry": geometry
    }

    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)


    response.raise_for_status()
    data = response.json()

    return {
        "location": location_name,
        "lat": lat,
        "lon": lon,
        "tree_cover_loss_by_year": data.get("data", [])
    }


if __name__ == "__main__":
    locations = [
        {"name": "Mumbai", "lat": 19.07283, "lon": 72.88261},
        {"name": "Semi-arid India example", "lat": 26.9, "lon": 75.8},
        {"name": "Sub-Saharan Africa example", "lat": -1.3, "lon": 36.8},
    ]

    results = [
        get_deforestation_data(
            loc["lat"],
            loc["lon"],
            loc["name"]
        )
        for loc in locations
    ]

    with open("data/structured/deforestation_data.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Done! Saved to data/structured/deforestation_data.json")