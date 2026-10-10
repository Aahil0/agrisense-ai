import json
from pathlib import Path
from services.risk_engine import assess_risk
from services.weather_api import demo_forecast

crop = json.loads((Path(__file__).resolve().parents[1] / "config/crop_profiles.json").read_text())["Wheat"]

def test_demo_alerts():
    result = assess_risk(demo_forecast()["days"], crop, "Vegetative")
    assert result["overall"] == "High"
    assert len(result["timeline"]) == 7
    assert result["score"] <= 100

def test_low_risk():
    days = [{"date": "test", "tmax": 22, "rain": 4, "et0": 2, "wind": 6}]
    assert assess_risk(days, crop, "Seedling")["score"] == 0

def test_unknown_stage():
    import pytest
    with pytest.raises(ValueError): assess_risk(demo_forecast()["days"], crop, "unknown")
