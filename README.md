# GramUrja AI

Microgrid energy-mix optimizer for off-grid and weak-grid rural communities, modelled on
a Banaskantha farm: solar PV, battery storage, a rationed agricultural grid feeder, and a
diesel backup.

## Setup

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Python 3.11 is required. `python-microgrid` 1.4.1 predates NumPy 2.0 and calls the removed
`np.product`, so the scientific stack is pinned in `requirements.txt`.

## Run the baselines

```bash
PYTHONPATH=src .venv/bin/python scripts/run_baseline.py
```

This establishes the two reference points every later savings claim is measured against:

- **Status quo** — rationed grid plus a diesel pumpset, no solar, wind or battery. The
  pumpset is sized to the pump alone, so during an outage it cannot also carry household,
  dairy and cold-storage load. That is what makes reliability fall below 100%.
- **Solar + wind + battery under rule-based control** — the same hardware the optimizer
  will use, but with simple rules instead of optimization. The gap between this and the
  Phase 4 optimizer is what the AI itself contributes.

Current default sizing generates about 160% of annual demand, which leaves the rule-based
run with very little diesel to remove and roughly 40% curtailment. Size solar and wind
closer to demand, or scale demand up to a community, before quoting a diesel-reduction
percentage.

## Layout

```
src/gramurja/
  config.py     site and economic parameters
  profiles.py   synthetic hourly solar, load and grid-availability series
  farm.py       assembles the pymgrid Microgrid
  baseline.py   rule-based reference runs
  kpi.py        diesel, cost, CO2 and reliability from a run log
scripts/
  run_baseline.py
```

## Sizing

```bash
PYTHONPATH=src .venv/bin/python scripts/optimize_sizing.py [rbc|mpc]
```

Sweeps solar/wind/battery combinations over the full 8,760 hours and picks the cheapest
that holds reliability, costing capital by recovery factor over each asset's life.

Sizing depends on the controller, and not by a little. Under rule-based control the optimum
carries no battery at all; under the optimiser it carries one and roughly doubles the
diesel reduction. A myopic controller never buys cheap agricultural-feeder power to
displace diesel later, so it values storage at nothing and sizes it away.

Current recommendation, on real 2025 weather and day-ahead forecasts: **3 kWp solar, no
wind, 5 kWh battery** -- Rs 84,565/yr all-in against a Rs 167,737/yr status quo, 83% less
diesel, reliability 94.1% to 100%. The cost surface is flat, with the top dozen
configurations inside 7%, so the exact sizing is not critical. Spending Rs 1,460/yr more
for 10 kWh of battery instead of 5 buys another 10 points of diesel reduction.

## Weather

Solar and wind come from measured Open-Meteo data for Palanpur, cached under `data/weather`.
Real weather matters: the synthetic profiles this replaced overstated solar yield by about
a third (1,946 vs 1,490 kWh/kWp) and wind by an order of magnitude. Measured wind at this
site runs a 1.2% capacity factor -- mean speed 2.5 m/s, below cut-in most of the year --
so wind is not a viable source here regardless of its cost.

Day-ahead forecast error is calibrated against Open-Meteo's own archived model runs for
this location: 17.5% mean absolute error on daylight irradiance.

## Status

Phases 1-4 are working: simulation, baselines, sizing, forecasting, and a receding-horizon
optimiser. Under realistic forecasts the optimiser retains 88% of its perfect-foresight
advantage over rule-based control, and forecast error costs about 5% of total energy cost.

## Emissions

Carbon is priced in both the dispatch objective (`MPCConfig`) and the sizing objective
(`CapexAssumptions`), via `carbon_price_inr_per_kg`.

Pricing carbon does nothing to dispatch. Grid power is 0.71 kg CO2/kWh and diesel 0.81, so
the two are within a few percent once battery round-trip losses are counted, and there is
no cleaner option for the controller to switch to. Even at Rs 50/kg, emissions move under
1%. Emissions are set by what is installed, not by how it is run.

Sizing is where carbon bites. Raising the price buys more solar, and the resulting
abatement is cheap: going from the cost-optimal system to the Rs 5/kg system cuts emissions
49% instead of 35% for about Rs 5,200/yr more, an abatement cost near Rs 3/kg -- below most
estimates of the social cost of carbon. Pushing to 69% costs roughly Rs 8/kg abated.

Note that the farmer pays that extra cost while the carbon benefit is external, so without
an incentive the farmer rationally buys the smaller system. That gap is an argument aimed
at the agencies and NGOs in the problem statement rather than at the farmer.

All profiles are synthetic and the economic parameters are planning assumptions. They must
be replaced with metered data and current Gujarat tariffs before any savings figure is
published.
