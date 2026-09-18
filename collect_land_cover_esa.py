import rasterio
from rasterio.windows import from_bounds
import json
import math


WORLDCOVER_CLASSES = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare / sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water bodies",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen",
}


def get_tile_name(lat, lon):
    tile_lat = int(math.floor(lat / 3.0) * 3)
    tile_lon = int(math.floor(lon / 3.0) * 3)

    lat_prefix = "N" if tile_lat >= 0 else "S"
    lon_prefix = "E" if tile_lon >= 0 else "W"

    return f"{lat_prefix}{abs(tile_lat):02d}{lon_prefix}{abs(tile_lon):03d}"


def get_land_cover_esa(lat, lon, location_name, box_degrees=0.05):

    tile = get_tile_name(lat, lon)

    url = (
        f"/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/"
        f"v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
    )

    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):

        with rasterio.open(url) as src:

            min_lon = lon - box_degrees
            max_lon = lon + box_degrees
            min_lat = lat - box_degrees
            max_lat = lat + box_degrees

            window = from_bounds(
                min_lon,
                min_lat,
                max_lon,
                max_lat,
                src.transform
            )

            data = src.read(1, window=window)

    # Remove empty / invalid pixels
    values = data.flatten()
    values = [int(v) for v in values if v != 0 and v in WORLDCOVER_CLASSES]

    total_pixels = len(values)

    if total_pixels == 0:
        return {
            "location": location_name,
            "lat": lat,
            "lon": lon,
            "esa_tile": tile,
            "land_cover_classes_found": [],
            "habitat_diversity_count_esa": 0,
            "land_cover_proportions": {},
            "habitat_diversity_shannon_index": 0.0
        }

    class_counts = {}

    for value in values:
        class_name = WORLDCOVER_CLASSES[value]
        class_counts[class_name] = class_counts.get(class_name, 0) + 1

    # Calculate proportions
    class_proportions = {}

    for class_name, count in class_counts.items():
        proportion = count / total_pixels

        class_proportions[class_name] = round(proportion, 4)

    # Shannon habitat diversity
    shannon_index = 0.0

    for proportion in class_proportions.values():

        if proportion > 0:
            shannon_index -= proportion * math.log(proportion)

    return {
        "location": location_name,
        "lat": lat,
        "lon": lon,
        "esa_tile": tile,

        "land_cover_classes_found": sorted(
            class_counts.keys()
        ),

        "habitat_diversity_count_esa": len(class_counts),

        "land_cover_proportions": class_proportions,

        "habitat_diversity_shannon_index": round(
            shannon_index,
            3
        )
    }


if __name__ == "__main__":

    locations = [
        {
            "name": "Semi-arid India example",
            "lat": 26.9,
            "lon": 75.8
        },
        {
            "name": "Sub-Saharan Africa example",
            "lat": -1.3,
            "lon": 36.8
        }
    ]

    results = [
        get_land_cover_esa(
            loc["lat"],
            loc["lon"],
            loc["name"]
        )
        for loc in locations
    ]

    with open(
        "data/structured/land_cover_esa_data.json",
        "w"
    ) as f:
        json.dump(results, f, indent=2)

    print(
        "Done! Saved to "
        "data/structured/land_cover_esa_data.json"
    )

    print(json.dumps(results, indent=2))