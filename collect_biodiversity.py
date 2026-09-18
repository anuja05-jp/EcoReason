import requests
import json
import math

def get_biodiversity_data(lat, lon, location_name):
    """
    Fetches species richness AND taxonomic diversity for a location.
    - Species richness = how many distinct species were recorded
    - Taxonomic diversity = how spread out those species are across
      different families (a proxy for ecosystem variety, not just count)
    """
    url = "https://api.gbif.org/v1/occurrence/search"
    params = {
        "decimalLatitude": f"{lat - 0.5},{lat + 0.5}",
        "decimalLongitude": f"{lon - 0.5},{lon + 0.5}",
        "limit": 300
    }
    response = requests.get(url, params=params)
    data = response.json()

    species_set = set()
    family_counts = {}  # counts how many records belong to each family

    for record in data.get("results", []):
        species = record.get("species")
        family = record.get("family")

        if species:
            species_set.add(species)

        if family:
            family_counts[family] = family_counts.get(family, 0) + 1

    # --- Shannon diversity index across families ---
    # This is a standard ecology formula: it's high when records are spread
    # evenly across MANY families, and low when one family dominates.
    total_records = sum(family_counts.values())
    shannon_index = 0.0

    if total_records > 0:
        for count in family_counts.values():
            proportion = count / total_records
            shannon_index -= proportion * math.log(proportion)

    return {
        "location": location_name,
        "lat": lat,
        "lon": lon,
        "distinct_species_recorded": len(species_set),
        "distinct_families_recorded": len(family_counts),
        "taxonomic_diversity_shannon_index": round(shannon_index, 3)
    }


if __name__ == "__main__":
    locations = [
        {"name": "Semi-arid India example", "lat": 26.9, "lon": 75.8},
        {"name": "Sub-Saharan Africa example", "lat": -1.3, "lon": 36.8},
    ]

    results = [get_biodiversity_data(loc["lat"], loc["lon"], loc["name"]) for loc in locations]

    with open("data/structured/biodiversity_data.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Done! Saved to data/structured/biodiversity_data.json")
    print(json.dumps(results, indent=2))