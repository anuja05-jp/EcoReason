import json
from pathlib import Path

from live_environment_profile import build_live_environment_profile
from reasoning_engine import build_reasoning_context
from rag_reasoning import attach_evidence


# =========================================================
# PATHS
# =========================================================

REASONING_CONTEXT_PATH = (
    "data/structured/reasoning_context.json"
)

RAG_CONTEXT_PATH = (
    "data/structured/rag_reasoning_context.json"
)


# =========================================================
# SAVE JSON
# =========================================================

def save_json(data, path):

    Path(path).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(path, "w") as f:

        json.dump(
            data,
            f,
            indent=2
        )


# =========================================================
# MAIN HYBRID CHAT
# =========================================================

def run_hybrid_chat():

    print(
        "System: Hi! Tell me where your land is, "
        "and I'll automatically pull soil, climate, "
        "biodiversity, and land-use data for it."
    )

    # -----------------------------------------------------
    # STEP 1 — LOCATION
    # -----------------------------------------------------

    location_name = input(
        "\nYou (location, e.g. 'Jaipur, India'): "
    ).strip()

    if not location_name:

        print(
            "No location provided."
        )

        return None

    # -----------------------------------------------------
    # STEP 2 — LIVE ENVIRONMENTAL DATA
    # -----------------------------------------------------

    print(
        "\n(Fetching live environmental data...)"
    )

    profile = build_live_environment_profile(
        location_name
    )

    print(
        "\nSystem: Here's what I found automatically "
        "for your area:"
    )

    print(
        json.dumps(
            profile,
            indent=2
        )
    )

    # -----------------------------------------------------
    # STEP 3 — FARMER INPUT
    # -----------------------------------------------------

    farmer_practice = input(
        "\nSystem: One thing I can't get from satellite "
        "data — what's your specific farming practice "
        "or crop? (e.g. 'monoculture wheat', "
        "'mixed cropping', 'pasture' — or type 'skip')\n"
        "You: "
    ).strip()

    farmer = {
        "soil_organic_carbon": None,
        "rainfall": None,
        "land_use": None,
        "region": None
    }

    if (
        farmer_practice
        and farmer_practice.lower() != "skip"
    ):

        farmer["land_use"] = farmer_practice

    # -----------------------------------------------------
    # STEP 4 — REASONING ENGINE
    # -----------------------------------------------------

    print(
        "\nRunning EcoReason signal detection..."
    )

    reasoning_context = build_reasoning_context(
        profile,
        farmer
    )

    print(
        "\nDetected signals:"
    )

    for signal in reasoning_context.get(
        "detected_signals",
        []
    ):

        print(
            f"  • {signal.get('description', '')}"
            f" [{signal.get('severity', '')}]"
        )

    print(
        "\nDetected interactions:"
    )

    interactions = reasoning_context.get(
        "multi_variable_interactions",
        []
    )

    if not interactions:

        print(
            "  • No multi-variable interactions detected."
        )

    else:

        for interaction in interactions:

            print(
                f"  • {interaction.get('interaction', '')}"
            )

    # -----------------------------------------------------
    # STEP 5 — SAVE INTERMEDIATE REASONING CONTEXT
    # -----------------------------------------------------

    save_json(
        reasoning_context,
        REASONING_CONTEXT_PATH
    )

    print(
        "\nReasoning context saved."
    )

    # -----------------------------------------------------
    # STEP 6 — RETRIEVE SCIENTIFIC EVIDENCE
    # -----------------------------------------------------

    print(
        "\nRunning scientific evidence retrieval..."
    )

    rag_context = attach_evidence(
        reasoning_context
    )

    # -----------------------------------------------------
    # STEP 7 — SAVE FINAL RAG CONTEXT
    # -----------------------------------------------------

    save_json(
        rag_context,
        RAG_CONTEXT_PATH
    )

    print(
        f"\nRAG context saved to "
        f"{RAG_CONTEXT_PATH}"
    )

    print(
        "\nSaved — ready for reasoning."
    )

    return rag_context


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    run_hybrid_chat()