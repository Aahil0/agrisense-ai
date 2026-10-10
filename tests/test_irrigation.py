import json
from pathlib import Path
from services.irrigation import irrigation_advice
from services.weather_api import demo_forecast

crop = json.loads((Path(__file__).resolve().parents[1] / "config/crop_profiles.json").read_text())["Maize"]

def test_valid_advice():
    output = irrigation_advice(demo_forecast()["days"], crop, "Flowering", "Sandy", "Dry")
    assert output["priority"] == "High"
    assert output["indicative_crop_demand_3d"] > 0

def test_wet_soil_reduces_priority():
    data = demo_forecast()["days"]
    a = irrigation_advice(data, crop, "Seedling", "Sandy", "Dry")
    b = irrigation_advice(data, crop, "Seedling", "Clayey", "Wet")
    assert a["index"] > b["index"]
