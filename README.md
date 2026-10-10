# 🌾 AgriSense AI 

**A weather-aware, explainable agricultural decision-support web app for Indian farmers.**

AgriSense turns a seven-day weather forecast and farmer-supplied crop/soil details into readable weather-risk warnings, a provisional irrigation priority, and suggested checks. The project is built with Streamlit and Python, and includes a transparent **heuristic decision model**. It is **not a trained ML model** and does not predict crop failure probabilities.

## Live demo

[Open AgriSense AI](https://agrisense-ai-aahil.streamlit.app/) — publicly deployed on Streamlit Community Cloud using Python 3.12. Both Offline demo and Live weather analysis were checked after deployment.

## What works

- Live geocoding for Indian cities and seven-day forecasts via Open-Meteo (temperature, rainfall, ET₀, wind).
- Offline synthetic demo mode, requiring no internet, with explicit sample-data labels.
- Crop profiles for Wheat, Rice, Maize and Tomato; four growth stages.
- Explainable daily risk indices and the precise thresholds behind each alert.
- Irrigation screening from forecast rainfall/ET₀ and user-reported soil moisture and soil type.
- Dynamic charts, tabular weather details, action cards, and model-transparency panel.
- Automated unit tests.

## Quick start

Python 3.10+ recommended.

```bash
git clone https://github.com/Aahil0/agrisense-ai.git
cd agrisense-ai
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local Streamlit URL shown in the terminal. Set **Offline demo** in the sidebar for a network-independent walkthrough; otherwise select **Live weather** and enter an Indian city.

## Tests

```bash
python -m pytest -q
```

The ZIP also contains an empty screenshots directory; no screenshots are bundled. Empty directories are not stored in Git.

## Implementation and data flow

`app.py` collects the city, crop, growth stage, soil texture and observed moisture through a Streamlit sidebar. Live mode geocodes the city and requests daily weather through `services/weather_api.py`; offline mode loads `data/sample_weather.json`. Live results are cached for 30 minutes. Analysis runs when **Analyze my farm** is pressed; changing sidebar inputs requires pressing the button again.

The weather rows feed `services/risk_engine.py` and `services/irrigation.py`. `utils/recommendations.py` turns triggered conditions into action cards. The dashboard presents temperature and rain charts, daily risk indices, forecast tables, alert evidence and configuration values. There is no database, login system, sensor integration, trained model or background alert delivery in this prototype.

The sample JSON contains seven fixed synthetic days labeled Demo Day 1–7, independent of the calendar. Live geocoding selects the first matching Indian location; verify the displayed city and state before interpreting results.

## Model explanation

The system deliberately uses an auditable rule engine rather than claiming accuracy from a model without an agricultural labeled dataset. Each forecast day is scored by additive triggers:

| Condition | Added score |
| --- | ---: |
| Max temperature ≥ crop heat threshold | 35 |
| Max temperature ≥ threshold + 4°C | 15 |
| Rainfall ≥ crop heavy-rain threshold | 40 |
| Rain < 1 mm and ET₀ ≥ crop dry threshold | 25 |
| Peak wind ≥ 40 km/h | 20 |

Daily scores cap at 100. Low < 25, moderate 25–59, high ≥ 60. Seven-day risk reflects the highest daily index. The irrigation index applies explicit soil-moisture, soil-type and 3-day weather rules. Parameters live in `config/crop_profiles.json` and must be locally validated before practical agricultural use.

The indicative 3-day crop water demand is calculated from **ET₀ × an illustrative crop coefficient × stage multiplier**, which is neither measured crop water use nor an irrigation volume. Forecast precipitation is not equal to effective rain. The app does not diagnose crop disease or issue automated irrigation commands.

Growth stage affects the indicative water demand and irrigation index. The daily weather-risk thresholds remain the same across growth stages for each crop.

### Irrigation index

Using the first three forecast days:

- Start with moisture points: Dry 45, Moderate 20, Wet 0.
- Add soil points: Sandy 15, Loamy 7, Clayey 0.
- Add `min(30, round(indicative_crop_demand_3d × 2))`.
- Subtract 35 for total rain ≥20 mm, or 18 for rain ≥8 mm and <20 mm.
- Clamp the result to 0–100. Low <35, Moderate 35–64, High ≥65.

Wet soil reduces the index but does not force a Low result. Always check the field before treating a priority as an action.

## Live API

[Open-Meteo forecast API](https://open-meteo.com/en/docs) and [geocoding API](https://open-meteo.com/en/docs/geocoding-api). Network requests time out with understandable messages. Live data does **not** silently fall back to synthetic data. The user must explicitly select Offline demo.

## Demo walkthrough (90 seconds)

1. Select Offline demo, Wheat, Vegetative, Sandy soil, Dry moisture.
2. Click **Analyze my farm**. Examine seven-day trends and high weather-risk alerts.
3. Open **Alerts & actions** to show evidence behind warnings and explain irrigation priority.
4. Change the reported soil moisture to Wet and run again. Compare the irrigation index.
5. Open **Model transparency** to demonstrate exactly how conditions determine output.
6. Optionally try Live weather if connectivity is available.

## Deployment

Push contents to a GitHub repository and deploy through [Streamlit Community Cloud](https://share.streamlit.io/), selecting `app.py` as the entry point. No secrets or API keys are needed for non-commercial Open-Meteo access under its terms; check provider usage and attribution conditions.

The live app is deployed from this repository's `main` branch with `app.py` as the entry point and Python 3.12. No secrets are configured.

## Troubleshooting

- **Live weather unavailable:** check internet connectivity and the city name, or explicitly select Offline demo. Live errors clear the previous analysis.
- **Module not found:** activate the same virtual environment used for installation and run `python -m streamlit run app.py`.
- **Port already in use:** run `python -m streamlit run app.py --server.port 8502`.
- **Inputs changed but results stayed the same:** press **Analyze my farm** again.

## Scope and limitations

**For educational demonstration only.** This is not a validated crop-loss model, medical-like advisory system, disease detector, or field-calibrated irrigation prescription. Weather forecasts can be wrong; field moisture is self-reported; crop coefficients and risk thresholds are illustrative. Consult trusted local agronomists and official weather warnings before making decisions. Avoid representing synthetic demo weather as actual observations.

