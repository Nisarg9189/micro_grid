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

Optionally, for the Gujarati and Hindi farmer messages only:

```bash
cp .env.example .env   # then paste a free key from https://aistudio.google.com/apikey
```

Everything else runs without it, and the advice falls back to English. No key is committed
to this repository and none should be.

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

## Changing the parameters yourself

Nothing above is hard-coded into the result. `scripts/simulate.py` takes the site, the
hardware, the loads and the tariffs on the command line, so you can point the model at a
different district or a different set of prices and see whether the conclusions survive.

```bash
# the headline case - identical to run_baseline.py
PYTHONPATH=src .venv/bin/python scripts/simulate.py

# a different district: the Saurashtra coast, with a turbine on a taller mast
PYTHONPATH=src .venv/bin/python scripts/simulate.py \
    --lat 22.24 --lon 68.97 --site "Dwarka" --wind 3 --hub-height 50

# different economics: cheaper diesel, dearer domestic power
PYTHONPATH=src .venv/bin/python scripts/simulate.py --diesel-price 60 --village-tariff 9

# put a price on carbon
PYTHONPATH=src .venv/bin/python scripts/simulate.py --carbon-price 5

# stop assuming the hardware and derive it instead (a few minutes)
PYTHONPATH=src .venv/bin/python scripts/simulate.py --sweep

# machine-readable output
PYTHONPATH=src .venv/bin/python scripts/simulate.py --json out.json
```

`--help` lists everything. The parameters worth trying first:

| Group | Flags | Default |
| --- | --- | --- |
| Site | `--lat` `--lon` `--site` `--year` | 24.17, 72.43, Palanpur, 2025 |
| Hardware | `--solar` `--wind` `--battery` | 3 kWp, 0 kW, 5 kWh |
| | `--battery-reserve` `--c-rate` `--hub-height` `--genset-kw` | 0.20, 0.25 C, 18 m, 6 kW |
| Loads | `--pump-kw` `--household-kw` `--dairy-kw` `--cold-storage-kw` | 3.73, 0.4, 1.2, 0.8 kW |
| Economics | `--diesel-price` `--ag-tariff` `--village-tariff` | Rs 98.39/L, Rs 1.50, Rs 5.00 |
| | `--ag-kw` `--village-kw` `--carbon-price` `--grid-carbon` | 10 kW, 3 kW, Rs 0/kg, 0.71 kg/kWh |
| Run | `--days` `--sweep` `--advice-day` `--json` | 365, off, day 20, none |

Two things to know when you change them.

**Any new location triggers a fresh weather download** from Open-Meteo (no key needed),
cached afterwards under `data/weather`, so the first run at a new site is slower.

**The tariffs and feeder capacities apply to all three controllers**, so the comparison
stays honest. That was not true of an earlier version of this script: overriding
`--village-tariff` priced only the optimiser and left the baselines at the default, which
made the optimiser look worse than the rules. If you see a result where the optimiser
loses, check that first -- it is more likely a pricing mismatch than a real finding.

## Every command, and what it does

| Command | Time | What it shows |
| --- | --- | --- |
| `scripts/serve.py` | instant | **Interactive console at 127.0.0.1:8000. Start here.** |
| `scripts/simulate.py` | ~40 s | Any site, hardware and tariff you pass. Start here. |
| `scripts/run_baseline.py` | ~40 s | The headline case: status quo, rule-based, optimiser |
| `scripts/optimize_sizing.py [mpc\|rbc]` | ~25 min | Derives the hardware from the load profile |
| `scripts/validate_forecast.py` | ~30 s | Synthesised forecast vs genuine archived forecasts |
| `scripts/village_microgrid.py` | ~25 min | The whole village, with feeder routing enforced |
| `scripts/village_scenario.py` | ~10 min | Coastal village where wind competes |
| `scripts/energy_sharing.py` | ~5 min | What sharing surplus between neighbours is worth |
| `scripts/combined_village.py` | ~1 min | Farms, homes, dairy and water as one village |
| `scripts/farmer_message.py [gujarati\|hindi\|english]` | ~15 s | The message a farmer receives |
| `scripts/build_dashboard.py` | ~3 min | Regenerates `report/dashboard_data.json` |

All of them take the `PYTHONPATH=src .venv/bin/python` prefix. The sweeps use every core
you have and print progress as they go.

### On Windows

The commands above are POSIX. The code itself is portable -- paths use `pathlib` and every
script carries a `__main__` guard, which Windows needs because it spawns rather than forks
processes. Only the shell syntax changes:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONPATH="src"; .venv\Scripts\python.exe scripts\simulate.py
```

In `cmd.exe` use `set PYTHONPATH=src` on its own line instead. Python 3.11 must already be
installed -- the `py` launcher selects among versions, it does not fetch one.

## The dashboard

```bash
PYTHONPATH=src .venv/bin/python scripts/build_dashboard.py   # rerun the model
python3 -c "import pathlib; \
 t=pathlib.Path('report/dashboard_react_template.html').read_text(); \
 d=pathlib.Path('report/dashboard_data.json').read_text(); \
 pathlib.Path('report/dashboard.html').write_text(t.replace('__DATA__', d))"
```

Then open `report/dashboard.html`. It is a React page with the model's output baked in as
JSON: a week of hourly dispatch, battery state of charge, the irrigation-window comparison,
the grid carbon curve and the KPI tables.

**It is a snapshot, not a live tool.** The page cannot re-run the simulation, because the
simulation is Python and the page is a browser document -- so changing a parameter means
rerunning `build_dashboard.py` and rebuilding, as above. Edit `SOLAR_KWP`, `BATTERY_KWH`
or `WEEK_START_DAY` at the top of `build_dashboard.py` to change what it plots. Making the
controls live would need a local API server in front of the model, which is not built.

## The interactive console

**Full guide: [CONSOLE.md](CONSOLE.md)** -- every control, what changing it does, worked
examples, and exactly which inputs are measured data and which are assumptions.

```bash
PYTHONPATH=src .venv/bin/python scripts/serve.py
```

Open <http://127.0.0.1:8000>. Change the site, the hardware, the loads or the tariffs on the
left, then either let the model choose the hardware or run the optimiser on hardware you
set. Every figure comes from a simulation run on the spot -- nothing on the page is
pre-computed.

Three buttons:

- **Decide the size for me** sweeps solar x wind x battery, ranks every candidate by
  annualised total cost subject to 99% reliability, and offers to apply the winner.
- **Run the optimiser** runs status quo, rule-based control and the optimiser on the same
  hardware, and plots the hourly dispatch, feeder availability and battery state of charge.
- **Get the farmer's advice** ranks every pump start hour, then optionally re-words the
  result in Gujarati or Hindi and shows whether every numeral survived verification.

### What it can and cannot do

**A shorter horizon.** A full 8,760-hour optimisation takes about 105 seconds and a full
sizing sweep about 25 minutes, which is not something to wait for behind a button. The
console defaults to 30 days (about 3 seconds) and allows up to 90. Every response carries
the horizon it used, and the page shows it.

**Read the ranking, not the rupees.** For sizing, capital is recovered per year while
energy is only simulated over the horizon, so the energy cost is scaled up to a year to
put the two on the same footing. That extrapolation assumes the window is seasonally
representative, which a 30-day block is not: a winter month understates solar and will
favour storage. Use 60-90 days for a fairer answer, and `scripts/optimize_sizing.py` for
the authoritative annual one. The 60-day console run recommends 2 kWp + 10 kWh where the
full-year sweep says 3 kWp + 5 kWh -- same territory, and the difference is exactly this
seasonal bias.

**Localhost only.** The endpoints run real CPU work and there is no authentication, so the
server binds to 127.0.0.1 and is a review tool for one machine, not something to expose.

API docs, if you want to drive it directly, are at `/api/docs`. The three endpoints are
`POST /api/simulate`, `POST /api/size` and `POST /api/advice`, all taking the same
parameter object.

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
  advice.py     irrigation window search and the farmer briefing
  explain.py    Gemini for phrasing only, with number verification
  village.py    community load model with pump diversity
  sharing.py    per-participant cluster model and the village line
  sizing.py     capital costing and the parallel configuration sweep
  kpi.py        diesel, cost, CO2 and reliability from a run log
  api.py        FastAPI endpoints behind the console
scripts/
  simulate.py           parameterised entry point - any site, hardware, tariff
  serve.py              the interactive console at 127.0.0.1:8000
  run_baseline.py       the headline case, three controllers
  optimize_sizing.py    derive hardware for the Banaskantha farm
  village_scenario.py   the coastal village case, where wind competes
  village_microgrid.py  a whole Banaskantha village, not one farm
  energy_sharing.py     what a village line between neighbours is worth
  combined_village.py   the whole village as one run, with every flow attributed
  validate_forecast.py  synthesised forecast vs genuine archived forecasts
  farmer_message.py     the message a farmer receives, via Gemini
  build_dashboard.py    regenerates the dashboard's data
report/
  mid-evaluation.html   results write-up
  architecture.html     system and agent-layer diagrams
  dashboard.html        the operations board (React, built from the template)
  console.html          the interactive console served by scripts/serve.py
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
wind, 5 kWh battery** -- Rs 84,709/yr all-in against a Rs 167,737/yr status quo, 83% less
diesel, reliability 94.1% to 100%. The cost surface is flat, with the top dozen
configurations inside 7%, so the exact sizing is not critical. Spending Rs 1,509/yr more
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

## Sharing surplus between neighbours

```bash
PYTHONPATH=src .venv/bin/python scripts/energy_sharing.py [days]
```

The village section above puts every load on one bus, which assumes sharing is already
perfect and free. This asks the question properly: model the village as its actual
participants -- 20 farms, 100 homes in blocks, the dairy chiller, the water supply -- and
run it twice with only the line between them different.

Only the farms own panels and batteries. Households are 31% of demand and own nothing, may
not draw agricultural-tariff power, and have no backup, so without sharing they simply go
without. Energy crossing the line loses 3% and every connection is capacity-limited --
without both, sharing would be free by construction and the result would mean nothing.

60 days, Palanpur, 60 kWp solar and 100 kWh storage on the farms:

| Line | Diesel | Curtailed | Unserved | Reliability | Per kWh served |
| --- | --- | --- | --- | --- | --- |
| 0 kW | 1,153 L | 1,808 kWh | 1,394 kWh | 97.12% | Rs 5.38 |
| 1 kW | 265 L | **0** | 827 kWh | 98.29% | Rs 3.25 |
| 2 kW | **154 L** | 0 | 517 kWh | 98.93% | **Rs 2.91** |
| 4 kW | 312 L | 0 | 131 kWh | 99.73% | Rs 3.11 |
| 8 kW | 370 L | 0 | **0** | **100%** | Rs 3.19 |

One kilowatt of line ends all curtailment. Diesel falls 87% and a delivered kWh falls 46%
cheaper, from Rs 5.38 to Rs 2.91.

The unserved column is the point. Without sharing it is households 1,149 kWh, dairy 197,
water 48 -- and farms zero. The farms own the hardware and were never in the dark. Sharing
is about the homes and the milk cooler that had no backup.

Note that cheapest and fairest differ: 2 kW is cheapest per unit but leaves 517 kWh
unserved, while 8 kW serves everybody for 9% more and deliberately burns more diesel to
reach the last household. Both are reported; choosing between them is policy, not
engineering. Either way the wire is small -- capacity stops binding between 2 and 8 kW.

Runs 60 days rather than a year: the cluster program solves a balance per participant and is
much heavier than the single-farm one. Read the ratios, not the rupees.

## Running it all as one village

```bash
PYTHONPATH=src .venv/bin/python scripts/combined_village.py [days] [line_kw]
```

The sweep above prices the line. This shows how the parts behave once it is there: one run
at a chosen line capacity with every flow attributed to its owner. Defaults to 60 days and
4 kW. 27 metered connections covering 122 premises, one line, one battery fleet, one
optimisation.

At 4 kW the village serves 99.73% of 48,433 kWh at Rs 3.11 per kWh with no curtailment.
Supply is village feeder 39.2%, agricultural feeder 31.4%, own solar 28.6%, diesel 0.8%.
Demand and shortfall by participant:

| | Demand | Share | Unserved | Diesel |
| --- | --- | --- | --- | --- |
| Farms | 29,868 kWh | 61.7% | 0.0 | 312 L |
| Households | 15,006 kWh | 31.0% | 103.3 kWh | 0 |
| Dairy chiller | 2,664 kWh | 5.5% | 28.0 kWh | 0 |
| Water pumping | 895 kWh | 1.8% | 0.0 | 0 |

The interesting output is the export/import table, which shows the line running **both
ways**. The farms are the only net exporters (11,601 out, 4,121 in) because they own every
panel. But the households own no generation and still export 471 kWh, and the cause is the
farms' own domestic connection cap: each farm holds 2 kW on the village feeder while a
household block holds 12 kW it does not fully use, so when a farm is capped a block imports
on its behalf and relays it. Raise the farm cap to 6 kW and that export falls to exactly
zero.

So it is a real two-way trade -- farm solar by day, spare household connection capacity
when a farm is capped -- but read it as a symptom: the relay works around an undersized
farm connection, and raising the cap is cheaper than wheeling power around it.

Two caveats on that table. A small wheeling charge (Rs 0.01/kWh) is applied to energy
pushed onto the line, because without it the optimiser was exactly indifferent about who
routed a surplus that would otherwise be curtailed, and different solvers returned
different splits at identical cost. With it, CLARABEL and ECOS agree on the per-kind flows
within 0.3%. Which *individual* block relays is still not determined, so read the table by
kind and never by participant.

The script also prints the combined day hour by hour. The battery fleet charges 01--05,
10--17 and 23--24 and discharges 05--10, 17--21 and 22--23 -- two charge windows for two
unrelated reasons, the Rs 1.50 agricultural tariff overnight and free surplus solar at
midday. At noon the feeders nearly switch off (4.4 and 0.1 kW) against 33.7 kW of solar.
The line peaks at 07:00 at 14.3 kW, above its 4 kW nameplate because the limit is per
connection and 27 of them each move their own share.

## Status

All seven phases are working: simulation, baselines, forecasting, the receding-horizon
optimiser, hardware sizing, irrigation advice with farmer-language messages, the dashboard
and live console, and community energy sharing.

Under realistic forecasts the optimiser retains 88% of its perfect-foresight advantage over
rule-based control, and forecast error costs about 5% of total energy cost.

What is not built: autonomous agent orchestration, where an agent decides for itself when to
re-plan rather than being asked. The pieces it would need already exist -- the optimiser is
a single call, the run log records every flow, and the advice layer turns set-points into
sentences -- so it is a wrapper over a finished interface rather than a rewrite.

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
| Rs 0/kg | 3 kWp | 5 kWh | 184 L | 8,290 kg | 31.9% | Rs 84,709 | -- |
| Rs 2/kg | 3 kWp | 5 kWh | 197 L | 8,110 kg | 33.3% | Rs 86,077 | Rs 7.60/kg |
| Rs 5/kg | 5 kWp | 10 kWh | 94 L | 6,349 kg | 47.8% | Rs 92,701 | Rs 4.12/kg |
| Rs 15/kg | 8 kWp | 20 kWh | 34 L | 3,858 kg | 68.3% | Rs 119,738 | Rs 7.90/kg |

The farmer's bill column strips out the notional carbon charge, which nobody actually pays;
abatement is measured against the Rs 0 row.

Two different mechanisms are at work. At Rs 2/kg the hardware does not change at all -- the
gain is pure dispatch, the optimiser re-timing the battery to charge through the midday
trough and discharge into the evening peak, worth 180 kg a year for no capital whatsoever.
From Rs 5/kg upward it buys capacity instead, and capacity is the cheaper lever: Rs 4.12/kg
against Rs 7.60 for re-timing, because it removes far more carbon per rupee spent.

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
