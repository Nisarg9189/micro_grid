# GRAMURJA AI: API Contract

This document outlines the exact request and response schemas for the Python FastAPI backend, based on inspection of `src/gramurja/api.py`.

## 1. Global Request Schema (`Params`)

Both `/api/simulate` and `/api/advice` accept the exact same JSON payload. All fields have defaults in the backend, meaning they are technically optional in the request, but for strictness, the frontend should send them or rely on known backend defaults.

```json
{
  "lat": 24.17,
  "lon": 72.43,
  "site": "Palanpur, Banaskantha",
  "year": 2025,
  "days": 30,
  "solar": 3.0,
  "wind": 0.0,
  "battery": 5.0,
  "battery_reserve": 0.20,
  "c_rate": 0.25,
  "hub_height": 18.0,
  "genset_kw": 6.0,
  "pump_kw": 3.73,
  "household_kw": 0.4,
  "dairy_kw": 1.2,
  "cold_storage_kw": 0.8,
  "diesel_price": 98.39,
  "ag_tariff": 1.50,
  "village_tariff": 5.00,
  "ag_kw": 10.0,
  "village_kw": 3.0,
  "carbon_price": 0.0,
  "grid_carbon": 0.71,
  "advice_day": 5,
  "language": "english"
}
```

## 2. `POST /api/simulate`

**Purpose:** Runs the microgrid LP optimization over the specified horizon (`days`). Minimum horizon is 7 days.

### Response Schema
```json
{
  "meta": {
    "days": 30,
    "site": "Palanpur, Banaskantha",
    "caveat": "30-day horizon, not an annual figure..."
  },
  "resource": {
    "solar_kwh_per_kwp_year": 1825.0,
    "wind_capacity_factor_pct": 0.0,
    "demand_kwh": 450.0,
    "peak_kw": 6.13
  },
  "kpis": {
    "status_quo": {
      "diesel_litres": 150.5,
      "cost_inr": 25000.0,
      "reliability_pct": 95.5,
      "unmet_kwh": 12.5,
      "co2_kg": 850.0,
      "grid_kwh": 350.0,
      "renewable_pct": 45.0
    },
    "rules": { ... },
    "optimiser": {
      "diesel_litres": 20.0,
      "cost_inr": 8500.0,
      "reliability_pct": 100.0,
      "unmet_kwh": 0.0,
      "co2_kg": 250.0,
      "grid_kwh": 200.0,
      "renewable_pct": 82.5
    }
  },
  "series": {
    "load_kw": [1.2, 1.3, ...],
    "solar_kw": [0.0, 0.0, 1.5, ...],
    "ag_kw": [0.0, 0.0, ...],
    "village_kw": [1.2, 1.3, ...],
    "diesel_kw": [0.0, 0.0, ...],
    "discharge_kw": [0.0, 0.0, ...],
    "charge_kw": [0.0, 0.0, ...],
    "soc": [0.8, 0.75, ...],
    "ag_available": [1, 1, 0, ...],
    "village_available": [1, 1, 1, ...],
    "carbon_kg_per_kwh": [0.71, 0.71, ...]
  }
}
```

## 3. `POST /api/advice`

**Purpose:** Evaluates the best irrigation start time for a specific day (`advice_day`) within the simulation horizon.

### Response Schema
```json
{
  "day": 5,
  "best_start": 10,
  "hours_needed": 4.0,
  "cost_saved_inr": 120.0,
  "diesel_saved_litres": 2.5,
  "options": [
    {
      "start_hour": 8,
      "cost_inr": 150.0,
      "diesel_litres": 1.2
    },
    {
      "start_hour": 10,
      "cost_inr": 30.0,
      "diesel_litres": 0.0
    }
  ],
  "briefing": "The optimal time to run the pump is 10:00. This avoids diesel use and utilizes peak solar availability...",
  "message": "...", 
  "language": "english",
  "numbers_verified": true,
  "unverified_numbers": []
}
```
*(Note: `message`, `language`, `numbers_verified`, and `unverified_numbers` are only present if `language != "english"`, but we will default to english for the dashboard.)*

## 4. Error Responses

FastAPI Validation Error (`HTTP 422 Unprocessable Entity`):
```json
{
  "detail": [
    {
      "loc": ["body", "days"],
      "msg": "Input should be greater than or equal to 7",
      "type": "greater_than_equal",
      "ctx": { "ge": 7 }
    }
  ]
}
```

Standard Error (`HTTP 400`/`500`):
```json
{
  "detail": "An internal simulation error occurred."
}
```
