import json
import sys
from pathlib import Path

from geocode import geocode_location
from collect_climate import get_environment_climate_data
from soilgrids import get_soil_data
from collect_biodiversity import get_biodiversity_data
from collect_land_cover_esa import get_land_cover_esa
from collect_deforestation import get_deforestation_data
from reasoning_engine import build_reasoning_context
from rag_reasoning import attach_evidence


def build_profile_from_coordinates(lat, lon, location_name):
    """
    Same data-fetching logic as build_live_environment_profile(),
    but takes coordinates directly instead of geocoding a place name.
    Used when the JSON input already provides lat/lon (the brief's
    'bonus: geo-coordinates' input type).
    """
    print(f"(Fetching live environmental data for {location_name} — {lat}, {lon}...)")

    soil = get_soil_data(lat, lon, location_name)
    climate = get_environment_climate_data(lat, lon, location_name)
    biodiversity = get_biodiversity_data(lat, lon, location_name)
    land_cover = get_land_cover_esa(lat, lon, location_name)
    deforestation = get_deforestation_data(lat, lon, location_name)

    yearly_loss = deforestation.get("tree_cover_loss_by_year", [])
    total_tree_cover_loss_ha = sum(item["loss_ha"] for item in yearly_loss)

    latest_year, latest_loss_ha = None, None
    if yearly_loss:
        latest = max(yearly_loss, key=lambda x: x["umd_tree_cover_loss__year"])
        latest_year = latest["umd_tree_cover_loss__year"]
        latest_loss_ha = latest["loss_ha"]

    return {
        "location": location_name,
        "coordinates": {"lat": lat, "lon": lon},
        "soil": {
            "organic_carbon_gkg": soil["soil_organic_carbon_gkg"],
            "ph": soil["soil_ph"],
            "moisture_pct": soil["soil_moisture_pct"]
        },
        "climate": {
            "average_temperature_c": climate["avg_temperature_c"],
            "annual_rainfall_mm": climate["annual_rainfall_mm"]
        },
        "pollution": {
            "pm2_5_ug_m3": climate["pollution"]["avg_pm2_5_ug_m3"],
            "pm10_ug_m3": climate["pollution"]["avg_pm10_ug_m3"],
            "no2_ug_m3": climate["pollution"]["avg_no2_ug_m3"]
        },
        "biodiversity": {
            "species_richness": biodiversity["distinct_species_recorded"],
            "distinct_families": biodiversity["distinct_families_recorded"],
            "taxonomic_diversity_shannon": biodiversity["taxonomic_diversity_shannon_index"]
        },
        "land_cover": {
            "classes": land_cover["land_cover_classes_found"],
            "class_count": land_cover["habitat_diversity_count_esa"],
            "class_proportions": land_cover["land_cover_proportions"],
            "habitat_diversity_shannon": land_cover["habitat_diversity_shannon_index"]
        },
        "human_impact": {
            "tree_cover_loss": {
                "total_loss_ha": round(total_tree_cover_loss_ha, 2),
                "latest_year": latest_year,
                "latest_year_loss_ha": round(latest_loss_ha, 2) if latest_loss_ha is not None else None,
                "yearly_loss": yearly_loss
            }
        }
    }


def process_structured_input(payload):
    """
    Accepts a JSON dict shaped like:
    {
      "location_name": "Jaipur, India"      // OR provide lat/lon directly:
      "lat": 26.9,
      "lon": 75.8,
      "farmer_input": {
        "land_use": "monoculture wheat",
        "soil_organic_carbon": null,
        "rainfall": null,
        "region": null
      }
    }
    Runs the exact same pipeline as hybrid_chat.py (signal detection +
    evidence retrieval), but with zero interactive prompts.
    """

    farmer = payload.get("farmer_input", {
        "soil_organic_carbon": None,
        "rainfall": None,
        "land_use": None,
        "region": None
    })

    # --- Resolve location: either given directly, or geocoded from a name ---
    if "lat" in payload and "lon" in payload:
        lat, lon = payload["lat"], payload["lon"]
        location_name = payload.get("location_name", f"({lat}, {lon})")
    elif "location_name" in payload:
        location = geocode_location(payload["location_name"])
        if location is None:
            return {"error": f"Could not resolve location: {payload['location_name']}"}
        lat, lon, location_name = location["lat"], location["lon"], location["resolved_name"]
    else:
        return {"error": "Payload must include either 'lat'+'lon' or 'location_name'"}

    profile = build_profile_from_coordinates(lat, lon, location_name)

    print("\nRunning EcoReason signal detection...")
    reasoning_context = build_reasoning_context(profile, farmer)

    print("Running scientific evidence retrieval...")
    rag_context = attach_evidence(reasoning_context)

    output_path = "data/structured/rag_reasoning_context.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(rag_context, f, indent=2)

    print(f"\nStructured input processed. Context saved to {output_path}")
    return rag_context


if __name__ == "__main__":
    # Two ways to run this:
    # 1. python structured_input.py path/to/input.json
    # 2. python structured_input.py   (uses example_input.json in this folder)

    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        input_path = "example_input.json"

    with open(input_path) as f:
        payload = json.load(f)

    result = process_structured_input(payload)

    if "error" in result:
        print(f"\nERROR: {result['error']}")
    else:
        print("\nDetected signals:")
        for s in result.get("detected_signals", []):
            print(f"  • {s.get('description', '')} [{s.get('severity', '')}]")