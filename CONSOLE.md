# The GramUrja Control Console

A browser interface to the model, meant for someone who wants to check the claims rather
than take them on trust. Change the site, the hardware or the prices and watch the answer
change; or hand the model the question and let it work out what to install.

Nothing on the page is pre-computed. Every figure comes from a simulation that runs when
you press the button.

---

## 1. Running it

```bash
# once, if you have not already
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# start the server
PYTHONPATH=src .venv/bin/python scripts/serve.py
```

Then open **<http://127.0.0.1:8000>**.

### Optional: the farmer-advice translation

Everything works without this. Only the Gujarati and Hindi rewording calls out to a
language model, and it needs a key of your own:

```bash
cp .env.example .env
# then paste your key after GEMINI_API_KEY=
```

A key is free from <https://aistudio.google.com/apikey> -- sign in, "Create API key", copy.
`.env` is gitignored and the key never leaves your machine except in the request to Google.

Without a key the advice button still works and returns the deterministic English briefing,
which carries exactly the same recommendation. No key is shipped with this repository, and
none should be: it is public, and a committed key is a key anyone can spend.

Leave the terminal running -- that is the server. `Ctrl+C` stops it. To use a different
port, pass it: `scripts/serve.py 8080`.

On Windows the shell syntax differs but the code does not:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONPATH="src"; .venv\Scripts\python.exe scripts\serve.py
```

The server binds to `127.0.0.1` deliberately. The endpoints run real CPU work and there is
no authentication, so this is a review tool for one machine, not something to put on a
network.

---

## 2. The layout

Controls run down the left in five groups; results appear on the right. On a narrow window
they stack, controls first. Until you press something, the right side says so.

If a request fails, a red band appears at the top with the reason.

---

## 3. Every control, and what changing it does

### Site

| Control | Default | Range | Effect |
|---|---|---|---|
| Preset chips | Palanpur | — | Palanpur, Dwarka, Mandvi, Jamnagar. Sets latitude and longitude together. |
| Latitude | 24.17 | -90 to 90 | Anywhere on earth. A new location downloads its weather. |
| Longitude | 72.43 | -180 to 180 | |
| Days to simulate | 30 | 7 to 90 | Longer is more representative and slower. See section 7. |

Changing the location triggers a fresh weather download from Open-Meteo, so the **first**
run at a new site takes a few seconds longer. After that it is cached on disk.

### Hardware

| Control | Default | Effect |
|---|---|---|
| Solar kWp | 3 | Panel capacity. `0` removes solar entirely. |
| Wind kW | 0 | Turbine capacity. `0` removes wind. |
| Hub height m | 18 | Turbine height. Matters enormously -- see section 6. |
| Battery kWh | 5 | Usable capacity. `0` removes storage. |
| Reserve floor | 0.2 | Fraction held back as a hard limit the optimiser may not cross. |
| Genset kW | 6 | Backup diesel rating. Too small and reliability fails. |

### Load

| Control | Default | Effect |
|---|---|---|
| Pump kW | 3.73 | The irrigation pump. 3.73 kW is a 5 HP motor. |
| Household kW | 0.4 | Base domestic load, with an evening rise added on top. |
| Dairy kW | 1.2 | Peak during morning and evening milking. |
| Cold storage kW | 0.8 | Runs most of the day. Set to 0 for a farm without one. |

### Prices and feeders

| Control | Default | Effect |
|---|---|---|
| Diesel ₹/L | 98.39 | Fuel price. Drives the whole economic case. |
| Ag tariff ₹/kWh | 1.50 | Subsidised agricultural supply. |
| Ag feeder kW | 10 | Capacity of the three-phase agricultural connection. |
| Village ₹/kWh | 5.00 | Domestic supply, unsubsidised. |
| Village feeder kW | 3 | Capacity of the single-phase domestic connection. |
| Carbon ₹/kg | 0 | Value placed on avoided CO₂. Not a bill anyone pays -- see section 8. |
| Grid kg CO₂/kWh | 0.71 | Mean grid carbon intensity; the daily shape is applied around it. |

**Note that the village feeder default (3 kW) is below the pump (3.73 kW).** That is not an
accident, and it is the constraint the whole problem turns on: when the agricultural feeder
is down, the domestic connection physically cannot run the pump.

### Run

The language dropdown and "Advice for day" only affect the advice button.

---

## 4. The three things it can do

### "Decide the size for me"

The interesting one. The model is not told the hardware -- it works it out.

It simulates **70 configurations** (7 solar × 2 wind × 5 battery), discards any that fail
99% reliability, and ranks the rest by annualised total cost: capital recovered over each
asset's life, plus fuel, plus grid. You get the winner in four tiles, the top ten in a
table, and a button to apply the winner.

Takes 20-60 seconds, because each candidate is a complete simulation rather than a formula.

### "Run the optimiser"

Runs whatever hardware is currently set on the left, under three controllers, and shows:

- **Four tiles** -- diesel, cost, reliability, CO₂, each against the status quo
- **The dispatch chart** -- a stacked area of where every hour's energy came from, with
  strips above it marking when each feeder was actually available
- **Battery state of charge** -- against the reserve floor, which the trace never crosses
- **The controller table** -- status quo, rule-based, optimiser on identical hardware

About 3 seconds at 30 days. The row that matters is the gap between *rule-based* and
*optimiser*: same hardware, so that difference is what the optimisation itself contributes,
separated from what the equipment does.

### "Get the farmer's advice"

Ranks all eleven candidate pump start hours -- each one a full re-simulation with the pump
moved -- and shows the briefing. Set the language dropdown to Gujarati or Hindi first and
you also get a translated message, plus a ✓ or ✗ reporting whether every numeral in it
traced back to the optimiser. See section 8 on why that check exists.

---

## 5. Reading the results

**Tiles** show the optimiser's outcome with the status quo underneath, so the comparison is
always in view.

**The dispatch chart** stacks five sources. Watch the two strips above the plot: when the
blue agricultural strip goes dark, the stack below it changes composition -- usually
battery green appearing, then diesel orange if storage runs out. That transition is the
system's whole behaviour in one picture.

**State of charge** should approach the reserve floor but never cross it. If it sits flat at
the floor for long stretches, the battery is too small to be useful; if it never comes down,
it is larger than the problem needs.

**The controller table** is where to check honesty. If the optimiser ever looks *worse* than
rule-based, something is inconsistent -- most likely a pricing mismatch rather than a real
finding.

---

## 6. Things worth trying

**Does the model follow the wind resource, or is it biased against wind?**
Click **Dwarka**, set Wind to 3 and Hub height to 50, then Run. Capacity factor goes from
about 1% to 17%. Now set Hub height back to 18 and run again: it collapses. Wind at this
scale is decided by mast height more than by geography.

**What is the battery actually worth?**
Set Battery to 0 and Run, note the diesel figure, then set it back to 5 and Run again.

**What happens when the domestic feeder cannot help?**
Set Village feeder kW to 1 and Run. The pump loses its fallback and you will see storage
and diesel take over in the chart.

**Does pricing carbon change anything?**
Set Carbon ₹/kg to 5 and press "Decide the size for me". It buys more solar. Then try
Grid kg CO₂/kWh at 0.2 (a clean grid) and see the case for solar weaken.

**Is the diesel case fragile?**
Set Diesel ₹/L to 40 and Run. Much of the saving disappears -- the economics rest on diesel
being expensive, and it is honest to see how much.

---

## 7. How it evaluates against real data

This section matters more than the rest. The console mixes measured data with modelled
assumptions, and it is worth knowing exactly which is which.

### What is genuinely measured

**Solar and wind resource.** When you enter a latitude and longitude, the server fetches
that location's weather from **Open-Meteo's ERA5 reanalysis archive** -- hourly shortwave
radiation, air temperature, wind speed and cloud cover for the whole year. Irradiance and
temperature go through a PV model with temperature derating (panels lose roughly 0.4% per
°C above 25 °C, which costs about 8% of nameplate on a 45 °C Banaskantha afternoon). Wind
speed is sheared from the 10 m measurement height to your hub height and passed through a
turbine power curve.

One caveat stated plainly: **ERA5 is reanalysis, not a weather station.** It is a physics
model that assimilates real observations onto a grid of roughly 9-30 km cells. It is
observation-grounded and the standard source for studies like this, but it is not a
pyranometer standing in that particular field. A site survey would precede any real
investment.

**Forecast error.** The optimiser does not get to see the future. It plans on a day-ahead
forecast whose error is calibrated to what Open-Meteo's own model actually gets wrong at
this site: **17.5% mean absolute error on daylight irradiance**, measured by comparing its
archived predictions against what subsequently happened over 92 days. Errors persist within
a day rather than varying hour to hour, because a weather model that misses a cloud bank is
wrong all afternoon.

That synthesised forecast was itself checked against genuine archived forecasts over the
window where both exist. It reproduces **93% of the cost penalty a real forecast imposes** --
slightly optimistic, and quantified rather than assumed. Run
`scripts/validate_forecast.py` to reproduce that check.

### What is modelled, and is not data

| Assumption | Value | Note |
|---|---|---|
| Demand profile | 15,175 kWh/yr default | **Constructed, not metered.** The largest assumption in the project. |
| Feeder schedule | 8 h block, three rotating slots | Modelled on Jyotigram structure, not a published roster. |
| Feeder outage rates | 5% agricultural, 7% village | Assumed. |
| Tariffs and capacities | ₹1.50 / ₹5.00, 10 kW / 3 kW | Assumed. |
| Capital costs | ₹50,000/kWp, ₹18,000/kWh | Planning figures. Results are sensitive to battery capital. |
| Grid carbon shape | 0.515 midday to 0.890 evening | Plausible model of the Indian grid, not measured dispatch. |
| Genset fuel rate | 0.30 L/kWh | Engineering assumption. The 0.75 L/kWh pumpset figure is derived from field data. |

Only the pump rating, its run hours and the diesel price trace back to field research. Change
any of the above in the console and you are changing an assumption, which is exactly the
point of exposing them.

### Why the numbers cannot be quietly wrong

The optimiser is a **linear program**: it proposes actions, but it does not execute them.
A separate simulator (`pymgrid`) steps the microgrid, enforces the physics -- battery limits,
feeder capacity, energy balance -- and logs what actually happened. If a plan were
over-optimistic, it would surface in the log as **unserved load or overgeneration**, both of
which the console reports. They are zero across the results shown.

The same principle governs the farmer message. Numbers are decided by the optimiser; a
language model is allowed only to re-word them. Every numeral in the generated text is
extracted and checked against the source, and if one does not trace back, the message is
marked unverified and the deterministic English is shown instead. A farmer deciding when to
irrigate should never act on an invented figure.

---

## 8. Limits you should know before quoting a number

**It runs 30 days, not a year.** A full 8,760-hour optimisation takes about 105 seconds and
a full sizing sweep about 25 minutes -- too slow to sit behind a button. The console
defaults to 30 days and allows up to 90. Every response states its horizon, and the page
displays it. The **comparison between controllers is fair**; the **absolute totals are not
annual figures**.

**Sizing is indicative, not authoritative.** Capital is recovered per year while energy is
only simulated over the horizon, so the energy cost is scaled up to a year to put them on
the same footing. That extrapolation assumes the window is seasonally representative, and a
30-day block is not -- a winter month understates solar and over-buys battery. Use 60-90
days for a fairer read, and `scripts/optimize_sizing.py` for the real annual answer.

Concretely: the 60-day console run recommends **2 kWp + 10 kWh**, where the full-year sweep
says **3 kWp + 5 kWh**. Same territory, and the gap is precisely this seasonal bias.

**The carbon price is not a bill.** It expresses how much the decision-maker values avoiding
a kilogram of CO₂ -- a policy instrument, a subsidy, an NGO's internal valuation, or simply
a planning scenario. Nothing charges it to the farmer. The sizing table separates the
optimiser's internal total from what the farmer actually pays.

**No field validation.** Nothing here has been measured against an installed system. These
are model results.

---

## 9. Driving the API directly

Interactive docs at **<http://127.0.0.1:8000/api/docs>**. Three endpoints, all taking the
same parameter object:

| Endpoint | Returns |
|---|---|
| `POST /api/simulate` | KPIs for all three controllers plus the full hourly series |
| `POST /api/size` | Recommended hardware and the ranked candidates |
| `POST /api/advice` | Ranked pump start hours, the briefing, and optionally a translation |

```bash
curl -s -X POST http://127.0.0.1:8000/api/simulate \
     -H 'Content-Type: application/json' \
     -d '{"days": 30, "solar": 5, "battery": 10, "lat": 22.24, "lon": 68.97}'
```

Any field you omit takes its default. Values are range-checked, so an impossible input
returns a 422 with the reason rather than a misleading result.

---

## 10. If something goes wrong

| Symptom | Cause |
|---|---|
| Red band, `422` | A control is blank or out of range. The message names the field. |
| First run at a new site is slow | Downloading that location's weather. Cached afterwards. |
| Sizing recommends almost nothing | Check the genset and feeder capacities are large enough to hold 99% reliability. |
| Optimiser looks *worse* than rule-based | Almost certainly a pricing inconsistency, not a finding. Worth reporting. |
| Advice shows ✗ unverified | The language model introduced a figure not in the source. The deterministic English is shown instead; this is the guardrail working. |
| No translated message | `GEMINI_API_KEY` is missing from `.env`. Everything else still works. |
