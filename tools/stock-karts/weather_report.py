#!/usr/bin/env python3
"""Compare complete clear/rain/snow balance runs. Prints a Markdown report.

Run balance.sh once per weather first, then:
  python3 tools/stock-karts/weather_report.py > tools/stock-karts/weather_balance.md
"""

import json
import statistics
from pathlib import Path

from balance_table import COURSES

ROOT = Path(__file__).resolve().parents[2]
WEATHERS = ("clear", "rain", "snow")


def main():
    results = {
        weather: json.loads((ROOT / "build/balance" / weather / "results.json").read_text())
        for weather in WEATHERS
    }
    vehicles = sorted(path.stem for path in (ROOT / "data/karts/stock").glob("*.json"))
    scores = {}
    medians = {}
    for weather, data in results.items():
        for kart in vehicles:
            for course in COURSES:
                if course not in data.get(kart, {}):
                    raise ValueError(f"Missing {weather}: {kart} on {course}; finish the full run first")
        medians[weather] = {
            course: statistics.median(
                data[kart][course]["time"] for kart in vehicles if data[kart][course]["time"] > 0
            )
            for course in COURSES
        }
        scores[weather] = {
            kart: 100 * (statistics.mean(data[kart][course]["time"] / medians[weather][course] for course in COURSES) - 1)
            if all(data[kart][course]["time"] > 0 for course in COURSES) else None
            for kart in vehicles
        }

    print("# Stock vehicle weather balance\n")
    print("Two laps from a standing start, one AI-driven vehicle at a time, on Peach Pit, Foundry Flats, Launchpad Loop and Dune Drift. All 22 stock vehicles; clear, rain and snow; daytime; random seed 12345 reset before each race. No vehicle or driving changes were made for this run.\n")
    print("Each percentage is the mean of the vehicle's time divided by the median time on each course, minus one. Negative is quicker than the field; positive is slower. The rain/snow change columns subtract the dry percentage: negative means the vehicle gains relative to its peers in that weather. These are percentage-point changes, not raw speed changes.\n")
    print("This is one seed and one two-lap run per combination, using AI. It identifies candidates for follow-up, not a measure of human performance or consistency across all courses and puddle layouts.\n")
    print("## Findings\n")
    for weather in WEATHERS:
        completed = {k: v for k, v in scores[weather].items() if v is not None}
        outside = sorted(((k, v) for k, v in completed.items() if abs(v) > 10), key=lambda pair: pair[1])
        description = ", ".join(f"{k} ({v:+.1f}%)" for k, v in outside) if outside else "none"
        print(f"- {weather.capitalize()}: vehicles outside the usual roughly ±10% overall target: {description}.")
    print("\nWeather-specific outliers should be checked with more seeds before retuning. Changing a vehicle globally to correct a wet-weather advantage may disturb its dry balance.\n")
    print("## Relative pace\n")
    print("| Vehicle | Clear | Rain | Snow | Rain change | Snow change |")
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    for kart in vehicles:
        values = [scores[w][kart] for w in WEATHERS]
        changes = [v - values[0] if v is not None and values[0] is not None else None for v in values[1:]]
        formatted = [f"{v:+.1f}%" if v is not None else "DNF" for v in values]
        formatted += [f"{v:+.1f} pp" if v is not None else "—" for v in changes]
        print(f"| {kart} | " + " | ".join(formatted) + " |")
    for weather in WEATHERS:
        data = results[weather]
        finished = sum(data[k][c]["time"] > 0 for k in vehicles for c in COURSES)
        resets = sum(data[k][c]["resets"] for k in vehicles for c in COURSES)
        print(f"\n## {weather.capitalize()}\n")
        print(f"{finished}/{len(vehicles) * len(COURSES)} runs finished; {resets} resets in total. Times below are seconds for both laps.\n")
        lines = [line for path in (ROOT / "build/balance" / weather).glob("log_*.txt") for line in path.read_text().splitlines()]
        errors = sum("ERROR:" in line for line in lines)
        capacity_warnings = sum("Jolt Physics job system exceeded" in line for line in lines)
        print(f"Worker logs: {errors} engine errors; {capacity_warnings} Jolt job-capacity warnings during concurrent runs.\n")
        print("| Vehicle | Peach Pit | Foundry Flats | Launchpad Loop | Dune Drift | Resets |")
        print("| --- | ---: | ---: | ---: | ---: | ---: |")
        print("| Field median | " + " | ".join(f"{medians[weather][c]:.1f}" for c in COURSES) + " | — |")
        for kart in vehicles:
            times = [f"{data[kart][c]['time']:.1f}" if data[kart][c]["time"] > 0 else "DNF" for c in COURSES]
            resets = sum(data[kart][c]["resets"] for c in COURSES)
            print(f"| {kart} | " + " | ".join(times) + f" | {resets} |")
    print("\nRaw results and worker logs are in `build/balance/{clear,rain,snow}/`. Reproduce with `BALANCE_WEATHER=<weather> tools/stock-karts/balance.sh` for all three weathers, then `python3 tools/stock-karts/weather_report.py`.\n")


if __name__ == "__main__":
    main()
