import requests
import json

DEBUG = False
def get_climate_data(lat, lon, location_name):
    """
    Fetches temperature and rainfall for a location.
    """

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "daily": "temperature_2m_mean,precipitation_sum",
        "timezone": "auto"
    }

    for attempt in range(3):
        try:
            if DEBUG:
                print(f"Requesting climate data (attempt {attempt + 1}/3)...")

            response = requests.get(
                url,
                params=params,
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            temperatures = data["daily"]["temperature_2m_mean"]
            rainfall = data["daily"]["precipitation_sum"]

            temperatures = [v for v in temperatures if v is not None]
            rainfall = [v for v in rainfall if v is not None]

            avg_temp = sum(temperatures) / len(temperatures)
            total_rainfall = sum(rainfall)

            return {
                "location": location_name,
                "lat": lat,
                "lon": lon,
                "avg_temperature_c": round(avg_temp, 1),
                "annual_rainfall_mm": round(total_rainfall, 1)
            }

        except requests.exceptions.RequestException as e:
            if DEBUG:
                print(f"Climate request failed: {e}")

            if attempt == 2:
                raise


def get_air_quality_data(lat, lon):
    """
    Fetches current air-quality indicators from Open-Meteo.
    Values are modelled atmospheric concentrations in μg/m³.
    """

    url = "https://air-quality-api.open-meteo.com/v1/air-quality"

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "pm2_5,pm10,nitrogen_dioxide",
        "forecast_days": 1,
        "timezone": "auto"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()["hourly"]

    def average(values):
        values = [v for v in values if v is not None]
        return round(sum(values) / len(values), 2) if values else None

    return {
        "avg_pm2_5_ug_m3": average(data["pm2_5"]),
        "avg_pm10_ug_m3": average(data["pm10"]),
        "avg_no2_ug_m3": average(data["nitrogen_dioxide"])
    }


def get_environment_climate_data(lat, lon, location_name):

    climate = get_climate_data(lat, lon, location_name)
    air_quality = get_air_quality_data(lat, lon)

    return {
        **climate,
        "pollution": air_quality
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
        get_environment_climate_data(
            loc["lat"],
            loc["lon"],
            loc["name"]
        )
        for loc in locations
        ]


    with open("data/structured/climate_data.json", "w") as f:
        json.dump(results, f, indent=2)


    print("Done! Saved to data/structured/climate_data.json")
    print(json.dumps(results, indent=2))