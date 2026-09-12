# GramUrja AI — Complete Project Explanation

[PROJECT_STARTUP.md](PROJECT_STARTUP.md) · [CONSOLE.md](CONSOLE.md)

A guide to what this project is, how it works, what the numbers mean, and what it does not
yet do. Written for teammates, judges and evaluators.

---

## Read this first

**In one sentence:** GramUrja AI decides what energy hardware a rural farm should install,
and then how to run it hour by hour — choosing between solar, battery, two different grid
feeders and diesel so the bill is as low as possible while the power stays on.

**The result**, on a full year of hourly simulation at a Banaskantha farm:

| | Today | With GramUrja AI |
|---|---|---|
| Diesel | 1,080 L/year | **184 L/year** (−83%) |
| Total energy cost | ₹167,737/year | **₹84,709/year** (₹83,027 saved) |
| Reliability | 94.1% | **100%** |
| CO₂ | 12,166 kg/year | **8,290 kg/year** (−31.9%) |

Recommended system: **3 kWp solar, 5 kWh battery, no wind** — derived from the load profile,
not assumed.

**Three things that make this more than a simulation:**

1. **The optimiser changes what hardware is worth buying.** Run the same sizing search under
   simple rules and it buys *no battery at all*; run it under our optimiser and the battery
   pays for itself and nearly doubles the diesel displaced. The controller has capital
   consequences, not just operating ones.
2. **It survives imperfect forecasts.** 88% of the perfect-foresight advantage remains when
   the controller plans on forecasts carrying this site's genuinely measured 17.5% error —
   and that forecast was itself validated against real archived weather predictions.
3. **Wind was evaluated, not assumed away.** It loses at Palanpur on measured physics (1.2%
   capacity factor), but the same engine *selects* it at a coastal village site below
   ₹60,000/kW. The model follows the resource rather than carrying a bias.

**The uncomfortable one, stated upfront:** roughly half the diesel reduction comes from
replacing an inefficient diesel pumpset with a proper generator — no AI involved. What the
optimiser adds on top is ₹18,867/year and 184 L of diesel beyond what simple rules achieve on
identical hardware.

**Where to go next:** Section 12 for all results · Section 3 for how the optimiser differs
from rule-based control · Section 11 for what is real data and what is assumed · Section 15
for limitations.

---

## 1. Project overview

### What GramUrja AI is

GramUrja AI is a **microgrid energy-mix optimiser**. Given a farm's energy demand, its solar
and wind resource, the grid connections available to it, and a diesel backup, it decides
**how much of every hour's load should come from each source** so that the total cost is as
low as possible while the supply stays reliable.

It is a decision engine, not a piece of hardware. It answers two questions:

- **What to install** — how many kWp of solar, how many kWh of battery, whether wind is
  worth it at all.
- **What to run, hour by hour** — when to charge the battery, when to spend it, when to
  import from which feeder, when to start the diesel.

### The problem it solves

A Banaskantha farm today runs on two separate electricity supplies and a diesel engine:

- A **5 HP diesel pumpset** drives irrigation. It is a direct-coupled engine turning a pump
  shaft, so it cannot power anything else — not a milking machine, not a cold store.
- The **agricultural feeder** is three-phase but rationed to about eight hours a day.
- The **village feeder** is near-continuous but single-phase and small.

The result is expensive and unreliable. In the modelled year the farm burns **1,080 litres
of diesel**, spends **₹167,737** on energy, and **892 kWh of demand goes unserved** because
when the agricultural feeder is down the village feeder cannot carry the pump.

### The complete system flow

```
Weather (solar & wind resource)  +  Farm load  +  Feeder availability
                              ↓
                        Forecasting
                              ↓
                 Optimisation engine (MPC)
                              ↓
       Solar · Wind · Grid feeders · Battery · Diesel
                              ↓
                       Farmer's loads
                              ↓
             Measurement, then re-optimisation
```

### What exists and what does not

| Component | Status |
|---|---|
| Hourly microgrid simulation | **Built** |
| Reanalysis weather → solar and wind output | **Built** |
| Forecasting of generation, demand, feeder availability | **Built** |
| Receding-horizon dispatch optimiser | **Built** |
| Hardware sizing search | **Built** |
| Carbon-aware optimisation | **Built** |
| Agent layer (monitoring, replanning, farmer explanations) | **Planned, not written** |
| Operator dashboard and farmer app | **Planned, not written** |
| Community energy sharing | **Planned, not written** |

Everything reported in this document comes from the built components. There is currently
**no agent, no dashboard and no machine-learning model** in the codebase.

---

## 2. How the current system works

### Weather

Solar and wind come from **Open-Meteo's ERA5 reanalysis** for Palanpur, Banaskantha
(24.17°N, 72.43°E), for calendar 2025 — 8,760 hourly values.

An important honesty point: reanalysis is **not** a weather station reading. It is a physics
model that assimilates real observations onto a grid of roughly 9–30 km cells. It is
observation-grounded and is the standard source for studies like this, but it is not a
pyranometer standing in a field at Palanpur. A site survey would be the next step before
anyone spends money.

Grounding the model in reanalysis mattered. The synthetic profiles it replaced overstated
**solar yield by about a third** and **wind by an order of magnitude**.

### Solar generation

Irradiance and air temperature are converted to AC output with a temperature-derated PV
model — panels lose roughly 0.4% of output per °C above 25 °C, and Banaskantha runs hot, so
a 45 °C afternoon costs around 8% of nameplate.

**Measured yield: 1,490 kWh per kWp per year.**

### Wind generation

Wind speed at the 10 m reanalysis height is sheared up to hub height and passed through a
turbine power curve (cut-in 3 m/s, rated 12 m/s).

**At Palanpur: mean wind 2.5 m/s, capacity factor 1.2%.** A 3 kW turbine would produce
327 kWh in a year. Wind is modelled and fully supported, but the recommended system for this
site contains **0 kW of it**. Section 9 explains where it does get selected.

### Farm load

Hourly demand totalling **15,175 kWh a year**, made of:

- **Irrigation pump** — 5 HP (3.73 kW), about 640 run-hours a year, seasonal: roughly three
  hours a day in the rabi season, two in summer, half an hour during the monsoon.
- **Household** — 0.4 kW base with an evening rise.
- **Dairy** — 1.2 kW during morning and evening milking.
- **Cold storage** — 0.8 kW, running most of the day.

**This demand profile is constructed, not metered.** It is the largest modelled assumption
in the project, and cold storage alone drives roughly 40% of the annual total.

### The two feeders

Gujarat's Jyotigram scheme separates rural supply into two distinct feeders, and that split
governs the whole problem.

| | Agricultural feeder | Village feeder |
|---|---|---|
| Purpose | Irrigation pumping | Homes, dairy, small loads |
| Phase | Three-phase | Single-phase |
| Capacity (modelled) | 10 kW | **3 kW** |
| Tariff (assumed) | ₹1.50/kWh | ₹5.00/kWh |
| Availability (modelled) | ~31% — a rostered 8 h block | ~93% — near-continuous |

### Per-feeder constraints — why this matters so much

Each feeder is modelled as its own connection with its own cap. This is not a detail. **The
pump draws 3.73 kW and the village feeder can deliver 3 kW.** So when the agricultural
feeder is down, the pump *physically cannot* fall back on the domestic supply. That single
constraint is what creates the shortfall the battery and diesel exist to cover — and
separating the feeders is exactly why Jyotigram exists.

### Feeder availability

The agricultural feeder follows a **published rotating roster**: an eight-hour block whose
start time rotates weekly through **three slots — 06:00, 14:00 and 22:00**. On top of the
schedule, about 5% of hours are lost to **unplanned outages**.

That split is deliberate and important for forecasting: the **roster is knowable in advance**
and the **unplanned outages are not**. The village feeder is nominally continuous with
roughly 7% of hours lost to unannounced interruptions.

### Battery

5 kWh usable capacity in the recommended system, with:

- a **20% reserve floor** (1 kWh held back),
- charge and discharge limited to **1.25 kW** (a C/4 rate),
- **95% efficiency each way**, so a **90% round trip** — storing a kWh and getting it back
  costs about 11% extra.

That 10% loss turns out to matter a great deal for carbon (Section 6).

### Diesel backup

Two very different machines, which must not share one efficiency number:

| | Fuel rate | Cost per kWh | CO₂ per kWh |
|---|---|---|---|
| Direct-coupled pumpset (status quo) | 0.75 L/kWh | **₹73.79** | 2.03 kg |
| Proper backup genset (new system) | 0.30 L/kWh | **₹29.52** | 0.81 kg |

A small direct-coupled pumpset really is this inefficient, and it is why the status quo is
so expensive. Diesel is priced at ₹98.39/L and emits 2.7 kg CO₂ per litre.

### Reliability constraint

Unserved load carries a very high penalty in the optimiser (₹100/kWh, far above diesel's
₹29.52), so it will always burn fuel rather than shed load. In sizing, any configuration
that fails to hold **99% reliability** is rejected outright.

Result: the status quo serves 94.1% of demand; every recommended system serves **100%**.

### Cost optimisation

The optimiser minimises the total rupee cost of meeting demand — grid imports at each
feeder's own tariff, diesel at its fuel cost, plus penalties for unserved load. In sizing,
capital cost is added, recovered over each asset's life.

### Carbon-aware optimisation and time-varying grid intensity

Carbon can be priced into the same objective. Crucially, the **grid's carbon intensity
varies through the day**:

| Hour | Grid intensity |
|---|---|
| 13:00 (utility solar peak) | **0.515 kg/kWh** |
| 00:00–04:00 (coal baseload) | ~0.735 kg/kWh |
| 20:00 (evening peak) | **0.890 kg/kWh** |
| Annual mean | 0.710 kg/kWh |

A 73% spread between cleanest and dirtiest hour. Section 6 explains why that shape is the
only reason a battery can help emissions at all.

---

## 3. MPC vs RBC

### The two terms

- **RBC = Rule-Based Control.** Fixed if-then rules.
- **MPC = Model Predictive Control.** Look ahead, plan, act, repeat.

### How RBC decides

RBC looks only at *right now*. Its logic is essentially: use renewable energy if it's
available; if not, take the cheapest source available this instant; if there's surplus, store
it. It has no idea what happens next hour. It is simple, robust, and it is what most real
controllers do today.

### How MPC decides

Every hour, MPC:

1. Reads the current state — battery charge, current load, what's available.
2. Looks **24 hours ahead** at forecast demand, forecast solar, the feeder roster, tariffs
   and carbon intensity.
3. Solves for the cheapest 24-hour plan that meets every constraint.
4. **Applies only the first hour** and discards the rest.
5. Next hour, re-solves with updated information.

That last part matters: it never commits to a stale plan. If the forecast was wrong, the next
solve corrects for it.

### Why MPC preserves the battery

Because it knows what's coming. A kWh in the battery is not worth what it would save *now* —
it's worth what it will save **when it is finally used**. If the cheap feeder is on now, that
kWh only displaces ₹1.50 power. But if the feeder goes down during tonight's pump run, the
same kWh displaces **₹29.52 diesel**. MPC holds it for the second case. RBC cannot, because
it doesn't know tonight exists.

### Why MPC uses cheap grid power

For exactly the same reason. When the ₹1.50 feeder is on, buying from it is cheaper than
spending stored energy that is worth far more later. So MPC buys grid power *and* charges the
battery at the same time — building up a reserve precisely when energy is cheapest.

### Why MPC spends the battery during outages

When the agricultural feeder is down and the pump is running, the village feeder is capped at
3 kW against a 5.81 kW load. The only remaining options are the battery and diesel. Stored
energy is now worth ₹29.52/kWh, so MPC discharges at full rate and lets diesel cover only
what's left.

### Verified behaviour

Over 30 simulated days, the built optimiser showed:

| Behaviour | Result |
|---|---|
| Hours discharging while the ₹1.50 feeder was **up** | **0** |
| Hours discharging while it was **down** | 342 |
| Hours holding usable charge while importing from the cheap feeder | 200 |
| Share of charging done inside the cheap window | **85%** (117 of 137 kWh) |

A perfect separation: the battery is *never* spent while cheap power is available.

---

## 4. The feeder example

### The two-feeder concept

Think of the farm as having two electricity taps:

- **The agricultural tap** — big enough for the pump, but only open on a schedule.
- **The village tap** — always open, but too small for the pump.

### The modelled roster — and what it is not

This project models the agricultural feeder as an **eight-hour block rotating weekly through
three start times: 06:00, 14:00, 22:00**, plus random unplanned outages.

**This is the project's modelled example, not an official statewide rule.** Real Jyotigram
schedules differ by district and feeder and change over time. What the model is trying to
capture is the *structure* that matters: supply is **scheduled and therefore predictable**,
with an **unpredictable failure rate on top**. A real deployment would use the actual
published roster for that feeder.

### How availability is forecast

The controller predicts feeder availability by simply reading the roster — the schedule is
published, so no clever prediction is needed. What it **cannot** foresee is an unplanned
outage. For the village feeder, which has no schedule, the controller assumes supply will be
there and is occasionally surprised.

This split is deliberate: it tests forecasting where forecasting is genuinely hard, rather
than giving the controller knowledge it wouldn't have.

### Hour-by-hour behaviour

**Agricultural feeder available** → serve load from grid and solar; **charge** the battery
with the surplus. Do not discharge — stored energy is worth more later.

**Agricultural feeder unavailable, village available** → serve from solar and the village
feeder up to its 3 kW cap; discharge the battery only for what the village feeder cannot
carry.

**Both feeders unavailable** → solar, then battery, then diesel for the remainder.

**Pump running with the agricultural feeder down** → the village feeder's 3 kW cannot carry a
3.73 kW pump. Battery and diesel must cover the gap. There is no way around this; it is a
physical limit, not a cost preference.

### Why the battery is saved

A battery holds a limited amount of energy. Spending it while a ₹1.50 feeder is available
buys a ₹1.50 saving. Holding it until the feeder is down buys a ₹29.52 saving. Same kWh,
nearly twenty times the value. The only reason to spend early is if it would otherwise sit
full and waste incoming solar.

---

## 5. A simple MPC example

These are **real timesteps** from the model, not an invented illustration. `ag` is the
₹1.50 feeder, `vil` the ₹5.00 feeder (3 kW cap), `soc` is battery state of charge with a
floor at 0.20.

```
hour  load  pump  solar agUp    ag   vil   chg   dis   soc   dsl
 149  2.08  0.00   0.00    0  0.00  2.08  0.00  0.00  0.20  0.00
 150  2.08  0.00   0.00    1  2.70  0.00  0.62  0.00  0.20  0.00
 151  5.81  3.73   0.00    1  6.19  0.00  0.38  0.00  0.32  0.00
 161  2.40  0.00   0.43    0  0.00  1.90  0.00  0.07  0.96  0.00
 162  2.90  0.00   0.05    0  0.00  2.81  0.00  0.04  0.95  0.00
 163  2.58  0.00   0.00    0  0.00  0.00  0.00  1.19  0.94  1.39
 175  5.81  3.73   0.00    0  0.00  3.00  0.00  1.19  0.89  1.62
 176  4.71  3.73   0.18    0  0.00  3.00  0.00  1.19  0.64  0.34
 177  4.71  3.73   0.67    0  0.00  3.00  0.00  0.88  0.39  0.16
 178  1.30  0.00   1.12    0  0.00  0.18  0.00  0.00  0.20  0.00
```

**Hour 149 — feeder down.** Load 2.08 kW served entirely by the village feeder at ₹5.00.
Battery sits at its 0.20 floor and legally cannot discharge.

**Hour 150 — the feeder comes on.** Village import drops instantly to zero; the farm pulls
2.70 kW from the ₹1.50 feeder for a 2.08 kW load. The extra 0.62 kW **charges the battery**.
It abandons the expensive tap the moment the cheap one opens, and starts stockpiling.

**Hour 151 — the pump starts, and the battery still charges.** Load jumps to 5.81 kW. The
battery has energy, but MPC imports 6.19 kW and keeps charging. *Why?* Discharging now saves
₹1.50/kWh. That same kWh is worth ₹29.52 later. It buys rather than spends.

**Hours 161–162 — holding the line.** Battery is nearly full (0.96), the cheap feeder is
down, and MPC *still* buys from the ₹5.00 village feeder rather than draining storage. It is
saving it for something.

**Hour 163 — the something.** The village feeder fails too. No grid at all, 2.58 kW of load.
Battery discharges at its 1.19 kW maximum, diesel covers the remaining 1.39 kW. Without the
reserve, all of it would have been diesel.

**Hours 175–177 — the big one.** The pump runs with the agricultural feeder down. Village is
pinned at exactly **3.00 kW, its hard cap**, and the pump alone wants 3.73 kW. The battery
discharges flat out (1.19, 1.19, 0.88) and diesel fills only the remainder. State of charge
drains 0.89 → 0.20, hitting the floor exactly as the pump stops.

Nothing was wasted and nothing was spent early. That is the whole mechanism.

---

## 6. Battery intelligence

### Why stored energy is not spent on sight

A battery is not a free energy source — it is a **timing device**. Every kWh in it was paid
for, and using it now means not having it later. The right question is never "is there energy
in the battery?" but "**is now the most valuable moment to use it?**"

### What "future value" means

The value of a stored kWh equals the cost of whatever it will displace:

| Displaces | Worth |
|---|---|
| Agricultural feeder power | ₹1.50/kWh |
| Village feeder power | ₹5.00/kWh |
| Diesel | **₹29.52/kWh** |

MPC holds the battery for the highest-value moment it can see in its 24-hour window.

### What it weighs

Future load (especially pump hours), forecast solar, the feeder roster, unplanned-outage
risk, tariffs, carbon intensity, and the battery's own limits — the 20% floor, the 1.25 kW
rate cap, the 90% round-trip efficiency.

### Carbon-aware battery dispatch

If carbon is given a price, the optimiser also weighs the emissions of each option. Whether
that changes anything depends entirely on one thing: **does grid carbon vary over time?**

### Why flat carbon creates no arbitrage

Suppose the grid emitted a constant 0.71 kg/kWh. Discharging a stored kWh to avoid grid
carbon saves 0.71 kg now — but you must re-import that kWh later, and the 90% round trip
means importing 1.11 kWh to restore it, emitting 0.79 kg. **Net: 0.08 kg worse.**

This was tested. With flat intensity, even at a carbon price of **₹50/kg** — roughly ten
times the social cost of carbon — the optimiser **never once** discharged the battery to
avoid grid carbon, and total emissions moved by under 1%. A battery can only arbitrage
things that *change*. Flat carbon doesn't change, so there is nothing to trade.

### Why time-varying carbon does create arbitrage

With a real daily shape, the trade becomes profitable: store a kWh at 13:00 when the grid is
at 0.515 kg/kWh, release it at 20:00 when it is 0.890. That saves 0.375 kg — comfortably more
than the ~0.08 kg the round trip costs.

Measured over 30 days with time-varying intensity:

| Carbon price | Charging in clean midday | Discharging in dirty evening | CO₂ |
|---|---|---|---|
| ₹0/kg | 51.3 kWh | 27.3 kWh | 821 kg |
| **₹2/kg** | **112.0 kWh** | **74.2 kWh** | **801 kg** |
| ₹5/kg | 114.9 kWh | 76.9 kWh | 800 kg |
| ₹50/kg | 123.7 kWh | 89.7 kWh | 797 kg |

Almost the entire behavioural shift happens between ₹0 and ₹2. That matters practically:
India's carbon market trades near ₹2/kg, so this is reachable under existing policy rather
than requiring a hypothetical price.

---

## 7. Sizing optimisation

### The question

How much solar, wind and battery should actually be installed? Guessing is easy to get
wrong — the project's original placeholder of 10 kWp solar and 20 kWh of battery turned out
to be roughly three times too large and threw away 40% of what it generated.

### Why it must be a sweep

Each candidate configuration behaves differently in ways that interact and cannot be
reasoned about in isolation: capital cost, generation, how hard the battery gets cycled,
diesel consumption, reliability and emissions. The only honest way to compare them is to
**run each one**.

So the search:

1. Enumerates combinations of solar × wind × battery.
2. Simulates **every one over the full 8,760-hour year** with the real controller.
3. Costs each: capital recovered over each asset's life (25 years solar, 20 wind, 10 battery,
   at a 9% discount rate) plus fuel, grid and O&M.
4. Discards anything below 99% reliability.
5. Picks the cheapest survivor.

Because each candidate is scored by running the actual controller, **the answer depends on
which controller runs** — see Section 12.

### The result (reanalysis weather, realistic forecasts, 120 configurations)

**Recommended: 3 kWp solar · 0 kW wind · 5 kWh battery**

| Metric | Value |
|---|---|
| Diesel | 184 L/year (83.0% below status quo) |
| Reliability | 100% |
| Annualised capital | ₹31,695 |
| Energy cost | ₹53,014 |
| **Total** | **₹84,709/year** |
| Curtailed energy | 19 kWh/year |

Nearby options, showing how flat the cost surface is:

| Solar | Battery | Diesel | Diesel cut | Total/year |
|---|---|---|---|---|
| **3 kWp** | **5 kWh** | 184 L | 83.0% | **₹84,709** |
| 2 kWp | 5 kWh | 198 L | 81.6% | ₹85,055 |
| 3 kWp | 10 kWh | 75 L | 93.1% | ₹86,218 |
| 0 | 10 kWh | 107 L | 90.1% | ₹88,353 |
| 2 kWp | 0 | 396 L | 63.4% | ₹90,827 |

The top dozen configurations sit within 7% of each other, so the recommendation is robust
rather than knife-edge. Note the third row: **₹1,460/year more buys a 10 kWh battery and
lifts the diesel cut from 83% to 93%**.

---

## 8. The village case

The problem statement asks about **off-grid communities**, and names microgrid operators,
electrification agencies and NGOs as its users — not individual farmers. So the same engine
was pointed at a whole village rather than one holding.

### What the village contains

100 households, 20 farms, a dairy chilling centre and the drinking-water supply.

| Load | kWh/year | Share | Character |
|---|---|---|---|
| Households | 91,271 | 58.0% | Small individually, evening peak |
| Irrigation | 44,350 | 28.2% | Large, scheduled, deferrable |
| Dairy chilling | 16,206 | 10.3% | Twice daily, **hard deadline** |
| Water supply | 5,446 | 3.5% | Critical but shiftable |
| **Total** | **157,273** | | Peak 49.9 kW, load factor 36% |

### A village is not one farm multiplied

Two things change, and both matter.

**Diversity.** A hundred households do not switch on together, and twenty pumps do not start
in the same minute. Each farm in the model has its own fixed start hour, so the aggregate
pump peak is **29.8 kW against the 74.6 kW they would draw simultaneously — a diversity
factor of 0.40**. That spread is the whole economic argument for sharing infrastructure, and
a model that multiplies one farm by twenty throws it away.

**The peak moves to the evening.** On a single farm the dominant load is a pump running in
daylight, so demand and solar roughly coincide. In a village, households dominate and peak at
**31 kW at 19:00** when solar is zero, against a **10.9 kW trough at 13:00** when solar is
strongest. That mismatch is precisely what storage exists to fix.

### The routing constraint

At farm scale, the rule that pumps cannot use the domestic feeder came for free: a 3 kW
single-phase connection physically cannot start a 3.73 kW pump. A 50 kW village transformer
can, so at village scale the rule has to be stated explicitly.

It is a real constraint, not a modelling convenience. Agricultural and domestic supplies are
**separately sanctioned and separately tariffed** — ₹1.50 against ₹5.00 — and running a pump
off a domestic connection is a different contract, not a clever optimisation. The optimiser
now carries demand as two groups with a separate energy balance each, and every connection
declares what it may serve. Grid power may only reach the battery through a connection
already allowed to serve the domestic side; otherwise storage becomes a laundering route for
agricultural-tariff power.

**Enforcing it changed the answer completely:**

| | Without routing | **With routing** |
|---|---|---|
| Solar | 20 kWp | **40 kWp** |
| Battery | **0 kWh** | **100 kWh** |
| Diesel | 2,014 L | **937 L** |
| CO₂ cut | 33.0% | **47.7%** |
| Saved per household | ₹19,244 | **₹16,524** |

Storage went from worthless to essential. Once pumps genuinely cannot fall back on the
domestic feeder, the roughly 69% of hours when the agricultural feeder is down must be
covered by solar, battery or diesel — and storage is the cheapest way to do it. **Every one
of the ten cheapest configurations now carries a battery**, the smallest being 25 kWh.

The earlier ₹19,244 per household was inflated because the model was quietly supplying pumps
from a domestic connection. The honest figure is about 14% lower.

### Result

**Recommended: 40 kWp solar, 0 kW wind, 100 kWh battery**

| Metric | Status quo | Recommended |
|---|---|---|
| Diesel | 21,970 L/year | **937 L/year** (−95.7%) |
| Total cost | ₹2,707,313/year | **₹1,054,954/year** |
| Reliability | 94.7% | **100%** |
| Unserved load | 8,306 kWh/year | **0** |
| CO₂ | 149,246 kg/year | **78,116 kg/year** (−47.7%) |

**Saving: ₹1,652,359/year — ₹16,524 per household.**

The nearest alternatives:

| Solar | Battery | Diesel | Renewable share | Total/year |
|---|---|---|---|---|
| **40 kWp** | **100 kWh** | 937 L | 36.8% | **₹1,054,954** |
| 30 kWp | 50 kWh | 2,680 L | 27.5% | ₹1,063,273 |
| 40 kWp | 50 kWh | 2,555 L | 33.7% | ₹1,068,275 |
| 30 kWp | 100 kWh | 1,114 L | 28.0% | ₹1,077,758 |
| 60 kWp | 100 kWh | 826 L | 48.0% | ₹1,084,170 |

Two consistency checks worth noting. Status-quo diesel works out to **1,098 L per farm**
against 1,080 L from the independent single-farm run — within 1.7%, from a completely
different load model. And the village needs 100 kWh of storage where a single farm needed
5 kWh; with 20 farms that is suggestive rather than rigorous, since the village also carries
100 households, but the two models landing in the same territory from different directions is
reassuring.

**Caveat:** every figure in the village load model is an assumption — 2.5 kWh/day per
household, a 5 kW bulk milk cooler, four hours of water pumping. Structurally realistic for
Banaskantha, but none of it is metered.

---

---

## 9. The wind decision

### Why wind was rejected at Palanpur

Not on cost — on physics.

| Quantity | Measured | Consequence |
|---|---|---|
| Mean wind speed | 2.5 m/s | Below the 3 m/s turbine cut-in most of the year |
| Capacity factor | **1.2%** | A 3 kW turbine yields 327 kWh/year |
| Appearances in the optimum | **0 of 120** | Beaten by solar at every capacity and price |

Banaskantha is inland northern Gujarat. The state's wind resource is on the Kutch and
Saurashtra coast.

### The Dwarka experiment

To check that the engine follows the resource rather than carrying a built-in bias, the same
code was run at **Dwarka** on the Saurashtra coast, at **village scale** — 20 farms
(303,500 kWh/year) sharing one **80 m turbine**, which is plausible for a community where a
single farm's 18 m mast is not.

**Hub height turned out to matter more than the site.** Raising it from 18 m to 80 m lifted
the capacity factor from 8.6% to **22.2%**, because a farm-scale mast sits in slow surface
wind. And 35% of that output arrives **after dark**, when solar contributes nothing.

| Wind capital | Solar | Wind | Battery | Total/year | Wind selected |
|---|---|---|---|---|---|
| ₹70,000/kW | 60 kWp | 0 | 100 kWh | ₹1,686,963 | No — by 0.75% |
| **₹60,000/kW** | 40 kWp | **20 kW** | 100 kWh | ₹1,683,517 | **Yes** |
| ₹50,000/kW | 40 kWp | 20 kW | 100 kWh | ₹1,655,608 | Yes |
| ₹40,000/kW | 40 kWp | 40 kW | 100 kWh | ₹1,614,095 | Yes |

**Wind enters the modelled optimum below about ₹60,000/kW** under these assumptions, and as
it cheapens the optimiser buys more of it and retires solar — trading the two resources on
merit.

### The honest conclusion

Wind is **not globally rejected**. GramUrja evaluates whether wind makes sense for a specific
site and a specific set of economics, and at Palanpur the answer is no. The conclusion is
about **scale as much as geography**: no single farm reaches the hub height that makes wind
work, which is itself an argument for a shared village microgrid.

---

## 10. Carbon-aware optimisation

### Cost-only versus carbon-aware

By default the optimiser minimises rupees. Carbon-aware mode adds emissions to the same
objective:

```
Total objective  =  energy cost  +  carbon price × CO₂ emitted
```

### What the carbon price actually represents

**The carbon price is a modelling parameter, not a bill.** It expresses how much the
decision-maker values avoiding a kilogram of CO₂. It can stand for a policy instrument, a
subsidy, an NGO's internal valuation, a social cost of carbon, or simply a planning
scenario.

**The farmer does not pay this price.** Nothing in the implementation charges it to anyone.
That is why the tables below separate the optimiser's internal objective from the farmer's
actual bill.

### Sensitivity results

| Carbon value | Solar | Battery | Diesel | CO₂ | CO₂ cut | Optimisation total | Farmer's bill | Abatement |
|---|---|---|---|---|---|---|---|---|
| ₹0/kg | 3 kWp | 5 kWh | 184 L | 8,290 kg | 31.9% | ₹84,709 | ₹84,709 | — |
| ₹2/kg | 3 kWp | 5 kWh | 197 L | 8,110 kg | 33.3% | ₹102,297 | ₹86,077 | ₹7.60/kg |
| ₹5/kg | 5 kWp | 10 kWh | 94 L | 6,349 kg | 47.8% | ₹124,446 | ₹92,701 | ₹4.12/kg |
| ₹15/kg | 8 kWp | 20 kWh | 34 L | 3,858 kg | 68.3% | ₹177,608 | ₹119,738 | ₹7.90/kg |

**Reading this table correctly:**

- **Optimisation total** is the objective's own value and *includes* the modelled carbon
  term. It is not money anyone pays.
- **Farmer's bill** removes that carbon term — capital plus energy only. This is the number
  to compare against the ₹167,737 status quo.
- **Abatement** is the extra rupees per kilogram of CO₂ avoided, measured against the ₹0 row.

### The key finding

Two distinct mechanisms operate, and they are worth separating:

**At ₹2/kg the hardware does not change at all.** Still 3 kWp and 5 kWh. The entire 180 kg
gain comes from the optimiser **re-timing the battery** against the daily carbon curve —
charging through the clean midday trough, discharging into the dirty evening peak. No
capital, pure dispatch.

**From ₹5/kg upward it buys capacity instead**, and capacity is the cheaper lever — ₹4.12/kg
against ₹7.60/kg for re-timing, because it removes far more carbon per rupee.

So: **installed renewable capacity is the dominant driver of emissions, but dispatch is not
irrelevant** — it contributes a real, if smaller, reduction once carbon intensity varies
through the day. Under a flat intensity assumption, dispatch contributes essentially nothing.

---

## 11. Real data versus modelled assumptions

Being precise about this is the difference between a defensible project and an
embarrassing one.

### Grounded in observation

| Item | Source | Note |
|---|---|---|
| Solar and wind resource | Open-Meteo **ERA5 reanalysis**, Palanpur 2025 | Observation-assimilated model on a ~9–30 km grid — **not** a weather station |
| Day-ahead forecast error | Open-Meteo's **archived past model runs**, 92 days | 17.5% mean absolute error on daylight irradiance — genuinely measured |
| Diesel price | Field research | ₹98.39/L |
| Pumpset fuel rate | Derived from field figures | 2.8 L/h over a 3.73 kW pump = 0.75 L/kWh |

### The forecast, precisely

This deserves care because it is easy to overstate.

- Annual runs use a **synthesised** forecast — the reanalysis irradiance perturbed with
  day-correlated noise scaled to the measured 17.5% error. It is **not** downloaded forecast
  data. Synthesis is necessary because the forecast archive reaches back only ~92 days.
- Genuine archived forecasts are used in **one place**: a 93-day validation run.
- That validation found the synthesised forecast reproduces **93% of the cost penalty** a
  real forecast imposes (₹517 against ₹557), making it very slightly optimistic.

| Forecast | Diesel | Cost | Penalty vs perfect foresight |
|---|---|---|---|
| Perfect foresight | 45.8 L | ₹15,065 | — |
| Archived, genuine | 51.9 L | ₹15,622 | ₹557 |
| Synthesised | 51.6 L | ₹15,582 | ₹517 |

### Modelled assumptions — not data

| Item | Value | Note |
|---|---|---|
| Farm demand profile | 15,175 kWh/year | **Constructed.** Cold storage alone is ~40% of it |
| Feeder roster | 8 h block, three rotating start times | Modelled example of Jyotigram structure |
| Feeder outage rates | 5% agricultural, 7% village | Assumed |
| Feeder tariffs | ₹1.50 and ₹5.00/kWh | Assumed |
| Feeder capacities | 10 kW and 3 kW | Assumed |
| Solar capital | ₹50,000/kWp | Planning assumption |
| Battery capital | ₹18,000/kWh | Planning assumption — **results are sensitive to this** |
| Wind capital | ₹120,000/kW farm, ₹70,000/kW community | Planning assumption |
| Asset lives / discount rate | 25 / 20 / 10 years at 9% | Assumed |
| Backup genset fuel rate | 0.30 L/kWh | Engineering assumption |
| Grid emission factor | 0.710 kg/kWh mean, varying 0.515–0.890 | Assumed shape and level |

**None of the second table is real data.** They are reasonable planning figures that a pilot
would replace.

---

## 12. Current results

### The three controllers

Same hardware (3 kWp solar, 5 kWh battery), same year, same weather. **These are energy costs
only — they exclude the ₹31,695/year of annualised capital**, so they are not comparable to
the ₹84,709 total in the next table.

| Metric | Status quo | Rule-based | Optimiser (realistic forecast) |
|---|---|---|---|
| Diesel | 1,080 L | 368 L | **184 L** |
| Energy cost | ₹167,737 | ₹71,869 | **₹53,002** |
| Reliability | 94.1% | 100% | **100%** |
| Unserved load | 892 kWh | 0 | **0** |
| CO₂ | 12,166 kg | 8,294 kg | 8,291 kg |

The optimiser removes **184 L of diesel and ₹18,867 a year beyond what rules achieve on
identical hardware** — 26% of the remaining bill.

Now look at the CO₂ column: halving the diesel moves emissions by **4 kg across a whole
year**, which is nothing. The optimiser displaces diesel largely by importing more grid
power, and once round-trip losses are counted the two emit about the same per kWh delivered.
Cost and carbon are not the same objective, and optimising hard for one barely touches the
other.

### Total cost of ownership

Comparing like with like — the status quo has no capital because there is no hardware.

| | Status quo | Recommended system |
|---|---|---|
| Hardware | None | 3 kWp solar, 5 kWh battery |
| Annualised capital | ₹0 | ₹31,695 |
| Energy cost | ₹167,737 | ₹53,014 |
| **Total per year** | **₹167,737** | **₹84,709** |
| Diesel | 1,080 L | 184 L (**−83.0%**) |
| Reliability | 94.1% | **100%** |
| CO₂ | 12,166 kg | 8,290 kg (**−31.9%**) |

**Saving: ₹83,027 per year**, about half the farm's total energy bill.

### Sizing depends on the controller

The same search, run under each controller, gives different hardware:

| Controller | Solar | Battery | Diesel cut |
|---|---|---|---|
| Rule-based | 2 kWp | **0 kWh** | 59.0% |
| Optimiser | 2 kWp | **5 kWh** | 85.0% |

Under simple rules a battery never earns back its cost, so the optimal system has none. Under
optimisation the same battery pays for itself. **The controller determines which hardware is
worth installing** — that is this project's central finding.

*(Those two rows come from an earlier sweep on synthetic weather; the real-weather
recommendation is the 3 kWp / 5 kWh system above. The comparison between controllers is what
matters here, and it holds in both.)*

---

## 13. What makes this "AI"

This deserves an honest answer, because the term gets stretched.

### What is in the system today

**Statistical forecasting — not machine learning.** The forecast series is generated by
perturbing reanalysis data with day-correlated noise calibrated to the site's genuinely
measured forecast error, and validated against real archived forecasts. **There is no trained
model in this project** — no XGBoost, no neural network, no scikit-learn. Calling it "ML
forecasting" would be false. A trained model on metered data is a natural next step.

**Mathematical optimisation — the real engine.** The dispatch decision is a **linear
program** solved every hour over a 24-hour horizon. This is operations research, not machine
learning. It is the right tool precisely *because* it is not a learned model: battery limits,
feeder capacity and energy balance are **constraints that can be proven**, not behaviours
that have to be learned and hoped for.

**Search-based design optimisation.** The sizing sweep evaluates every candidate system over
a full simulated year and selects by an explicit objective.

**Closed-loop adaptation.** The receding-horizon loop re-solves every hour with measured
state, so when reality diverges from forecast the plan corrects itself. This is the
"re-optimisation" in the flow diagram, and it is implemented.

**Carbon-aware decision-making.** Emissions can enter the same objective as cost, and the
optimiser changes both dispatch and recommended hardware in response.

### What is not in the system

**The agent layer is designed, not built.** The intention is that agents handle monitoring,
deciding when a re-plan is worth running, and translating set-points into farmer-readable
advice — calling the optimiser as a tool. A deliberate architectural commitment goes with it:
**a language model must never write a set-point.** A plausible-looking number can violate a
battery limit or strand a critical load, and nothing in a language model would catch it.
Agents orchestrate; the solver decides.

### The honest summary

> Today GramUrja AI is a **forecast-driven optimisation and control system** with
> carbon-aware decision-making. The intelligence is in looking ahead, weighing future value
> against present cost, and proving constraints rather than guessing them. Machine learning
> and agentic orchestration are planned extensions, not current claims.

---

## 14. End-to-end flow

```
              Reanalysis weather + forecast error
                              |
                              v
        +---------------------+---------------------+
        |                     |                     |
        v                     v                     v
  Solar/wind           Farm demand          Feeder availability
   forecast              forecast          (roster + outage risk)
        |                     |                     |
        +---------------------+---------------------+
                              |
                              v
                   MPC decision engine
              (24-hour horizon linear program;
               cost + carbon, subject to
               reliability and physical limits)
                              |
                              v
        Solar + Wind + Grid feeders + Battery + Diesel
                              |
                              v
     Farmer loads  (irrigation, household, dairy, cold storage)
                              |
                              v
        Measurement: what actually happened this hour
                              |
                              v
              Re-optimisation with the new state
                              |
                              +--> (loop back to the decision engine)
```

The loop runs every hour. Only the first hour of each 24-hour plan is ever executed.

---

## 15. Limitations and honest caveats

These are stated plainly because an evaluator will find them anyway, and because a project
that names its own weaknesses is more trustworthy than one that doesn't.

**Demand is synthetic.** The household, dairy and cold-storage profiles are constructed, not
metered, and cold storage alone drives roughly 40% of annual load. Every rupee figure rests
on this. It is the single biggest soft spot.

**Weather is reanalysis, not site measurement.** ERA5 on a 9–30 km grid is observation-
grounded but is not a pyranometer at Palanpur. A site survey should precede any investment.

**Forecasts are synthesised for annual runs.** Calibrated to real measured error and
validated to reproduce 93% of the real penalty over 93 days — but still synthesised, and
slightly optimistic. Annual results are a mild upper bound.

**Capital costs and tariffs are assumptions.** Battery capital in particular drives the
sizing result. Vendor quotes would change the recommendation.

**Grid carbon intensity is an assumed shape.** The 0.515–0.890 kg/kWh daily curve is a
plausible model of the Indian grid, not measured dispatch data. The carbon conclusions in
Section 10 depend on it.

**Feeder behaviour is modelled.** The three-slot rotating roster, the 5% and 7% outage rates,
the 10 kW and 3 kW caps and both tariffs are assumptions about structure, not the published
schedule of any specific feeder.

**No field validation.** Nothing here has been measured against an installed system. These
are **model results, not an installation guarantee**.

**One site, one year.** Calendar 2025 at a single representative farm, with no multi-year
weather variability and no sensitivity to a bad monsoon.

**Half the benefit is not the optimiser.** Replacing the 0.75 L/kWh pumpset with an efficient
genset delivers a large share of the diesel reduction at zero capital and no intelligence
whatsoever. This is worth stating clearly, because it sharpens what the optimiser is actually
for: the arbitrage and reliability gains that rules cannot capture.

**The agent layer does not exist.** Phases for monitoring, farmer-facing explanation and
community sharing are designed and diagrammed only.
