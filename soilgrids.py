import requests
import rasterio
import numpy as np
from pyproj import Transformer
import json
import os
import time

DEBUG = False
WCS_URL = "https://maps.isric.org/mapserv"


def get_soilgrids_value(
    latitude,
    longitude,
    coverage_id,
    temp_filename,
    retries=3
):
    """
    Fetch a small SoilGrids WCS subset around a coordinate.
    Tries a small box first, then widens automatically if no
    valid soil pixels are found (e.g. dense urban/water areas).
    """

    property_name = coverage_id.split("_")[0]
    url = f"{WCS_URL}?map=/map/{property_name}.map"

    transformer = Transformer.from_crs(
        "EPSG:4326",
        "ESRI:54052",
        always_xy=True
    )

    # Try increasingly larger search boxes if smaller ones find no valid data
    box_sizes = [0.02, 0.1, 0.3]

    for box_index, box in enumerate(box_sizes, start=1):
        if DEBUG:
            print(f"--- Trying box size {box}° (attempt {box_index}/{len(box_sizes)}) ---")

        min_lon, max_lon = longitude - box, longitude + box
        min_lat, max_lat = latitude - box, latitude + box

        min_x, min_y = transformer.transform(min_lon, min_lat)
        max_x, max_y = transformer.transform(max_lon, max_lat)

        params = [
            ("SERVICE", "WCS"),
            ("VERSION", "2.0.1"),
            ("REQUEST", "GetCoverage"),
            ("COVERAGEID", coverage_id),
            ("FORMAT", "GEOTIFF_INT16"),
            ("SUBSET", f"X({min_x},{max_x})"),
            ("SUBSET", f"Y({min_y},{max_y})"),
            ("SUBSETTINGCRS", "http://www.opengis.net/def/crs/EPSG/0/152160"),
            ("OUTPUTCRS", "http://www.opengis.net/def/crs/EPSG/0/4326")
        ]

        # --- Request with retries (your existing logic, unchanged) ---
        last_error = None
        response = None

        for attempt in range(1, retries + 1):
            try:
                if DEBUG:
                    print(f"Requesting SoilGrids {coverage_id} (attempt {attempt}/{retries})...")
                response = requests.get(url, params=params, timeout=120)
                response.raise_for_status()
                break
            except Exception as e:
                last_error = e
                if DEBUG:
                    print(f"SoilGrids request failed: {e}")
                if attempt < retries:
                    if DEBUG:
                        print("Retrying...")
                    time.sleep(3)
        else:
            raise Exception(f"SoilGrids failed after {retries} attempts: {last_error}")

        # --- Save raster ---
        os.makedirs("data", exist_ok=True)
        filepath = os.path.join("data", temp_filename)
        with open(filepath, "wb") as f:
            f.write(response.content)

        # --- Read raster ---
        try:
            with rasterio.open(filepath) as src:
                data = src.read(1).astype(float)
                nodata = src.nodata
                if DEBUG:
                    print(f"Raster shape: {data.shape}")
                    print(f"Raster min/max: {data.min()} / {data.max()}")
                    print(f"Raster nodata: {nodata}")
        except Exception as e:
            raise Exception(f"Could not read SoilGrids raster for {coverage_id}: {e}")

        # --- Filter invalid pixels ---
        valid = data[np.isfinite(data)]
        if nodata is not None:
            valid = valid[valid != nodata]
        valid = valid[valid != -32768]
        valid = valid[valid > 0]

        if len(valid) > 0:
            raw_mean = float(valid.mean())
            if DEBUG:
                print(f"{coverage_id}: valid pixels={len(valid)}, raw mean={raw_mean:.2f}, box used={box}°")
            return raw_mean

        if DEBUG:
            print(f"No valid pixels found for {coverage_id} at box size {box}° — widening search area...")

    # Every box size tried, genuinely no data — this is a real limitation, not an error
    if DEBUG:
        print(f"No valid pixels found for {coverage_id} even at widest radius ({box_sizes[-1]}°)")
    return None


def get_soil_data(
    latitude,
    longitude,
    location_name
):
    """
    Get SoilGrids soil properties for the 0-5 cm layer.
    """

    # ---------------------------------------------------------
    # ORGANIC CARBON
    # ---------------------------------------------------------

    raw_soc = get_soilgrids_value(
        latitude,
        longitude,
        "soc_0-5cm_mean",
        "temp_soc.tif"
    )

    soc_g_kg = (
        round(raw_soc / 10, 2)
        if raw_soc is not None
        else None
    )

    # ---------------------------------------------------------
    # pH
    # ---------------------------------------------------------

    raw_ph = get_soilgrids_value(
        latitude,
        longitude,
        "phh2o_0-5cm_mean",
        "temp_ph.tif"
    )

    ph = (
        round(raw_ph / 10, 2)
        if raw_ph is not None
        else None
    )

    # ---------------------------------------------------------
    # MOISTURE
    # ---------------------------------------------------------
    # SoilGrids currently maps wv003, but its WebDAV access
    # is not available in the same property-folder structure.
    # We'll add this separately after SOC + pH work.

    moisture_pct = None

    return {
        "location": location_name,
        "lat": latitude,
        "lon": longitude,
        "soil_organic_carbon_gkg": soc_g_kg,
        "soil_ph": ph,
        "soil_moisture_pct": moisture_pct
    }


if __name__ == "__main__":

    lat = 19.07283
    lon = 72.88261

    print(
        "\nTesting SoilGrids for Mumbai...\n"
    )

    try:

        result = get_soil_data(
            lat,
            lon,
            "Mumbai"
        )

        print(
            "\nFinal SoilGrids Result:"
        )

        print(
            json.dumps(
                result,
                indent=2
            )
        )

        os.makedirs(
            "data/structured",
            exist_ok=True
        )

        with open(
            "data/structured/soil_data.json",
            "w"
        ) as f:

            json.dump(
                [result],
                f,
                indent=2
            )

        print(
            "\nSaved to "
            "data/structured/soil_data.json"
        )

    except Exception as e:

        print("\nERROR:")
        print(e)