"""Produce the message a farmer actually receives.

Chains the whole system: measured weather, forecast, optimiser, irrigation-window search,
deterministic briefing, then a language model for phrasing only. Run with a language:

    PYTHONPATH=src .venv/bin/python scripts/farmer_message.py gujarati

Needs GEMINI_API_KEY in the environment or .env. Without it the deterministic English
briefing is printed instead, which is the same advice in a less friendly wrapper.
"""

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gramurja.advice import daily_briefing, recommend_irrigation_window  # noqa: E402
from gramurja.config import DEFAULT_CONFIG  # noqa: E402
from gramurja.explain import LANGUAGES, api_key, render_advice  # noqa: E402
from gramurja.profiles import generate_profiles  # noqa: E402
from gramurja.weather import fetch_actual_weather  # noqa: E402

SOLAR_KWP, BATTERY_KWH = 3.0, 5.0
DAY = 20
PUMP_HOURS = 3


def main() -> None:
    language = (sys.argv[1] if len(sys.argv) > 1 else "gujarati").lower()
    if language not in LANGUAGES:
        raise SystemExit(f"usage: farmer_message.py [{'|'.join(LANGUAGES)}]")

    config = replace(
        DEFAULT_CONFIG,
        solar_capacity_kwp=SOLAR_KWP, wind_capacity_kw=0.0,
        battery_capacity_kwh=BATTERY_KWH,
        battery_max_charge_kw=BATTERY_KWH * 0.25,
        battery_max_discharge_kw=BATTERY_KWH * 0.25,
    )
    weather = fetch_actual_weather("2025-01-01", "2025-12-31")
    profiles = generate_profiles(days=365, config=config, weather=weather)

    print(f"Evaluating pump start hours for day {DAY} ({PUMP_HOURS} hours needed)...\n")
    advice = recommend_irrigation_window(profiles, day=DAY, hours_needed=PUMP_HOURS, config=config)

    print(f"{'start':>7}{'diesel L':>11}{'day cost':>11}")
    print("-" * 29)
    for option in advice.options:
        marker = "  <- best" if option.start_hour == advice.best.start_hour else ""
        print(f"{option.start_hour:>5}:00{option.diesel_litres:>11.2f}"
              f"{option.cost_inr:>11.1f}{marker}")

    briefing = daily_briefing(profiles, advice, config)
    print("\nDeterministic briefing, the source of truth:")
    for line in briefing:
        print(f"  - {line}")

    if not api_key():
        print("\nNo GEMINI_API_KEY found; the briefing above is the output.")
        return

    result = render_advice(briefing, language=language)
    print(f"\nMessage in {LANGUAGES[result.language]}:")
    print(f"  {result.safe_text}")

    print("\nNumber check:")
    if result.verified:
        print("  every numeral in the message traces back to the optimiser")
    else:
        print(f"  UNVERIFIED - these figures are not in the source: {result.unverified_numbers}")
        print("  falling back to the deterministic English above")


if __name__ == "__main__":
    main()
