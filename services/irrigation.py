"""Advisory water-demand screening, not a field-calibrated irrigation prescription."""


def irrigation_advice(days: list[dict], crop: dict, stage: str, soil: str, moisture: str) -> dict:
    if stage not in crop["stages"]:
        raise ValueError("Unknown crop stage")
    if soil not in ("Sandy", "Loamy", "Clayey") or moisture not in ("Dry", "Moderate", "Wet"):
        raise ValueError("Unknown field conditions")
    window = days[:3]
    et0 = sum(d["et0"] for d in window)
    rain = sum(d["rain"] for d in window)
    kc = float(crop["kc"]) * float(crop["stages"][stage])
    indicative_demand = et0 * kc
    # Rainfall cannot be treated as equal to effective rainfall. This figure is contextual only.
    score = {"Dry": 45, "Moderate": 20, "Wet": 0}[moisture]
    score += {"Sandy": 15, "Loamy": 7, "Clayey": 0}[soil]
    score += min(30, round(indicative_demand * 2))
    if rain >= 20: score -= 35
    elif rain >= 8: score -= 18
    score = max(0, min(100, score))
    priority = "High" if score >= 65 else "Moderate" if score >= 35 else "Low"
    if priority == "High":
        action = "Check root-zone soil moisture soon and consider irrigation only after local field verification."
    elif priority == "Moderate":
        action = "Monitor root-zone moisture and upcoming rainfall before planning irrigation."
    else:
        action = "Avoid unnecessary irrigation; recheck soil moisture as conditions change."
    return {"priority": priority, "index": score, "et0_3d": round(et0, 1), "rain_3d": round(rain, 1), "indicative_crop_demand_3d": round(indicative_demand, 1), "action": action, "note": "Screening only. ET₀ × illustrative crop coefficient is not a verified irrigation volume; rainfall is not effective rainfall. Verify local crop coefficients, soil depth, and field moisture."}
