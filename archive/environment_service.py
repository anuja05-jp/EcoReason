import json

from geocode import geocode_location
from soilgrids import get_soil_data
from collect_climate import get_environment_climate_data
from collect_biodiversity import get_biodiversity_data
from collect_land_cover_esa import get_land_cover_esa
from collect_deforestation import get_deforestation_data


def get_environment_profile(location_name):
    """
    Convert a user-provided location into a unified environmental profile.

    Pipeline:
        Location
          ↓
        Geocoding
          ↓
        SoilGrids
        Open-Meteo
        GBIF
        ESA WorldCover
        Global Forest Watch
          ↓
        Unified environmental profile
    """

    print(f"\nResolving location: {location_name}")

    # ---------------------------------------------------------
    # 1. GEOCODE LOCATION
    # ---------------------------------------------------------

    location = geocode_location(location_name)

    if not location:
        raise ValueError(
            f"Could not find the location '{location_name}'. "
            "Please provide a more specific location."
        )

    resolved_name = location["resolved_name"]
    country = location["country"]
    lat = location["lat"]
    lon = location["lon"]

    print(
        f"Resolved to: {resolved_name}, {country} "
        f"({lat:.4f}, {lon:.4f})"
    )

    # ---------------------------------------------------------
    # 2. SOILGRIDS
    # ---------------------------------------------------------

    print("Fetching soil data...")

    soil = get_soil_data(
        lat,
        lon,
        resolved_name
    )

    # ---------------------------------------------------------
    # 3. CLIMATE + AIR QUALITY
    # ---------------------------------------------------------

    print("Fetching climate and air-quality data...")

    climate = get_environment_climate_data(
        lat,
        lon,
        resolved_name
    )

    # ---------------------------------------------------------
    # 4. BIODIVERSITY / GBIF
    # ---------------------------------------------------------

    print("Fetching biodiversity data...")

    biodiversity = get_biodiversity_data(
        lat,
        lon,
        resolved_name
    )

    # ---------------------------------------------------------
    # 5. LAND COVER / ESA WORLDCOVER
    # ---------------------------------------------------------

    print("Fetching ESA WorldCover data...")

    land_cover = get_land_cover_esa(
        lat,
        lon,
        resolved_name
    )

    # ---------------------------------------------------------
    # 6. TREE COVER LOSS / GLOBAL FOREST WATCH
    # ---------------------------------------------------------

    print("Fetching tree-cover loss data...")

    deforestation = get_deforestation_data(
        lat,
        lon,
        resolved_name
    )

    # ---------------------------------------------------------
    # 7. BUILD UNIFIED PROFILE
    # ---------------------------------------------------------

    profile = {
        "location": resolved_name,
        "country": country,

        "coordinates": {
            "lat": lat,
            "lon": lon
        },

        "soil": {
            "organic_carbon_gkg": soil.get(
                "soil_organic_carbon_gkg"
            ),
            "ph": soil.get(
                "soil_ph"
            ),
            "moisture_pct": soil.get(
                "soil_moisture_pct"
            )
        },

        "climate": {
            "average_temperature_c": climate.get(
                "avg_temperature_c"
            ),
            "annual_rainfall_mm": climate.get(
                "annual_rainfall_mm"
            )
        },

        "pollution": {
            "pm2_5_ug_m3": climate.get(
                "pollution", {}
            ).get("avg_pm2_5_ug_m3"),

            "pm10_ug_m3": climate.get(
                "pollution", {}
            ).get("avg_pm10_ug_m3"),

            "no2_ug_m3": climate.get(
                "pollution", {}
            ).get("avg_no2_ug_m3")
        },

        "biodiversity": {
            "species_richness": biodiversity.get(
                "distinct_species_recorded"
            ),
            "distinct_families": biodiversity.get(
                "distinct_families_recorded"
            ),
            "taxonomic_diversity_shannon": biodiversity.get(
                "taxonomic_diversity_shannon_index"
            )
        },

        "land_cover": {
            "classes": land_cover.get(
                "land_cover_classes_found",
                []
            ),
            "class_count": land_cover.get(
                "habitat_diversity_count_esa",
                0
            ),
            "class_proportions": land_cover.get(
                "land_cover_proportions",
                {}
            ),
            "habitat_diversity_shannon": land_cover.get(
                "habitat_diversity_shannon_index"
            )
        },

        "human_impact": {
            "tree_cover_loss": {
                "yearly_loss": deforestation.get(
                    "tree_cover_loss_by_year",
                    []
                )
            }
        }
    }

    return profile


def save_profile(profile, filename="data/structured/current_profile.json"):
    """
    Save the generated profile for inspection/debugging.
    """

    with open(filename, "w") as f:
        json.dump(profile, f, indent=2)

    print(f"\nProfile saved to {filename}")


def print_profile_summary(profile):
    """
    Print a readable summary without dumping the entire datasets.
    """

    print("\n" + "=" * 60)
    print("ENVIRONMENTAL PROFILE")
    print("=" * 60)

    print(f"Location: {profile['location']}, {profile['country']}")

    coords = profile["coordinates"]

    print(
        f"Coordinates: "
        f"{coords['lat']:.4f}, {coords['lon']:.4f}"
    )

    print("\nSOIL")
    print(
        f"  Organic carbon: "
        f"{profile['soil']['organic_carbon_gkg']} g/kg"
    )
    print(
        f"  pH: "
        f"{profile['soil']['ph']}"
    )
    print(
        f"  Moisture: "
        f"{profile['soil']['moisture_pct']}%"
    )

    print("\nCLIMATE")
    print(
        f"  Average temperature: "
        f"{profile['climate']['average_temperature_c']} °C"
    )
    print(
        f"  Annual rainfall: "
        f"{profile['climate']['annual_rainfall_mm']} mm"
    )

    print("\nAIR QUALITY")
    print(
        f"  PM2.5: "
        f"{profile['pollution']['pm2_5_ug_m3']} μg/m³"
    )
    print(
        f"  PM10: "
        f"{profile['pollution']['pm10_ug_m3']} μg/m³"
    )
    print(
        f"  NO₂: "
        f"{profile['pollution']['no2_ug_m3']} μg/m³"
    )

    print("\nBIODIVERSITY")
    print(
        f"  Species recorded: "
        f"{profile['biodiversity']['species_richness']}"
    )
    print(
        f"  Families recorded: "
        f"{profile['biodiversity']['distinct_families']}"
    )
    print(
        f"  Taxonomic Shannon index: "
        f"{profile['biodiversity']['taxonomic_diversity_shannon']}"
    )

    print("\nLAND COVER")
    print(
        f"  Classes found: "
        f"{profile['land_cover']['class_count']}"
    )
    print(
        f"  Habitat Shannon index: "
        f"{profile['land_cover']['habitat_diversity_shannon']}"
    )

    print(
        f"  Class proportions: "
        f"{profile['land_cover']['class_proportions']}"
    )

    print("\nTREE COVER LOSS")

    yearly_loss = profile[
        "human_impact"
    ][
        "tree_cover_loss"
    ][
        "yearly_loss"
    ]

    print(
        f"  Years available: "
        f"{len(yearly_loss)}"
    )

    if yearly_loss:
        latest = max(
            yearly_loss,
            key=lambda x: x.get(
                "umd_tree_cover_loss__year",
                0
            )
        )

        print(
            f"  Latest year: "
            f"{latest.get('umd_tree_cover_loss__year')}"
        )

        print(
            f"  Latest loss: "
            f"{latest.get('loss_ha')} ha"
        )

    print("=" * 60)


if __name__ == "__main__":

    location_name = input(
        "Enter a location to analyze: "
    ).strip()

    if not location_name:
        print("Please enter a location.")
        raise SystemExit

    try:

        profile = get_environment_profile(
            location_name
        )

        print_profile_summary(profile)

        save_profile(profile)

    except Exception as e:

        print("\nERROR:")
        print(e)