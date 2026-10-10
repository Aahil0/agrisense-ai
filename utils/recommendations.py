"""Clear actions tied to evaluated conditions."""

def recommendations(risk, irrigation):
    actions = [{"title": "Irrigation planning", "message": irrigation["action"]}]
    all_reasons = " ".join(" ".join(a["reasons"]) for a in risk["alerts"])
    if "heat trigger" in all_reasons:
        actions.append({"title": "Heat watch", "message": "Inspect crop for visible heat stress and check water availability; avoid claiming a disease diagnosis from weather alone."})
    if "heavy-rain trigger" in all_reasons:
        actions.append({"title": "Heavy rain watch", "message": "Check drainage and avoid field operations when soils are waterlogged."})
    if "Peak wind" in all_reasons:
        actions.append({"title": "Wind watch", "message": "Secure loose infrastructure and check local weather warnings."})
    if len(actions) == 1:
        actions.append({"title": "Routine monitoring", "message": "Keep observing soil moisture and consult local agronomy advice for crop-specific decisions."})
    return actions
