import requests
import json

def get_land_cover(lat, lon, location_name, radius_m=2000):
    """
    Queries OpenStreetMap (via Overpass API) for land cover types
    within radius_m meters of a point. Returns the list of distinct
    types found (= land use / land cover) and how many distinct
    types there are (= a simple habitat diversity score).
    """
    overpass_url = "https://overpass-api.de/api/interpreter"

    # This query asks for anything tagged "landuse" or "natural"
    # within radius_m meters of our point.
    query = f"""
    [out:json][timeout:25];
    (
      way["landuse"](around:{radius_m},{lat},{lon});
      way["natural"](around:{radius_m},{lat},{lon});
    );
    out tags;
    """

    headers = {
    "User-Agent": "EcoReason-Hackathon-Project (student project, contact: anujajp.05@gmail.com)"
}
    response = requests.post(overpass_url, data={"data": query}, headers=headers)

    if not response.ok:
        raise Exception(f"Overpass request failed (status {response.status_code})")

    data = response.json()

    cover_types = set()
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        if "landuse" in tags:
            cover_types.add(f"landuse:{tags['landuse']}")
        if "natural" in tags:
            cover_types.add(f"natural:{tags['natural']}")

    return {
        "location": location_name,
        "lat": lat,
        "lon": lon,
        "radius_m": radius_m,
        "land_cover_types_found": sorted(cover_types),
        "habitat_diversity_count": len(cover_types)  # distinct types = diversity score
    }


if __name__ == "__main__":
    locations = [
        {"name": "Semi-arid India example", "lat": 26.9, "lon": 75.8},
        {"name": "Sub-Saharan Africa example", "lat": -1.3, "lon": 36.8},
    ]

    results = [get_land_cover(loc["lat"], loc["lon"], loc["name"]) for loc in locations]

    with open("data/structured/land_cover_data.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Done! Saved to data/structured/land_cover_data.json")
    print(json.dumps(results, indent=2))