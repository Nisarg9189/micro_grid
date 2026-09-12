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

## Run it

```bash
PYTHONPATH=src .venv/bin/python scripts/run_baseline.py
```

About twenty seconds, and it prints the whole argument: a year of hourly simulation on the
recommended system, under three controllers.

- **Status quo** — rationed grid plus a diesel pumpset, no solar, wind or battery. The
  pumpset is sized to the pump alone, so during an outage it cannot also carry household,
  dairy and cold-storage load. That is what makes reliability fall below 100%.
- **Rule-based** — the same hardware, run by simple rules. This is the honest comparison,
  because it isolates what the optimisation contributes from what the hardware does.
- **Optimiser** — the same hardware again, dispatched by the receding-horizon program
  planning on a day-ahead forecast rather than on perfect foresight.

| | Status quo | Rule-based | Optimiser |
| --- | --- | --- | --- |
| Diesel | 1,080 L | 368 L | 184 L |
| Energy cost | Rs 167,737 | Rs 71,869 | Rs 53,002 |
| Reliability | 94.1% | 100% | 100% |
| CO2 | 12,166 kg | 8,294 kg | 8,291 kg |

The optimiser removes a further 184 L of diesel and Rs 18,867 a year beyond what the rules
achieve on identical hardware -- 26% of the remaining bill. Note the CO2 column: halving the
diesel moves emissions by 4 kg in a year, essentially nothing. The optimiser displaces diesel
largely by importing more grid power, and once battery round-trip losses are counted the two
emit about the same per kWh delivered. Cost and carbon are not the same objective here.

## Layout

```
src/gramurja/
  config.py     site, economic and feeder parameters
  weather.py    Open-Meteo client, and irradiance/wind to generator output
  profiles.py   hourly demand, feeder roster, and generation from weather
  forecast.py   what the controller believes, as distinct from what happens
  farm.py       assembles the pymgrid Microgrid
  baseline.py   status-quo and rule-based reference runs
  mpc.py        receding-horizon dispatch, as a cvxpy linear program
  sizing.py     capital costing and the parallel configuration sweep
  kpi.py        diesel, cost, CO2 and reliability from a run log
scripts/
  run_baseline.py       the two reference runs
  optimize_sizing.py    derive hardware for the Banaskantha farm
  village_scenario.py   the coastal village case, where wind competes
  village_microgrid.py  a whole Banaskantha village, not one farm
  validate_forecast.py  synthesised forecast vs genuine archived forecasts
report/
  mid-evaluation.html   results write-up
  architecture.html     system and agent-layer diagrams
```

The capacities in `DEFAULT_CONFIG` are reference values that the sizing sweep scales
candidates against, not a recommended system. They are deliberately larger than anything
worth installing, and `wind_capacity_kw` must stay non-zero because candidate scaling
divides by it. Scripts that run a specific system build their own config instead.

## Sizing

```bash
PYTHONPATH=src .venv/bin/python scripts/optimize_sizing.py [mpc|rbc]
```

Sweeps solar/wind/battery combinations over the full 8,760 hours and picks the cheapest
that holds reliability, costing capital by recovery factor over each asset's life. Defaults
to the optimiser; pass `rbc` to reproduce the rule-based sizing. Takes a few minutes, since
each candidate is a full year of simulation.

Sizing depends on the controller, and not by a little. Under rule-based control the optimum
carries no battery at all; under the optimiser it carries one and roughly doubles the
diesel reduction. A myopic controller never buys cheap agricultural-feeder power to
displace diesel later, so it values storage at nothing and sizes it away.

Current recommendation, on 2025 reanalysis weather and day-ahead forecasts: **3 kWp solar, no
wind, 5 kWh battery** -- Rs 84,565/yr all-in against a Rs 167,737/yr status quo, 83% less
diesel, reliability 94.1% to 100%. The cost surface is flat, with the top dozen
configurations inside 7%, so the exact sizing is not critical. Spending Rs 1,460/yr more
for 10 kWh of battery instead of 5 buys another 10 points of diesel reduction.

## Weather

Solar and wind come from Open-Meteo's archive for Palanpur, cached under `data/weather`.

That archive serves **ERA5 reanalysis**, not station readings: a physics model that
assimilates real observations onto a grid of roughly 9-30 km cells. It is
observation-grounded and the standard source for studies of this kind, but it is not a
pyranometer in a field at Palanpur, and a site survey would be the next step before
committing capital.

Grounding the model in it still changed the answers substantially. The synthetic profiles
it replaced overstated solar yield by about a third (1,946 against 1,490 kWh/kWp) and wind
by an order of magnitude. Reanalysis wind at this site runs a 1.2% capacity factor -- mean
speed 2.5 m/s, below turbine cut-in most of the year -- so wind is not viable here
regardless of its cost.

## Forecasts, and how real they are

The controller plans on a day-ahead forecast rather than on the truth. That forecast is
**synthesised, not downloaded**: `forecast_weather` perturbs the reanalysis irradiance with
day-correlated noise scaled to the error Open-Meteo's own model actually makes at this
site, 17.5% mean absolute error on daylight irradiance. Errors persist within a day rather
than varying hour to hour, because a model that misses a cloud bank is wrong all afternoon
and white noise would let the optimiser average the mistake away.

Synthesis is necessary because the archive of past forecasts reaches back roughly 92 days,
which is not a year. Over the window where genuine forecasts *do* exist, the substitution
can be checked:

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_forecast.py
```

This runs the optimiser three times over the same 93 days of reanalysis weather -- once with
perfect foresight, once on Open-Meteo's genuine archived day-ahead forecasts, and once on
the synthesised series:

| Forecast | Diesel | Cost | Penalty vs perfect foresight |
| --- | --- | --- | --- |
| perfect | 45.8 L | Rs 15,065 | -- |
| archived, genuine | 51.9 L | Rs 15,622 | Rs 557 |
| synthesised | 51.6 L | Rs 15,582 | Rs 517 |

The synthesised forecast reproduces **93% of the cost penalty a real forecast imposes**, so
the annual figures elsewhere in this README are a mild upper bound rather than a different
kind of claim. Reliability is 100% under all three.

## Another site, where wind competes

```bash
PYTHONPATH=src .venv/bin/python scripts/village_scenario.py
```

Runs the same engine at Dwarka on the Saurashtra coast, at village scale: twenty farms
sharing one 80 m turbine, which is plausible where a single farm's mast is not. Hub height
matters more than the site does -- 18 m to 80 m lifts the capacity factor from 8.6% to
22.2%, because a farm mast sits in slow surface wind.

There wind misses the optimum by 0.75% and enters it below Rs 60,000/kW, and as it cheapens
the optimiser buys more of it and retires solar. The engine follows the resource rather
than carrying a bias against wind; Banaskantha simply has none. Wind is a community
technology here, not a farm one.

## A whole village, not one farm

```bash
PYTHONPATH=src .venv/bin/python scripts/village_microgrid.py
```

The problem statement asks about off-grid *communities*, so the same engine is pointed at a
Banaskantha village: 100 households, 20 farms, a dairy chilling centre and the drinking-water
supply -- 157,273 kWh/yr in total.

A village is not one farm multiplied. Two things change. **Diversity**: twenty pumps on their
own schedules peak at 29.8 kW rather than the 74.6 kW they would draw together, a factor of
0.40, and that spread is the whole argument for sharing infrastructure. **The peak moves to
the evening**: households dominate and peak at 31 kW at 19:00 when solar is zero, against a
10.9 kW trough at 13:00 when solar is strongest.

### Feeder routing has to be explicit here

At farm scale the rule that pumps cannot use the domestic feeder came for free -- a 3 kW
single-phase connection cannot start a 3.73 kW pump. A 50 kW village transformer can, so the
rule must be stated: agricultural and domestic supplies are separately sanctioned and
separately tariffed, and neither may serve the other's load. Feeders now declare what they
serve, and grid power reaches the battery only through a connection already allowed to supply
the domestic side -- otherwise storage launders agricultural-tariff power.

Enforcing it changes the answer completely:

| | Without routing | With routing |
| --- | --- | --- |
| Solar | 20 kWp | **40 kWp** |
| Battery | **0 kWh** | **100 kWh** |
| Diesel | 2,014 L | **937 L** |
| CO2 cut | 33.0% | **47.7%** |
| Saved per household | Rs 19,244 | **Rs 16,524** |

Storage goes from worthless to essential, because the ~69% of hours when the agricultural
feeder is down must then be covered by solar, battery or diesel. Every one of the ten
cheapest configurations carries a battery. The earlier per-household figure was inflated by a
model quietly running pumps off a domestic connection.

### Result

**40 kWp solar, no wind, 100 kWh battery**

| Metric | Status quo | Recommended |
| --- | --- | --- |
| Diesel | 21,970 L/yr | **937 L/yr** (−95.7%) |
| Total cost | Rs 2,707,313/yr | **Rs 1,054,954/yr** |
| Reliability | 94.7% | **100%** |
| Unserved load | 8,306 kWh/yr | **0** |
| CO2 | 149,246 kg/yr | **78,116 kg/yr** (−47.7%) |

Saving **Rs 1,652,359/yr, Rs 16,524 per household**. Status-quo diesel works out to 1,098 L
per farm against 1,080 L from the independent single-farm run -- within 1.7%, from a
different load model.

Every figure in the village load model is an assumption: 2.5 kWh/day per household, a 5 kW
bulk milk cooler, four hours of water pumping. Structurally realistic, none of it metered.

## Status

Phases 1-4 are working: simulation, baselines, sizing, forecasting, and a receding-horizon
optimiser. Under realistic forecasts the optimiser retains 88% of its perfect-foresight
advantage over rule-based control, and forecast error costs about 5% of total energy cost.

## Emissions

Carbon is priced in both the dispatch objective (`MPCConfig`) and the sizing objective
(`CapexAssumptions`), via `carbon_price_inr_per_kg`.

Grid carbon intensity varies through the day rather than sitting at one number: utility
solar pushes the midday trough to 0.515 kg/kWh while the post-sunset peak runs 0.890, a
73% spread around a 0.710 annual mean. That shape is what makes storage worth anything for
emissions. Against a flat intensity a battery cannot help at all -- storing a kWh to avoid
carbon later costs more in round-trip losses than it saves, and the optimiser correctly
refuses to do it at any carbon price, even Rs 50/kg. Against a varying one it can charge
clean and discharge dirty.

| Carbon price | Solar | Battery | Diesel | CO2 | CO2 cut | Farmer's bill | Abatement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Rs 0/kg | 3 kWp | 5 kWh | 182 L | 8,302 kg | 31.8% | Rs 84,565 | -- |
| Rs 2/kg | 3 kWp | 5 kWh | 197 L | 8,110 kg | 33.3% | Rs 86,079 | Rs 7.89/kg |
| Rs 5/kg | 5 kWp | 10 kWh | 94 L | 6,350 kg | 47.8% | Rs 92,709 | Rs 4.17/kg |
| Rs 15/kg | 8 kWp | 20 kWh | 34 L | 3,855 kg | 68.3% | Rs 119,718 | Rs 7.91/kg |

The farmer's bill column strips out the notional carbon charge, which nobody actually pays;
abatement is measured against the Rs 0 row.

Two different mechanisms are at work. At Rs 2/kg the hardware does not change at all -- the
gain is pure dispatch, the optimiser re-timing the battery to charge through the midday
trough and discharge into the evening peak, worth 192 kg a year for no capital whatsoever.
From Rs 5/kg upward it buys capacity instead, and capacity is the cheaper lever: Rs 4.17/kg
against Rs 7.89 for re-timing, because it removes far more carbon per rupee spent.

The farmer pays that extra cost while the carbon benefit is external, so without an
incentive the farmer rationally buys the smaller system. That gap is an argument aimed at
the agencies and NGOs in the problem statement rather than at the farmer.

## What is grounded in data and what is not

Solar and wind generation come from ERA5 reanalysis for the site, and the forecast error the
controller runs against is calibrated to this location's real day-ahead error and validated
against genuine archived forecasts. Demand is not: the household, dairy and cold-storage profiles
are constructed, and cold storage alone drives roughly 40% of annual load. Irrigation is
grounded in surveyed pump hours.

Capital costs and tariffs are planning assumptions, and the sizing result is genuinely
sensitive to battery capital. Replace both with metered demand and vendor quotes before
publishing any savings figure.
