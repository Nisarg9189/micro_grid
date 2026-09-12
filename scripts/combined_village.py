"""One village, running as a single system: farms, households, dairy and water together.

`energy_sharing.py` answers "what is a line worth?" by sweeping its capacity. This script
answers a different question -- with the line in place, how do the parts actually combine?
It runs the whole village once and reports where the energy comes from, who sends it, who
receives it, and what the shape of an average day looks like.

    PYTHONPATH=src .venv/bin/python scripts/combined_village.py [days] [line_kw]

Everything is one optimisation: 27 metered connections covering 122 premises, one line,
one battery fleet, solved hour by hour under receding-horizon control against real
Banaskantha weather.
"""

import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gramurja.config import DEFAULT_CONFIG  # noqa: E402
from gramurja.profiles import generate_profiles  # noqa: E402
from gramurja.sharing import (  # noqa: E402
    VillageCluster,
    build_participants,
    participant_loads,
    run_cluster,
)
from gramurja.weather import fetch_actual_weather  # noqa: E402

KINDS = ("farm", "household", "dairy", "water")
LABEL = {"farm": "farms", "household": "households", "dairy": "dairy chiller",
         "water": "water pumping"}


def bar(value: float, peak: float, width: int = 22) -> str:
    """A crude horizontal bar, so the daily shape is visible without a plotting library."""
    if peak <= 0:
        return ""
    return "#" * int(round(width * value / peak))


def main() -> None:
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    line_kw = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0

    cluster = replace(VillageCluster(), line_kw=line_kw)
    people = build_participants(cluster)
    loads = participant_loads(days, cluster, people)
    weather = fetch_actual_weather("2025-01-01", "2025-12-31")
    profiles = generate_profiles(days=days, config=DEFAULT_CONFIG, weather=weather)

    solar_kwp = cluster.farms * cluster.solar_kwp_per_farm
    storage_kwh = cluster.farms * cluster.battery_kwh_per_farm

    print(f"\nONE VILLAGE, ONE OPTIMISATION -- {days} days, {line_kw:g} kW shared line")
    print("=" * 78)
    print(f"  participants   {len(people)} connections: {cluster.farms} farms, "
          f"{cluster.households} households in {cluster.household_blocks} blocks,")
    print("                 one dairy chilling centre, one drinking-water pumping station")
    print(f"  generation     {solar_kwp:g} kWp solar and {storage_kwh:g} kWh storage, "
          "all of it on the farms")
    print(f"  gensets        {cluster.genset_kw_per_farm:g} kW per farm, farms only")
    print(f"  line losses    {100 * (1 - cluster.transfer_efficiency):.0f}% on energy that crosses")

    r = run_cluster(weather, loads, people, profiles.grid_status,
                    profiles.grid_status_village, cluster)

    served = r.demand_kwh - r.unmet_kwh
    print(f"\nWHAT THE VILLAGE CONSUMED")
    print("-" * 78)
    print(f"{'':<16}{'demand':>12}{'share':>8}{'unserved':>11}{'diesel':>10}")
    print(f"{'':<16}{'kWh':>12}{'%':>8}{'kWh':>11}{'L':>10}")
    for kind in KINDS:
        demand = r.demand_by_kind.get(kind, 0.0)
        print(f"  {LABEL[kind]:<14}{demand:>12,.0f}{100 * demand / r.demand_kwh:>8.1f}"
              f"{r.unmet_by_kind.get(kind, 0.0):>11,.1f}"
              f"{r.diesel_by_kind.get(kind, 0.0):>10,.1f}")
    print(f"  {'village total':<14}{r.demand_kwh:>12,.0f}{100.0:>8.1f}"
          f"{r.unmet_kwh:>11,.1f}{r.diesel_litres:>10,.1f}")

    print(f"\nWHERE THE ENERGY CAME FROM")
    print("-" * 78)
    supply = {
        "own solar, used directly": r.solar_used_kwh,
        "agricultural feeder": r.ag_kwh,
        "village feeder": r.village_kwh,
        "diesel gensets": r.diesel_kwh,
    }
    total_supply = sum(supply.values())
    for name, kwh in supply.items():
        print(f"  {name:<28}{kwh:>10,.0f} kWh {100 * kwh / total_supply:>6.1f}%  "
              f"{bar(kwh, max(supply.values()))}")
    print(f"  {'':<28}{'':>10}       ({r.transferred_kwh:,.0f} kWh of it moved across the line)")

    print(f"\nWHO SENDS AND WHO RECEIVES")
    print("-" * 78)
    print(f"{'':<16}{'exported':>12}{'imported':>12}{'net':>12}")
    print(f"{'':<16}{'kWh':>12}{'kWh':>12}{'kWh':>12}")
    for kind in KINDS:
        out = r.exported_by_kind.get(kind, 0.0)
        into = r.imported_by_kind.get(kind, 0.0)
        print(f"  {LABEL[kind]:<14}{out:>12,.0f}{into:>12,.0f}{into - out:>+12,.0f}")
    print("  The farms are the only net exporters -- they own every panel. But the line runs")
    print("  both ways: the households own no generation and still push energy out, which")
    print("  needed a cause rather than a story. It is the farms' OWN domestic connection")
    print(f"  cap of {cluster.farmhouse_kw:g} kW. A household block holds "
          f"{cluster.village_kw_per_block:g} kW it does not fully use, so when a farm's")
    print("  domestic draw hits its own ceiling the block imports on the farm's behalf and")
    print("  relays it. Raise the farm cap to 6 kW and this export falls to exactly zero.")
    print()
    print("  So it is a two-way trade -- farm solar by day, spare household connection")
    print("  capacity when a farm is capped -- but read it as a symptom: the relay is a")
    print("  workaround for an undersized farm connection, and simply upgrading that")
    print("  connection is cheaper than wheeling power around it.")
    print()
    print("  Attribution caveat: these per-kind flows are stable (CLARABEL and ECOS agree")
    print("  within 0.3%), but WHICH individual block relays is not determined -- several")
    print("  assignments cost the same. Read the table by kind, never by participant.")

    # Collapse the run into an average day, so the interaction is visible as a shape.
    hourly = {name: np.asarray(v).reshape(-1, 24).mean(axis=0) for name, v in r.hourly.items()}
    print(f"\nAN AVERAGE DAY, HOUR BY HOUR (kW, mean over {days} days)")
    print("-" * 78)
    print(f"{'hr':>4}{'demand':>8}{'solar':>8}{'ag':>7}{'village':>9}{'battery':>9}"
          f"{'diesel':>8}{'shared':>8}   solar")
    print(f"{'':>4}{'':>8}{'':>8}{'':>7}{'':>9}{'+out/-in':>9}{'':>8}{'':>8}")
    peak_solar = hourly["solar"].max()
    for h in range(24):
        battery = hourly["discharge"][h] - hourly["charge"][h]
        print(f"{h:>4}{hourly['demand'][h]:>8.1f}{hourly['solar'][h]:>8.1f}"
              f"{hourly['ag'][h]:>7.1f}{hourly['village'][h]:>9.1f}{battery:>+9.1f}"
              f"{hourly['diesel'][h]:>8.1f}{hourly['transferred'][h]:>8.1f}   "
              f"{bar(hourly['solar'][h], peak_solar, 16)}")

    charge_hours = [h for h in range(24)
                    if hourly["charge"][h] > hourly["discharge"][h] + 0.05]
    discharge_hours = [h for h in range(24)
                       if hourly["discharge"][h] > hourly["charge"][h] + 0.05]
    share_peak = int(np.argmax(hourly["transferred"]))

    def runs(hours: list[int]) -> str:
        if not hours:
            return "never"
        blocks, start = [], hours[0]
        for a, b in zip(hours, hours[1:] + [None]):
            if b != (a + 1 if a is not None else None):
                blocks.append(f"{start:02d}:00-{a + 1:02d}:00")
                start = b
        return ", ".join(blocks)

    print(f"\nHOW THE PIECES COMBINE")
    print("-" * 78)
    print(f"  battery charges    {runs(charge_hours)}")
    print(f"  battery discharges {runs(discharge_hours)}")
    print(f"  line busiest at    {share_peak:02d}:00, moving "
          f"{hourly['transferred'][share_peak]:.1f} kW")
    print(f"  reliability        {r.reliability_pct:.2f}% of village demand served")
    print(f"  cost               Rs {r.energy_cost_inr:,.0f} over {days} days, "
          f"Rs {r.energy_cost_inr / served:.2f} per kWh served")
    print(f"  curtailment        {r.curtailed_kwh:,.0f} kWh of surplus wasted")

    print(f"\nCaveat: {days} days of ERA5 reanalysis weather at one site; load profiles are")
    print("modelled, not metered. Read the ratios and the shape, not the annual rupees.\n")


if __name__ == "__main__":
    main()
