# GRAMURJA AI: Backend Integration Report

## 1. BACKEND FRAMEWORK
- **Framework:** FastAPI
- **Python Version:** 3.x (numpy 1.26.4, pandas 2.1.4, cvxpy 1.4.3)
- **Backend Entry Point:** `gramurja/api.py` (served via `scripts/serve.py` using `uvicorn`)
- **API Base URL:** `http://127.0.0.1:8000` (by default via `scripts/serve.py`)
- **CORS:** **NOT CONFIGURED.** The backend lacks `CORSMiddleware`. We will need to configure Vite proxy or update the backend to allow requests from the React dev server, or configure the frontend to talk to a proxy.
- **Database:** None. The system operates statelessly as an analytical simulation engine rather than a live SCADA data logger.

## 2. AVAILABLE ENDPOINTS

### GET Endpoints
- `GET /` - Serves a static HTML page (`report/console.html`). No dashboard data endpoint exists.

### POST Endpoints
- `POST /api/simulate` - Runs the full microgrid simulation (baseline, rules, and MPC optimizer) for a specified number of days and returns KPIs and hourly series data.
- `POST /api/size` - Runs a sizing sweep to find optimal hardware configurations.
- `POST /api/advice` - Generates irrigation advice (best start hours, savings) based on the forecast.

### WEBSOCKET Endpoints
- **None.** The backend does not support WebSockets, SSE, or MQTT.

## 3. SCHEMAS

### Global Request Schema (`Params`)
All POST endpoints accept the same JSON payload describing the site and hardware:
```json
{
  "lat": 24.17, "lon": 72.43, "site": "Palanpur, Banaskantha",
  "year": 2025, "days": 30,
  "solar": 3.0, "wind": 0.0,
  "battery": 5.0, "battery_reserve": 0.20, "c_rate": 0.25,
  "hub_height": 18.0, "genset_kw": 6.0,
  "pump_kw": 3.73, "household_kw": 0.4, "dairy_kw": 1.2, "cold_storage_kw": 0.8,
  "diesel_price": 98.39, "ag_tariff": 1.50, "village_tariff": 5.00,
  "ag_kw": 10.0, "village_kw": 3.0,
  "carbon_price": 0.0, "grid_carbon": 0.71,
  "advice_day": 5, "language": "english"
}
```

### `/api/simulate` Response Schema (Energy & KPIs)
```json
{
  "meta": { "days": 30, "site": "...", "caveat": "..." },
  "resource": { "solar_kwh_per_kwp_year": 1234, ... },
  "kpis": {
    "status_quo": { "diesel_litres": 100, "cost_inr": 5000, "co2_kg": 200, ... },
    "rules": { ... },
    "optimiser": { "diesel_litres": 20, "cost_inr": 1000, "co2_kg": 50, ... }
  },
  "series": {
    "load_kw": [1.2, 1.3, ...],
    "solar_kw": [0, 0, 1.5, ...],
    "ag_kw": [0, 0, ...],
    "village_kw": [1.2, 1.3, ...],
    "diesel_kw": [0, 0, ...],
    "discharge_kw": [0, 0, ...],
    "charge_kw": [0, 0, ...],
    "soc": [80, 75, ...],
    "ag_available": [1, 1, 0, ...],
    "village_available": [1, 1, 1, ...]
  }
}
```

### `/api/advice` Response Schema (Optimizer Recommendation)
```json
{
  "day": 5,
  "best_start": 10,
  "hours_needed": 4,
  "cost_saved_inr": 120,
  "diesel_saved_litres": 2.5,
  "options": [ { "start_hour": 10, "cost_inr": 50, "diesel_litres": 0 }, ... ],
  "briefing": "..."
}
```

## 4. AUTHENTICATION & ERROR FORMAT
- **Authentication:** None.
- **Error Format:** Standard FastAPI `HTTPException` format (`{ "detail": "error message" }` or Pydantic validation errors `{"detail": [ { "loc": [...], "msg": "...", "type": "..." } ] }`).

## 5. CAPABILITIES MAP

### REAL
- **Energy Telemetry:** Historical/simulated energy series data via `POST /api/simulate` (`series` field).
- **Dashboard KPIs:** Real metrics returned via `POST /api/simulate` (`kpis.optimiser` field).
- **AI Optimizer (Execution & Recommendation):** Real optimization happens in `POST /api/simulate` (dispatch) and `POST /api/advice` (irrigation scheduling recommendation).
- **Optimizer Engine:** PuLP/CBC is used via `cvxpy`.

### SIMULATED (Kept in DEMO_MODE)
- **Real-Time Data:** The backend does not stream live data. It returns fixed arrays representing a horizon (e.g., 30 days). We will use this to populate the charts, but it won't "tick" live.
- **Generator Control (Start/Stop):** No endpoints exist to control a physical generator.
- **Sensor Calibration:** No endpoints exist to calibrate physical sensors.
- **Infrastructure Status:** The backend takes hardware capacities as *inputs* (`Params`), it does not query live sensors for "health" or "status".

### NOT IMPLEMENTED
- Live SCADA WebSocket streams.
- Database persistence.
