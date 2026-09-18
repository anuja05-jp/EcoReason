import json
from pathlib import Path


PROFILE_PATH = "data/structured/current_profile.json"
FARMER_INPUT_PATH = "data/structured/farmer_input.json"
OUTPUT_PATH = "data/structured/reasoning_context.json"


# ============================================================
# BASIC HELPERS
# ============================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


# ============================================================
# MERGE FARMER INPUT WITH LIVE ENVIRONMENT DATA
# ============================================================

def merge_farmer_inputs(profile, farmer):
    merged = dict(profile)

    if not farmer:
        return merged

    # Farmer reported soil organic carbon
    farmer_soc = safe_float(farmer.get("soil_organic_carbon"))

    if farmer_soc is not None:
        merged.setdefault("soil", {})

        # Farmer input is assumed to be percentage
        merged["soil"]["farmer_reported_organic_carbon_pct"] = farmer_soc
        merged["soil"]["farmer_reported_organic_carbon_gkg"] = farmer_soc * 10

    # Farmer reported rainfall
    farmer_rainfall = safe_float(farmer.get("rainfall"))

    if farmer_rainfall is not None:
        merged.setdefault("climate", {})
        merged["climate"]["farmer_reported_rainfall_mm"] = farmer_rainfall

    # Farmer reported land use
    land_use = farmer.get("land_use")

    if land_use:
        merged["land_use"] = {
            "farmer_reported": land_use
        }

    # Farmer reported region
    region = farmer.get("region")

    if region:
        merged["region"] = region

    return merged


# ============================================================
# SIGNAL DETECTION
# ============================================================

def detect_signals(profile):
    signals = []

    soil = profile.get("soil", {})
    climate = profile.get("climate", {})
    pollution = profile.get("pollution", {})
    biodiversity = profile.get("biodiversity", {})
    land_cover = profile.get("land_cover", {})
    human_impact = profile.get("human_impact", {})
    land_use = profile.get("land_use", {})

    # --------------------------------------------------------
    # 1. SOIL CARBON STRESS
    # --------------------------------------------------------

    farmer_soc = safe_float(
        soil.get("farmer_reported_organic_carbon_gkg")
    )

    api_soc = safe_float(
        soil.get("organic_carbon_gkg")
    )

    soil_carbon = (
        farmer_soc
        if farmer_soc is not None
        else api_soc
    )

    if soil_carbon is not None and soil_carbon < 10:
        signals.append({
            "type": "soil_carbon_stress",
            "severity": "moderate",
            "value": soil_carbon,
            "unit": "g/kg",
            "description": "Low soil organic carbon"
        })

    # --------------------------------------------------------
    # 2. RAINFALL STRESS
    # --------------------------------------------------------

    rainfall = safe_float(
        climate.get("farmer_reported_rainfall_mm")
    )

    if rainfall is None:
        rainfall = safe_float(
            climate.get("annual_rainfall_mm")
        )

    if rainfall is not None and rainfall < 600:
        signals.append({
            "type": "rainfall_stress",
            "severity": "moderate",
            "value": rainfall,
            "unit": "mm/year",
            "description": "Low annual rainfall"
        })

    # --------------------------------------------------------
    # 3. FARMING PRACTICE
    # --------------------------------------------------------

    reported_land_use = str(
        land_use.get("farmer_reported", "")
    ).lower()

    if "monoculture" in reported_land_use:
        signals.append({
            "type": "monoculture",
            "severity": "moderate",
            "value": reported_land_use,
            "description": "Monoculture cropping reported"
        })

    elif "mixed" in reported_land_use:
        signals.append({
            "type": "mixed_cropping",
            "severity": "low",
            "value": reported_land_use,
            "description": "Mixed cropping reported"
        })

    # --------------------------------------------------------
    # 4. URBAN / BUILT-UP DOMINANCE
    # --------------------------------------------------------

    proportions = land_cover.get(
        "class_proportions",
        {}
    )

    built_up = safe_float(
        proportions.get("Built-up")
    )

    if built_up is not None and built_up > 0.50:
        signals.append({
            "type": "urban_land_dominance",
            "severity": "high",
            "value": built_up,
            "unit": "proportion",
            "description": "Built-up land dominates the analysis area"
        })

    # --------------------------------------------------------
    # 5. HABITAT DIVERSITY PRESSURE
    # --------------------------------------------------------

    habitat_shannon = safe_float(
        land_cover.get("habitat_diversity_shannon")
    )

    if habitat_shannon is not None and habitat_shannon < 1.0:
        signals.append({
            "type": "habitat_diversity_pressure",
            "severity": "moderate",
            "value": habitat_shannon,
            "unit": "Shannon index",
            "description": "Low habitat diversity"
        })

    # --------------------------------------------------------
    # 6. BIODIVERSITY PRESSURE
    # --------------------------------------------------------

    biodiversity_shannon = safe_float(
        biodiversity.get("taxonomic_diversity_shannon")
    )

    if (
        biodiversity_shannon is not None
        and biodiversity_shannon < 3.5
    ):
        signals.append({
            "type": "biodiversity_pressure",
            "severity": "moderate",
            "value": biodiversity_shannon,
            "unit": "Shannon index",
            "description": "Reduced taxonomic diversity"
        })

    # --------------------------------------------------------
    # 7. TREE COVER LOSS
    # --------------------------------------------------------

    tree_cover_loss = human_impact.get(
        "tree_cover_loss",
        {}
    )

    yearly_loss = tree_cover_loss.get(
        "yearly_loss",
        []
    )

    if yearly_loss:

        latest_record = max(
            yearly_loss,
            key=lambda x: safe_float(
                x.get("umd_tree_cover_loss__year")
            ) or 0
        )

        latest_loss = safe_float(
            latest_record.get("loss_ha")
        )

        latest_year = latest_record.get(
            "umd_tree_cover_loss__year"
        )

        if latest_loss is not None and latest_loss > 0:
            signals.append({
                "type": "tree_cover_loss",
                "severity": "moderate",
                "value": latest_loss,
                "unit": "ha",
                "year": latest_year,
                "description": "Tree-cover loss detected"
            })

    # --------------------------------------------------------
    # 8. POLLUTION SIGNAL
    #
    # We don't invent a health/environmental threshold here.
    # Pollution is only marked as an observed environmental
    # variable when actual values are available.
    # --------------------------------------------------------

    pm25 = safe_float(
        pollution.get("pm2_5_ug_m3")
    )

    pm10 = safe_float(
        pollution.get("pm10_ug_m3")
    )

    no2 = safe_float(
        pollution.get("no2_ug_m3")
    )

    available_pollution = {}

    if pm25 is not None:
        available_pollution["pm2_5_ug_m3"] = pm25

    if pm10 is not None:
        available_pollution["pm10_ug_m3"] = pm10

    if no2 is not None:
        available_pollution["no2_ug_m3"] = no2

    if available_pollution:
        signals.append({
            "type": "air_quality_observed",
            "severity": "observed",
            "value": available_pollution,
            "description": "Air-quality measurements available for the location"
        })

    return signals


# ============================================================
# MULTI-VARIABLE INTERACTIONS
# ============================================================

def find_interactions(signals):

    signal_types = {
        signal["type"]
        for signal in signals
    }

    interactions = []

    # --------------------------------------------------------
    # SOIL + RAINFALL + MONOCULTURE
    # --------------------------------------------------------

    if {
        "soil_carbon_stress",
        "rainfall_stress",
        "monoculture"
    }.issubset(signal_types):

        interactions.append({
            "interaction": "soil_water_crop_diversity",
            "variables": [
                "soil_carbon_stress",
                "rainfall_stress",
                "monoculture"
            ],
            "evidence_query": (
                "soil organic carbon water retention "
                "monoculture cropping agricultural resilience"
            ),
            "reasoning_goal": (
                "Assess how soil condition, water availability, "
                "and monoculture interact to influence "
                "agricultural resilience."
            )
        })

    # --------------------------------------------------------
    # SOIL + RAINFALL
    # --------------------------------------------------------

    elif {
        "soil_carbon_stress",
        "rainfall_stress"
    }.issubset(signal_types):

        interactions.append({
            "interaction": "soil_water",
            "variables": [
                "soil_carbon_stress",
                "rainfall_stress"
            ],
            "evidence_query": (
                "soil organic carbon water retention "
                "drought resilience"
            ),
            "reasoning_goal": (
                "Assess the relationship between soil condition "
                "and water availability."
            )
        })

    # --------------------------------------------------------
    # MONOCULTURE + BIODIVERSITY PRESSURE
    # --------------------------------------------------------

    if {
        "monoculture",
        "biodiversity_pressure"
    }.issubset(signal_types):

        interactions.append({
            "interaction": "crop_biodiversity",
            "variables": [
                "monoculture",
                "biodiversity_pressure"
            ],
            "evidence_query": (
                "agricultural monoculture biodiversity "
                "crop diversity ecological resilience"
            ),
            "reasoning_goal": (
                "Assess how simplified agricultural systems "
                "relate to biodiversity and ecological resilience."
            )
        })

    # --------------------------------------------------------
    # URBAN LAND + HABITAT DIVERSITY
    # --------------------------------------------------------

    if {
        "urban_land_dominance",
        "habitat_diversity_pressure"
    }.issubset(signal_types):

        interactions.append({
            "interaction": "urban_habitat",
            "variables": [
                "urban_land_dominance",
                "habitat_diversity_pressure"
            ],
            "evidence_query": (
                "urban expansion habitat fragmentation "
                "biodiversity habitat diversity"
            ),
            "reasoning_goal": (
                "Assess how built-up land dominance and habitat "
                "diversity pressure interact."
            )
        })

    # --------------------------------------------------------
    # TREE LOSS + HABITAT
    # --------------------------------------------------------

    if {
        "tree_cover_loss",
        "habitat_diversity_pressure"
    }.issubset(signal_types):

        interactions.append({
            "interaction": "tree_loss_habitat",
            "variables": [
                "tree_cover_loss",
                "habitat_diversity_pressure"
            ],
            "evidence_query": (
                "tree cover loss habitat fragmentation "
                "biodiversity"
            ),
            "reasoning_goal": (
                "Assess how tree-cover loss may relate to "
                "habitat pressure."
            )
        })

    # --------------------------------------------------------
    # URBAN + TREE LOSS
    # --------------------------------------------------------

    if {
        "urban_land_dominance",
        "tree_cover_loss"
    }.issubset(signal_types):

        interactions.append({
            "interaction": "urban_tree_cover",
            "variables": [
                "urban_land_dominance",
                "tree_cover_loss"
            ],
            "evidence_query": (
                "urban expansion tree cover loss "
                "land use change vegetation"
            ),
            "reasoning_goal": (
                "Assess the relationship between built-up land "
                "dominance and observed tree-cover loss."
            )
        })

    # --------------------------------------------------------
    # MONOCULTURE + URBAN LAND
    # --------------------------------------------------------

    if {
        "monoculture",
        "urban_land_dominance"
    }.issubset(signal_types):

        interactions.append({
            "interaction": "agriculture_urban_pressure",
            "variables": [
                "monoculture",
                "urban_land_dominance"
            ],
            "evidence_query": (
                "urban expansion agricultural land "
                "land use change farming"
            ),
            "reasoning_goal": (
                "Assess the interaction between agricultural "
                "land-use practice and surrounding built-up pressure."
            )
        })

    # --------------------------------------------------------
    # POLLUTION + URBAN LAND
    # --------------------------------------------------------

    if {
        "air_quality_observed",
        "urban_land_dominance"
    }.issubset(signal_types):

        interactions.append({
            "interaction": "urban_air_quality",
            "variables": [
                "urban_land_dominance",
                "air_quality_observed"
            ],
            "evidence_query": (
                "urban land use air pollution "
                "built-up areas air quality"
            ),
            "reasoning_goal": (
                "Assess the relationship between built-up "
                "land dominance and observed air-quality conditions."
            )
        })

        # Fallback: if no named interaction rule matched, but at least 2
    # signals were detected, pair them generically.
    if not interactions and len(signals) >= 2:
        interactions.append({
            "interaction": "general_multi_signal",
            "variables": [s["type"] for s in signals],
            "evidence_query": " ".join(s["description"] for s in signals),
            "reasoning_goal": (
                "Assess how the detected environmental signals interact, "
                "since no predefined interaction pattern matched this "
                "specific combination."
            )
        })

    # Second fallback: even 0-1 signals still deserves an answer —
    # query using the raw profile itself so the system never goes silent.
    elif not interactions:
        interactions.append({
            "interaction": "baseline_assessment",
            "variables": ["soil_organic_carbon", "rainfall", "land_use"],
            "evidence_query": "soil health rainfall land use general environmental assessment",
            "reasoning_goal": (
                "No significant stress signals were detected against current "
                "thresholds — provide a baseline assessment and note that the "
                "profile does not indicate acute pressure by the system's rules."
            )
        })

    return interactions


# ============================================================
# BUILD FINAL REASONING CONTEXT
# ============================================================

def build_reasoning_context(profile, farmer=None):

    merged_profile = merge_farmer_inputs(
        profile,
        farmer
    )

    signals = detect_signals(
        merged_profile
    )

    interactions = find_interactions(
        signals
    )

    context = {
        "location": merged_profile.get("location"),

        "environmental_profile": merged_profile,

        "detected_signals": signals,

        "multi_variable_interactions": interactions,

        "reasoning_requirements": {
            "minimum_variables": 3,
            "scientific_grounding_required": True,
            "causal_chain_required": True,
            "measurable_recommendation_required": True,
            "uncertainty_required": True
        }
    }

    return context


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    profile = load_json(
        PROFILE_PATH
    )

    farmer = {}

    if Path(FARMER_INPUT_PATH).exists():
        farmer = load_json(
            FARMER_INPUT_PATH
        )

    reasoning_context = build_reasoning_context(
        profile,
        farmer
    )

    save_json(
        reasoning_context,
        OUTPUT_PATH
    )

    print("\nDetected signals:")

    for signal in reasoning_context[
        "detected_signals"
    ]:
        print(
            f"  • {signal['description']} "
            f"[{signal['severity']}]"
        )

    print("\nDetected interactions:")

    if not reasoning_context[
        "multi_variable_interactions"
    ]:
        print(
            "  • No multi-variable interactions detected."
        )
    else:
        for interaction in reasoning_context[
            "multi_variable_interactions"
        ]:
            print(
                f"  • {interaction['interaction']}"
            )

    print(
        f"\nReasoning context saved to {OUTPUT_PATH}"
    )