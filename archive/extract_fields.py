import re


def extract_fields_from_message(message, current_state):
    """
    Extracts environmental information from natural-language messages.

    Handles:
    - Soil organic carbon as % or g/kg
    - Rainfall as mm/year or low/moderate/high
    - Land-use keywords
    - Climate/region keywords
    - Location names introduced with common phrases
    """

    message_lower = message.lower()
    updates = {}

    # =========================================================
    # SOIL ORGANIC CARBON
    # =========================================================

    if current_state.fields["soil_organic_carbon"] is None:

        percent_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:%|percent)"
            r"\s*(?:organic\s+carbon|carbon)?",
            message_lower
        )

        if percent_match:
            updates["soil_organic_carbon"] = float(
                percent_match.group(1)
            )

        else:

            gkg_match = re.search(
                r"(\d+(?:\.\d+)?)\s*g\s*/\s*kg"
                r".{0,30}organic\s+carbon",
                message_lower
            )

            if gkg_match:
                updates["soil_organic_carbon"] = float(
                    gkg_match.group(1)
                )

    # =========================================================
    # RAINFALL
    # =========================================================

    if current_state.fields["rainfall"] is None:

        rainfall_match = re.search(
            r"(\d+(?:\.\d+)?)\s*mm"
            r"(?:\s*(?:per|/)\s*(?:year|yr|annum|annual))?",
            message_lower
        )

        if rainfall_match:

            updates["rainfall"] = float(
                rainfall_match.group(1)
            )

        elif any(
            phrase in message_lower
            for phrase in [
                "low rainfall",
                "low rain",
                "little rain",
                "very little rain",
                "hardly any rain",
                "not much rain",
                "dry",
                "drought"
            ]
        ):

            updates["rainfall"] = "low"

        elif any(
            phrase in message_lower
            for phrase in [
                "high rainfall",
                "heavy rain",
                "lots of rain",
                "very rainy"
            ]
        ):

            updates["rainfall"] = "high"

        elif any(
            phrase in message_lower
            for phrase in [
                "moderate rainfall",
                "average rainfall",
                "moderate rain"
            ]
        ):

            updates["rainfall"] = "moderate"

        elif message_lower.strip() == "low":

            updates["rainfall"] = "low"

        elif message_lower.strip() == "high":

            updates["rainfall"] = "high"

        elif message_lower.strip() in [
            "moderate",
            "average"
        ]:

            updates["rainfall"] = "moderate"

    # =========================================================
    # LAND USE
    # =========================================================

    if current_state.fields["land_use"] is None:

        land_use_keywords = {

            "wheat": "wheat monoculture",

            "monoculture": "monoculture",

            "mixed cropping": "mixed cropping",

            "mixed crop": "mixed cropping",

            "intercropping": "intercropping",

            "inter-cropping": "intercropping",

            "agroforestry": "agroforestry",

            "pasture": "pasture",

            "grazing": "pasture",

            "orchard": "orchard",

            "forest": "forest",

            "cropland": "cropland",

            "farmland": "cropland"
        }

        for keyword, label in land_use_keywords.items():

            if keyword in message_lower:

                updates["land_use"] = label
                break

    # =========================================================
    # REGION / CLIMATE ZONE
    # =========================================================

    if current_state.fields["region"] is None:

        region_keywords = [
            "semi-arid",
            "semi arid",
            "tropical",
            "temperate",
            "arid",
            "subtropical",
            "sub-tropical",
            "sub-saharan",
            "mediterranean",
            "humid"
        ]

        for keyword in region_keywords:

            if keyword in message_lower:

                if keyword == "semi arid":
                    updates["region"] = "semi-arid"

                elif keyword == "sub-tropical":
                    updates["region"] = "subtropical"

                else:
                    updates["region"] = keyword

                break

    # =========================================================
    # LOCATION
    # =========================================================

    if current_state.location is None:

        location_patterns = [
            r"\bin\s+([A-Za-z][A-Za-z .'-]{1,40})",
            r"\bnear\s+([A-Za-z][A-Za-z .'-]{1,40})",
            r"\baround\s+([A-Za-z][A-Za-z .'-]{1,40})",
            r"\bfrom\s+([A-Za-z][A-Za-z .'-]{1,40})"
        ]

        for pattern in location_patterns:

            match = re.search(
                pattern,
                message,
                re.IGNORECASE
            )

            if match:

                location = match.group(1).strip()

                # Remove common trailing words that
                # aren't part of the location.
                location = re.split(
                    r"\b(?:and|where|but|with|on|my)\b",
                    location,
                    maxsplit=1,
                    flags=re.IGNORECASE
                )[0].strip()

                if location:
                    updates["location"] = location
                    break

    return updates