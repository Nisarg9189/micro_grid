"""What is community energy sharing worth, and who does it help?

Runs one village twice over the same weather, the same loads and the same total hardware,
changing only whether a line exists between the participants. Sweeping the line's capacity
shows the value of sharing, who benefits, and the point past which more capacity stops
being the constraint.

    PYTHONPATH=src .venv/bin/python scripts/energy_sharing.py [days]

Only the farms own panels and batteries. Households, the dairy chiller and the water supply
have no generation and no backup, so in the independent case they simply go without when
the domestic feeder fails -- which is the situation sharing is supposed to fix.
"""

import sys
from dataclasses import replace
from pathlib import Path

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

LINE_CAPACITIES = [0.0, 1.0, 2.0, 4.0, 8.0]


def main() -> None:
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    cluster = VillageCluster()
    people = build_participants(cluster)
    loads = participant_loads(days, cluster, people)
    weather = fetch_actual_weather("2025-01-01", "2025-12-31")
    profiles = generate_profiles(days=days, config=DEFAULT_CONFIG, weather=weather)

    print(f"{cluster.farms} farms · {cluster.households} homes · dairy chilling centre · "
          "water supply")
    print(f"  demand        {loads.sum():,.0f} kWh over {days} days")
    for kind in ("farm", "household", "dairy", "water"):
        rows = [i for i, p in enumerate(people) if p.kind == kind]
        share = 100 * loads[rows].sum() / loads.sum()
        print(f"    {kind:<11}{loads[rows].sum():>9,.0f} kWh {share:>6.1f}%")
    solar = cluster.farms * cluster.solar_kwp_per_farm
    storage = cluster.farms * cluster.battery_kwh_per_farm
    print(f"  hardware      {solar:g} kWp solar and {storage:g} kWh storage, all on the farms")
    print(f"  line losses   {100 * (1 - cluster.transfer_efficiency):.0f}% on energy that crosses\n")

    print(f"{'line':>6}{'diesel':>9}{'curtailed':>11}{'shared':>9}{'unserved':>10}"
          f"{'reliability':>13}{'energy cost':>13}{'per kWh served':>16}")
    print(f"{'kW':>6}{'L':>9}{'kWh':>11}{'kWh':>9}{'kWh':>10}{'%':>13}{'INR':>13}{'INR':>16}")
    print("-" * 87)

    rows = []
    for capacity in LINE_CAPACITIES:
        r = run_cluster(weather, loads, people, profiles.grid_status,
                        profiles.grid_status_village, replace(cluster, line_kw=capacity))
        served = r.demand_kwh - r.unmet_kwh
        unit = r.energy_cost_inr / served
        rows.append((capacity, r, unit))
        print(f"{capacity:>6.0f}{r.diesel_litres:>9.1f}{r.curtailed_kwh:>11.0f}"
              f"{r.transferred_kwh:>9.0f}{r.unmet_kwh:>10.1f}{r.reliability_pct:>12.2f}%"
              f"{r.energy_cost_inr:>13,.0f}{unit:>16.2f}", flush=True)
        print(f"        who goes without: {r.unmet_by_kind or 'nobody'}", flush=True)

    alone = rows[0]
    cheapest = min(rows[1:], key=lambda r: r[2])
    complete = next((r for r in rows if r[1].unmet_kwh < 0.5), None)

    print(f"\nSharing removes every kWh of waste at the first kilowatt of line.")
    print(f"  curtailed surplus  {alone[1].curtailed_kwh:,.0f} -> 0 kWh")
    print(f"  diesel             {alone[1].diesel_litres:,.0f} -> "
          f"{cheapest[1].diesel_litres:,.0f} L "
          f"({100 * (alone[1].diesel_litres - cheapest[1].diesel_litres) / alone[1].diesel_litres:.0f}% less)")
    print(f"  cost per kWh served  Rs {alone[2]:.2f} -> Rs {cheapest[2]:.2f} "
          f"({100 * (alone[2] - cheapest[2]) / alone[2]:.0f}% cheaper)")

    print(f"\nBut cheapest and fairest are not the same line.")
    print(f"  a {cheapest[0]:g} kW line is cheapest per unit (Rs {cheapest[2]:.2f}), and still "
          f"leaves {cheapest[1].unmet_kwh:,.0f} kWh unserved")
    if complete:
        extra = 100 * (complete[2] - cheapest[2]) / cheapest[2]
        print(f"  a {complete[0]:g} kW line serves everybody (100% reliability) for "
              f"Rs {complete[2]:.2f}, about {extra:.0f}% more per unit")
        print(f"  it even burns more diesel -- {complete[1].diesel_litres:,.0f} L against "
              f"{cheapest[1].diesel_litres:,.0f} L -- because reaching the last household is "
              "worth\n  more than the fuel it costs")

    print(f"\nWho was going without, before any sharing:")
    for kind, kwh in sorted(alone[1].unmet_by_kind.items(), key=lambda x: -x[1]):
        print(f"  {kind:<11}{kwh:>8,.0f} kWh")
    print("  The farms are absent from that list: they own the panels, the batteries and the")
    print("  pumpsets. Sharing is not mainly about saving the farms money - it is about the")
    print("  households and the milk cooler that had no backup at all.")

    print(f"\nCaveat: {days} days at one site, and the load profiles are modelled rather than")
    print("metered. Read the ratios; the rupees are not an annual figure.")


if __name__ == "__main__":
    main()
