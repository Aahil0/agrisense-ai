"""Transparent heuristic decision model. Scores are NOT crop failure probabilities."""
from __future__ import annotations


def assess_risk(days: list[dict], crop: dict, stage: str) -> dict:
    if stage not in crop["stages"]:
        raise ValueError("Unknown crop stage")
    heat_threshold = float(crop["heat_c"])
    rain_threshold = float(crop["heavy_rain_mm"])
    et0_threshold = float(crop["dry_et0_mm"])
    per_day = []
    alerts = []
    for day in days:
        score, reasons = 0, []
        if day["tmax"] >= heat_threshold:
            score += 35
            reasons.append(f"Maximum temperature {day['tmax']:.1f}°C ≥ {heat_threshold:g}°C heat trigger")
        if day["tmax"] >= heat_threshold + 4:
            score += 15
            reasons.append("Additional extreme-heat trigger")
        if day["rain"] >= rain_threshold:
            score += 40
            reasons.append(f"Rainfall {day['rain']:.1f} mm ≥ {rain_threshold:g} mm heavy-rain trigger")
        if day["rain"] < 1 and day["et0"] >= et0_threshold:
            score += 25
            reasons.append(f"Low rain ({day['rain']:.1f} mm) with reference ET₀ {day['et0']:.1f} mm")
        if day["wind"] >= 40:
            score += 20
            reasons.append(f"Peak wind {day['wind']:.1f} km/h ≥ 40 km/h")
        score = min(100, score)
        label = "High" if score >= 60 else "Moderate" if score >= 25 else "Low"
        record = {"date": day["date"], "score": score, "label": label, "reasons": reasons}
        per_day.append(record)
        if reasons:
            alerts.append(record)
    peak = max(per_day, key=lambda r: r["score"])
    return {"overall": peak["label"], "score": peak["score"], "peak_date": peak["date"], "timeline": per_day, "alerts": alerts, "note": "Scores are scenario-based heuristic indices, not probabilities or validated crop-loss forecasts."}
