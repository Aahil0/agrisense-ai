"""AgriSense AI — agricultural risk decision-support prototype."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.weather_api import geocode, live_forecast, demo_forecast, WeatherError
from services.risk_engine import assess_risk
from services.irrigation import irrigation_advice
from utils.recommendations import recommendations

ROOT = Path(__file__).resolve().parent
PROFILES = json.loads((ROOT / "config/crop_profiles.json").read_text(encoding="utf-8"))
st.set_page_config(page_title="AgriSense AI | Farm Intelligence", page_icon="🌾", layout="wide")
st.markdown("""<style>
.stApp {background:#f7faf5;color:#142b21}
.block-container {padding-top:1.8rem;max-width:1260px}
h1,h2,h3 {color:#173a2b!important}
[data-testid="stMetric"] {border:1px solid #dce9dd;background:white;padding:17px;border-radius:14px}
div.stButton > button[kind="primary"] {background:#166534;border-color:#166534;color:white}
.hero {padding:27px 30px;border-radius:20px;background:linear-gradient(115deg,#153e2a,#28764d);color:#fff;margin-bottom:18px}
.hero h1 {color:white!important;margin:0;font-size:2.4rem}
.hero p {color:#d7f3df;margin:8px 0 0}
.smallnote {font-size:0.86rem;color:#496a55}
</style>""", unsafe_allow_html=True)

st.markdown('<div class="hero"><div style="font-weight:700;letter-spacing:2px;font-size:12px">HACKOVERFLOW 10.0 · AGRICULTURE</div><h1>🌾 AgriSense AI</h1><p>Understand the forecast. Identify crop risks. Make more informed farm decisions.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("🌱 Your field")
    mode = st.radio("Data source", ["Live weather", "Offline demo"], help="Offline demo uses labeled synthetic values and works without internet.")
    city = st.text_input("Indian city", "Pune", disabled=(mode == "Offline demo"))
    crop_name = st.selectbox("Crop", list(PROFILES))
    crop = PROFILES[crop_name]
    stage = st.selectbox("Growth stage", list(crop["stages"]))
    soil = st.selectbox("Soil type", ["Loamy", "Sandy", "Clayey"])
    moisture = st.selectbox("Observed soil moisture", ["Moderate", "Dry", "Wet"], help="User judgment, not sensor-verified soil moisture.")
    run = st.button("🔎 Analyze my farm", type="primary", use_container_width=True)
    st.divider()
    st.caption("Educational decision support. Not a crop-loss prediction, disease diagnosis, or calibrated irrigation prescription.")

@st.cache_data(ttl=1800, show_spinner=False)
def get_live(city_name):
    return live_forecast(geocode(city_name))

if "analysis" not in st.session_state:
    st.session_state.analysis = None
if run:
    try:
        with st.spinner("Analyzing forecast and crop conditions..."):
            weather = demo_forecast() if mode == "Offline demo" else get_live(city)
            risk = assess_risk(weather["days"], crop, stage)
            irrigation = irrigation_advice(weather["days"], crop, stage, soil, moisture)
            advice = recommendations(risk, irrigation)
            st.session_state.analysis = {"weather":weather,"risk":risk,"irrigation":irrigation,"advice":advice,"inputs":{"crop":crop_name,"stage":stage,"soil":soil,"moisture":moisture},"retrieved":datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
    except (WeatherError, ValueError) as ex:
        st.session_state.analysis = None
        st.error(f"Could not complete analysis: {ex}")
        st.info("Select Offline demo and analyze again to see the entire workflow without network access.")

result = st.session_state.analysis
if result is None:
    st.info("👈 Select your crop and location in the sidebar, then click **Analyze my farm**. Try **Offline demo** for a fully reproducible walkthrough.")
    a,b,c = st.columns(3)
    with a: st.markdown("### ☀️ Weather-aware\nSeven-day forecast converted into interpretable indicators.")
    with b: st.markdown("### 🛡️ Explainable risks\nSee the exact thresholds behind each warning.")
    with c: st.markdown("### 💧 Irrigation support\nDecision screening using rainfall and moisture conditions.")
    st.stop()

weather, risk, irrigation = result["weather"], result["risk"], result["irrigation"]
loc = weather["location"]
st.subheader(f"Farm outlook · {loc['name']}, {loc.get('admin1','India')}")
if weather["demo"]:
    st.warning("🧪 **SYNTHETIC OFFLINE DEMO** — dates and weather values are illustrative, NOT live observations or forecasts.")
else:
    st.success("🟢 LIVE FORECAST · Open-Meteo. These are forecast estimates, not ground measurements.")
st.caption(f"Source: {weather['source']} · Loaded: {result['retrieved']} · Crop: {result['inputs']['crop']} · Growth: {result['inputs']['stage']}")

days = weather["days"]
summary1, summary2, summary3, summary4 = st.columns(4)
summary1.metric("Overall weather risk", risk["overall"], help="Highest daily heuristic category in the seven-day period")
summary2.metric("Peak risk index", f"{risk['score']}/100", help="Heuristic index, not crop failure probability")
summary3.metric("Irrigation priority", irrigation["priority"], help="Requires local verification")
summary4.metric("Rain next 3 days", f"{irrigation['rain_3d']:.1f} mm", help="Forecast rainfall, not effective rainfall")

t1,t2,t3 = st.tabs(["📊 Forecast intelligence", "🛡️ Alerts & actions", "🔬 Model transparency"])
with t1:
    df = pd.DataFrame(days)
    df["risk_score"] = [x["score"] for x in risk["timeline"]]
    c1,c2 = st.columns(2)
    with c1:
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=df.date,y=df.tmax,mode="lines+markers",name="Maximum °C",line=dict(color="#e68c32",width=3)))
        fig.add_trace(go.Scatter(x=df.date,y=df.tmin,mode="lines+markers",name="Minimum °C",line=dict(color="#288b87",width=2)))
        fig.update_layout(title="Temperature forecast",yaxis_title="°C",margin=dict(l=15,r=15,t=48,b=15),height=330,legend=dict(orientation="h"),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)
    with c2:
        fig=go.Figure(go.Bar(x=df.date,y=df.rain,marker_color="#3d9ed1",name="Rainfall"))
        fig.update_layout(title="Daily precipitation",yaxis_title="mm",margin=dict(l=15,r=15,t=48,b=15),height=330,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)
    fig=go.Figure(go.Scatter(x=df.date,y=df.risk_score,fill="tozeroy",mode="lines+markers",line=dict(color="#e3a33a",width=3)))
    fig.update_layout(title="Explainable heuristic risk index by day",yaxis=dict(range=[0,100],title="Index / 100"),height=300,margin=dict(l=15,r=15,t=48,b=15),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig,use_container_width=True)
    st.dataframe(df.rename(columns={"date":"Day","tmax":"Max °C","tmin":"Min °C","rain":"Rain mm","et0":"ET₀ mm","wind":"Wind km/h","risk_score":"Risk index"}),hide_index=True,use_container_width=True)
with t2:
    st.markdown("#### Prioritized actions")
    for item in result["advice"]:
        st.info(f"**{item['title']}** — {item['message']}")
    st.markdown("#### Triggered weather alerts")
    if risk["alerts"]:
        for alert in risk["alerts"]:
            with st.expander(f"{alert['date']} · {alert['label']} · index {alert['score']}/100"):
                for reason in alert["reasons"]: st.write(f"• {reason}")
    else: st.success("No configured weather risk threshold was triggered over this forecast window.")
    st.markdown("#### Irrigation-screening context")
    a,b,c=st.columns(3)
    a.metric("3-day ET₀",f"{irrigation['et0_3d']} mm")
    b.metric("Indicative crop water demand",f"{irrigation['indicative_crop_demand_3d']} mm")
    c.metric("Irrigation priority index",f"{irrigation['index']}/100")
    st.caption(irrigation["note"])
with t3:
    st.markdown("#### How the decision model works")
    st.write("AgriSense v0.1 uses a **transparent rule-based heuristic model**, not a fitted machine-learning estimator. Risk categories express threshold-based attention levels; they are **not** likelihoods of crop loss.")
    st.json({"crop": result['inputs']['crop'], "growth_stage": result['inputs']['stage'], "heat_trigger_c": crop["heat_c"], "heavy_rain_trigger_mm_per_day": crop["heavy_rain_mm"], "dry_et0_trigger_mm": crop["dry_et0_mm"], "illustrative_base_crop_coefficient":crop["kc"], "stage_multiplier":crop["stages"][stage]})
    st.write("**Risk index per day:** +35 heat trigger, +15 extreme heat, +40 heavy rainfall, +25 low-rain/high-ET₀ combination, +20 high wind; capped at 100. Low <25; Moderate 25–59; High ≥60. Overall category is the peak daily category.")
    st.write("**Irrigation priority:** combines self-reported soil moisture, soil texture, illustrative crop-adjusted 3-day ET₀, and forecast precipitation. It is a screening index, **not measured soil water deficit** or an irrigation volume.")
    st.warning("Prototype thresholds and crop coefficients are illustrative, not locally calibrated or agronomically validated. Consult local agricultural extension guidance before acting.")

st.divider()
st.caption("AgriSense AI · HackOverflow 10.0 · Prototype for educational decision support · Forecast source: Open-Meteo (open-meteo.com)")
