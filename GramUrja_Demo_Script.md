# GramUrja AI — Live Demo Script (9–10 minutes)

Speaker notes in plain text. **[DEMO: ...]** lines tell you exactly what to click.
Numbers below are real values pulled live from the running site — if you re-run a
scenario before recording, glance at the screen and say whatever number is actually
showing rather than reading these from memory.

---

## 1. Situation (≈45 sec)

Banaskantha, Gujarat — like most of rural India — runs its farms and villages on a mix
of grid power that isn't always there, and diesel generators that fill the gap. The
agricultural feeder is only sanctioned a few hours a day. The village feeder is
separately metered, separately priced, and can't be used to power a farm's pump. When
both go down at once, the only thing standing between a farmer and a dead pump — or a
dairy cooler losing its milk — is a diesel genset burning fuel at nearly ₹100 a litre.

Solar and batteries can fix a lot of this. But nobody's handing a farmer a spreadsheet
that tells them exactly how much solar, how much battery, and how much diesel backup
they actually need — and once it's installed, nobody's telling them when to actually
run their pump to get the cheapest, greenest hour of the day.

## 2. Small story (≈45 sec)

Say you're a farmer in Palanpur. You've got a 3.7 kW borewell pump, a dairy chiller
running most of the day, and a household drawing power in the evening. The agricultural
feeder gives you cheap power at ₹1.50 a unit — when it's on. The village feeder is
₹5 a unit. Solar is free, but only while the sun's up. And right now, the only tool you
have to decide "should I irrigate at 7am or 3pm" is habit, not data.

That's the actual gap GramUrja AI is built to close — not "should this village go
solar," but "exactly how much of what, and exactly when."

## 3. Our proposed solution (≈1 min)

GramUrja AI is three things working together, not one black box:

1. A **sizing agent** that answers "how much solar, wind, battery and diesel backup
   should this site actually install" — by running a real branch-and-bound search over
   the hardware options, not a rule of thumb.
2. A **dispatch controller** — a model-predictive-control optimizer that re-solves,
   hour by hour, exactly how to split the load across solar, battery, both feeders, and
   diesel, using a real weather forecast, not perfect hindsight.
3. An **advisory agent** that turns that same dispatch logic into one sentence a farmer
   can act on: the best hour to start irrigating today.

Everything I'm about to show you is live — every number on this page comes from an
actual simulation running against real historical weather data for this site, not a
mockup.

**[DEMO: open the site, land on the Dashboard tab, currently on "Results"]**

## 4. How it works — the whole pipeline (≈50 sec)

**[DEMO: click the "How It Works" tab]**

This is the full pipeline, start to end, in six steps: real historical weather comes in
from Open-Meteo — not synthetic data. That feeds a forecast layer, which carries a real,
measured forecast error of about 17.5%, because pretending the model knows tomorrow's
weather perfectly would make the results dishonest. That forecast drives either the
sizing agent, deciding what hardware to build, or the MPC dispatch, deciding how to run
what's already built. The output is the KPIs you'll see in a minute, and the same
dispatch logic becomes the farmer advisory at the very end.

Every step here links straight to the section that does it — that's what the rest of
this demo walks through.

## 5. Configuration (≈1 min)

**[DEMO: click the "Configuration" tab, then click "Expand"]**

This is the control panel — site, hardware, load, and prices, and every single number
here feeds the live API call behind every result on this page.

Two things worth showing. First, up top: **Tested Scenarios**. These aren't hypothetical
— they're five configurations this project actually ran and reported a result for.
**[DEMO: click "Coastal wind site"]** — this re-runs the simulation live, right now,
against the real backend, switching to Dwarka's coordinates and an 80-metre shared wind
mast.

Second — site presets. **[DEMO: click the "+" next to the site pills]** — if I want to
test a site that isn't one of the four built-in presets, I just type a name and its
coordinates, and it's added and selected immediately. Everything downstream — weather,
solar yield, wind resource — is computed live for wherever I just typed.

## 6. Village-scale validation (≈1 min)

**[DEMO: click the "Village Scale" tab]**

Here's a question worth asking out loud: does the answer change once you're not sizing
one farm, but a whole village? This panel runs the exact same bounded-search sizing
agent, but against a real aggregate load — 100 households, 20 farms, a dairy chiller,
and the water supply — instead of one farm's demand.

**[DEMO: click "Coastal village (best case for wind)"]**

This is the single best-case scenario we could construct for wind — real village-scale
demand, a coastal site, an 80-metre shared mast, and a turbine priced at nearly half the
standard farm-mast cost. Watch what it recommends. *(~30 seconds while it runs)*

**[Point at the result once it lands: 40 kWp solar / 0 kW wind / battery, ~₹944,000/yr]**

Wind still isn't selected — not because there's no wind resource at Dwarka, there
genuinely is, real utility-scale wind farms operate there. It's that a 20 kW village
turbine carries a fixed yearly ownership cost of about ₹150,000 regardless of price,
and the system doesn't even choose a battery here either. If storing energy for the
evening gap isn't worth its own cost, a wind turbine — which can only help if it happens
to be blowing exactly when there's a shortfall — has even less chance. That's not a bug
in our model. That's a real, tested finding.

## 7. Results (≈40 sec)

**[DEMO: click the "Results" tab]**

These four numbers are the headline: energy cost, diesel consumption, grid reliability,
carbon emissions — all computed directly from the live simulation you just configured,
compared against a status-quo baseline with no optimization at all. Right now, for the
default Palanpur farm: **₹5,089 in energy cost over 30 days, 16.1 litres of diesel, 100%
reliability, 818 kg of CO2** — versus a status-quo system that would burn nearly nine
times as much diesel to hit only 95% reliability.

## 8. Energy Flow (≈1 min)

**[DEMO: click the "Energy Flow" tab]**

This is the actual dispatch decision the optimizer made, for the single hour of peak
demand in this run. Five real sources: solar, the agricultural feeder, the village
feeder, the battery, and diesel — each one reading its own real series, not a made-up
number. Notice the feeder status: a feeder can be "standby" — up, but not worth using
this hour — or genuinely "offline," and this page tells you which, because those are two
completely different facts a farmer needs to know.

**[DEMO: switch back to Configuration tab, click "Wind turbine installed (manual)", then return to Energy Flow]**

One more thing — if I manually install a wind turbine, even though our AI wouldn't
choose to on its own, watch: a sixth node appears, **Wind Turbine**, and it's generating
real power — pulled straight from actual wind-speed data at this site and hub height.
This proves the model isn't just returning zero because something's broken. Wind
genuinely works here. It just doesn't pay for itself.

## 9. Telemetry (≈40 sec)

**[DEMO: click the "Telemetry" tab]**

This is the full hour-by-hour dispatch curve behind those headline numbers — every
source's output plotted against the load it served, over 24 hours, 7 days, or the full
30-day horizon. And right beside it, the optimizer's own decision log: it re-solves this
as a real linear program every time you press Run — this isn't a canned animation, it's
the actual solver, CLARABEL, running live.

## 10. Agriculture (≈40 sec)

**[DEMO: click the "Agriculture" tab, click "Get Irrigation Advice"]**

This is where all of this becomes something a farmer can actually use. Same dispatch
logic, same live weather — turned into one recommendation: the best hour to start
irrigating today, how many hours the pump needs to run, and how much it saves versus
running it at the wrong hour. It's delivered in English, Gujarati, or Hindi, because a
number in the wrong language isn't useful to anyone.

## 11. Community Impact — closing (≈50 sec)

**[DEMO: click the "Community" tab]**

And this is the impact translated into terms a household actually feels: rupees saved,
litres of diesel avoided, kilograms of CO2 abated — computed live against the status quo
every single time, never a fixed number sitting in the code.

That's GramUrja AI: real weather, a real optimizer, a real sizing agent that isn't
afraid to tell you wind doesn't pay off here — and a farmer-facing recommendation at the
very end that turns all of it into one sentence someone can actually act on tomorrow
morning. Thank you.

---

### Timing checkpoint
Sections 1–3 (pitch): ~2.5 min · Sections 4–11 (live demo): ~7 min · **Total: ~9.5 min**

### If you're running short on time
Cut section 9 (Telemetry) to one sentence, and skip the manual wind-turbine demo inside
section 8 — mention it verbally instead ("if you install one manually, it does generate
real power, it just doesn't pay for itself").

### If a judge asks something not covered here
- *"Is this real data?"* → Weather is real (Open-Meteo, historical). Load profiles,
  tariffs, and capex numbers are modeled assumptions representative of the region, not
  live meter readings — say this plainly if asked, it's already disclosed on the
  Prediction page.
- *"Why doesn't wind ever win?"* → Point back to section 6's answer: fixed ownership
  cost plus intermittency beats it even in the single best-case scenario tested.
- *"Does this scale beyond one village?"* → Multi-village aggregation is on the roadmap,
  not yet built — say so rather than implying it already works.
