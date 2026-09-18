import json


def load_json(filename):
    with open(f"data/structured/{filename}", "r") as f:
        return json.load(f)


def build_environment_profile(location_index=0):

    soil = load_json("soil_data.json")[location_index]
    climate = load_json("climate_data.json")[location_index]
    biodiversity = load_json("biodiversity_data.json")[location_index]
    land_cover = load_json("land_cover_esa_data.json")[location_index]
    deforestation = load_json("deforestation_data.json")[location_index]

    # -----------------------------
    # Deforestation calculations
    # -----------------------------

    yearly_loss = deforestation.get("tree_cover_loss_by_year", [])

    total_tree_cover_loss_ha = sum(
        item["loss_ha"]
        for item in yearly_loss
    )

    latest_year = None
    latest_loss_ha = None

    if yearly_loss:
        latest = max(
            yearly_loss,
            key=lambda x: x["umd_tree_cover_loss__year"]
        )

        latest_year = latest["umd_tree_cover_loss__year"]
        latest_loss_ha = latest["loss_ha"]

    # -----------------------------
    # Unified environmental profile
    # -----------------------------

    profile = {

        "location": soil["location"],

        "coordinates": {
            "lat": soil["lat"],
            "lon": soil["lon"]
        },

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
            "species_richness": biodiversity[
                "distinct_species_recorded"
            ],

            "distinct_families": biodiversity[
                "distinct_families_recorded"
            ],

            "taxonomic_diversity_shannon": biodiversity[
                "taxonomic_diversity_shannon_index"
            ]
        },

        "land_cover": {
            "classes": land_cover[
                "land_cover_classes_found"
            ],

            "class_count": land_cover[
                "habitat_diversity_count_esa"
            ],

            "class_proportions": land_cover[
                "land_cover_proportions"
            ],

            "habitat_diversity_shannon": land_cover[
                "habitat_diversity_shannon_index"
            ]
        },

        "human_impact": {

            "tree_cover_loss": {
                "total_loss_ha": round(
                    total_tree_cover_loss_ha,
                    2
                ),

                "latest_year": latest_year,

                "latest_year_loss_ha": round(
                    latest_loss_ha,
                    2
                ) if latest_loss_ha is not None else None,

                "yearly_loss": yearly_loss
            }
        }
    }

    return profile


if __name__ == "__main__":

    profile = build_environment_profile(0)

    print(
        json.dumps(
            profile,
            indent=2
        )
    )