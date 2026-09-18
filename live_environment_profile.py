import json
from geocode import geocode_location
from collect_climate import get_environment_climate_data
from soilgrids import get_soil_data
from collect_biodiversity import get_biodiversity_data
from collect_land_cover_esa import get_land_cover_esa
from collect_deforestation import get_deforestation_data


def build_live_environment_profile(place_name):
    """
    Same shape as your build_environment_profile(), but instead of
    reading pre-saved JSON for a hardcoded location, it geocodes a
    place name typed by the user and fetches everything live.
    """
    location = geocode_location(place_name)
    if location is None:
        return None

    lat, lon, resolved_name = location["lat"], location["lon"], location["resolved_name"]
    print(f"(Fetching live environmental data for {resolved_name} — {lat}, {lon}...)")

    soil = get_soil_data(lat, lon, resolved_name)
    climate = get_environment_climate_data(lat, lon, resolved_name)
    biodiversity = get_biodiversity_data(lat, lon, resolved_name)
    land_cover = get_land_cover_esa(lat, lon, resolved_name)
    deforestation = get_deforestation_data(lat, lon, resolved_name)

    yearly_loss = deforestation.get("tree_cover_loss_by_year", [])
    total_tree_cover_loss_ha = sum(item["loss_ha"] for item in yearly_loss)

    latest_year, latest_loss_ha = None, None
    if yearly_loss:
        latest = max(yearly_loss, key=lambda x: x["umd_tree_cover_loss__year"])
        latest_year = latest["umd_tree_cover_loss__year"]
        latest_loss_ha = latest["loss_ha"]

    return {
        "location": resolved_name,
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