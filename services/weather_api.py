"""Open-Meteo fetch with strict validation; sample data is used only when requested."""
from __future__ import annotations
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
DAILY = "temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration,wind_speed_10m_max"

class WeatherError(RuntimeError):
    pass


def geocode(city: str) -> dict:
    if len(city.strip()) < 2:
        raise WeatherError("Enter at least two characters for the location.")
    try:
        response = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city.strip(), "count": 10, "language": "en", "format": "json", "countryCode": "IN"}, timeout=12)
        response.raise_for_status()
        hits = response.json().get("results", [])
    except (requests.RequestException, ValueError) as ex:
        raise WeatherError(f"Location lookup unavailable: {ex}") from ex
    if not hits:
        raise WeatherError("No Indian location found. Try a nearby major city.")
    hit = hits[0]
    return {"name": hit["name"], "admin1": hit.get("admin1", ""), "latitude": hit["latitude"], "longitude": hit["longitude"], "timezone": hit.get("timezone", "Asia/Kolkata")}


def validate_days(rows):
    if len(rows) < 3:
        raise WeatherError("Fewer than three forecast days returned.")
    required = ("date", "tmax", "tmin", "rain", "et0", "wind")
    for row in rows:
        if any(row.get(k) is None for k in required):
            raise WeatherError("Weather data has missing values.")
        for key in ("tmax", "tmin", "rain", "et0", "wind"):
            try: row[key] = float(row[key])
            except (TypeError, ValueError) as ex: raise WeatherError(f"Invalid {key} weather measurement.") from ex
    return rows


def live_forecast(location: dict) -> dict:
    try:
        response = requests.get("https://api.open-meteo.com/v1/forecast", params={"latitude": location["latitude"], "longitude": location["longitude"], "daily": DAILY, "forecast_days": 7, "timezone": location["timezone"]}, timeout=18)
        response.raise_for_status()
        j = response.json()
        d = j["daily"]
        rows = [{"date": date, "tmax": d["temperature_2m_max"][i], "tmin": d["temperature_2m_min"][i], "rain": d["precipitation_sum"][i], "et0": d["et0_fao_evapotranspiration"][i], "wind": d["wind_speed_10m_max"][i]} for i, date in enumerate(d["time"])]
        return {"location": location, "days": validate_days(rows), "source": "LIVE · Open-Meteo forecast", "demo": False}
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError, WeatherError) as ex:
        raise WeatherError(f"Live forecast unavailable: {ex}") from ex


def demo_forecast() -> dict:
    result = json.loads((ROOT / "data" / "sample_weather.json").read_text(encoding="utf-8"))
    result["days"] = validate_days(result["days"])
    return result
