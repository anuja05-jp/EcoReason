QUESTION_TEMPLATES = {
    "soil_organic_carbon": "What is your soil organic carbon percentage (if you know it)?",
    "rainfall": "How would you describe your rainfall pattern — low, moderate, or high?",
    "land_use": "What is your current land use? (e.g. monoculture wheat, mixed cropping, pasture)",
    "region": "What region or climate zone is your land in? (e.g. semi-arid, tropical, temperate)"
}

def generate_clarifying_question(missing_fields):
    """
    Given a list of missing fields, asks about them in one natural sentence,
    matching the brief's own example style.
    """
    if not missing_fields:
        return None

    if len(missing_fields) == 1:
        return QUESTION_TEMPLATES[missing_fields[0]]

    # Combine multiple missing fields into one question, brief's example style
    readable_names = {
        "soil_organic_carbon": "soil organic carbon %",
        "rainfall": "rainfall pattern",
        "land_use": "land use type",
        "region": "region"
    }
    parts = [readable_names[f] for f in missing_fields]
    joined = ", ".join(parts[:-1]) + (" and " + parts[-1] if len(parts) > 1 else parts[0])
    return f"Can you provide {joined}?"