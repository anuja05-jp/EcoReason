import json
from retrieve_knowledge import retrieve_relevant_knowledge

def build_query_from_profile(profile):
    """
    Turns the environmental profile into a natural-language query,
    so vector search can find the most relevant knowledge passages
    for THIS specific location's actual conditions.
    """
    parts = []

    soc = profile["soil"]["organic_carbon_gkg"]
    if soc is not None:
        parts.append(f"soil organic carbon {soc} g/kg")

    rainfall = profile["climate"]["annual_rainfall_mm"]
    if rainfall is not None:
        parts.append(f"annual rainfall {rainfall} mm")

    land_use = profile.get("land_use_detail_farmer_reported")
    if land_use:
        parts.append(f"land use: {land_use}")

    classes = profile["land_cover"]["classes"]
    if classes:
        parts.append(f"land cover includes {', '.join(classes)}")

    tree_loss = profile["human_impact"]["tree_cover_loss"]["total_loss_ha"]
    if tree_loss:
        parts.append(f"tree cover loss {tree_loss} hectares")

    return "Environmental conditions: " + "; ".join(parts)


def attach_evidence_to_profile(profile, top_k=5):
    """
    Retrieves the most relevant scientific knowledge passages for
    this profile and attaches them, with their source IDs, so the
    reasoning model can only cite things that were actually retrieved.
    """
    query = build_query_from_profile(profile)
    passages, ids = retrieve_relevant_knowledge(query, top_k=top_k)

    evidence = [
        {"source_id": doc_id, "text": passage}
        for doc_id, passage in zip(ids, passages)
    ]

    profile["retrieved_evidence"] = evidence
    return profile


if __name__ == "__main__":
    with open("data/structured/rag_reasoning_context.json") as f:
        profile = json.load(f)

    profile = attach_evidence_to_profile(profile)

    with open("data/structured/rag_reasoning_context.json", "w") as f:
        json.dump(profile, f, indent=2)

    print(f"Attached {len(profile['retrieved_evidence'])} evidence passages.")
    for e in profile["retrieved_evidence"]:
        print(" -", e["source_id"])