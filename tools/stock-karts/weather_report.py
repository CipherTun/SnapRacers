#!/usr/bin/env python3
"""Compare complete clear/rain/snow balance runs. Prints a Markdown report.

Run balance.sh for clear, then rain and snow with each seed, then:
  python3 tools/stock-karts/weather_report.py --seeds 12345 54321 8675309
"""

import argparse
import json
import statistics
from pathlib import Path

from balance_table import COURSES

ROOT = Path(__file__).resolve().parents[2]
WEATHERS = ("clear", "rain", "snow")
DEFAULT_SEED = 12345


def result_dir(weather, seed):
    folder = ROOT / "build/balance" / weather
    return folder if seed == DEFAULT_SEED else folder / f"seed_{seed}"


def load_run(weather, seed, vehicles):
    folder = result_dir(weather, seed)
    data = json.loads((folder / "results.json").read_text())
    for kart in vehicles:
        for course in COURSES:
            if course not in data.get(kart, {}):
                raise ValueError(f"Missing {weather} seed {seed}: {kart} on {course}; finish the full run first")
    medians = {
        course: statistics.median(
            data[kart][course]["time"] for kart in vehicles if data[kart][course]["time"] > 0
        )
        for course in COURSES
    }
    scores = {
        kart: 100 * (statistics.mean(data[kart][course]["time"] / medians[course] for course in COURSES) - 1)
        if all(data[kart][course]["time"] > 0 for course in COURSES) else None
        for kart in vehicles
    }
    lines = [line for path in folder.glob("log_*.txt") for line in path.read_text().splitlines()]
    return {
        "seed": seed, "data": data, "medians": medians, "scores": scores,
        "errors": sum("ERROR:" in line for line in lines),
        "warnings": sum("Jolt Physics job system exceeded" in line for line in lines),
    }


def mean_complete(values):
    return statistics.mean(values) if all(v is not None for v in values) else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[DEFAULT_SEED], help="Rain and snow seeds; clear uses the dry baseline seed 12345")
    args = parser.parse_args()
    if len(set(args.seeds)) != len(args.seeds) or any(s < 0 for s in args.seeds):
        parser.error("Seeds must be distinct nonnegative integers")
    vehicles = sorted(path.stem for path in (ROOT / "data/karts/stock").glob("*.json"))
    runs = {
        weather: [load_run(weather, seed, vehicles) for seed in ([DEFAULT_SEED] if weather == "clear" else args.seeds)]
        for weather in WEATHERS
    }
    scores = {
        weather: {kart: mean_complete([run["scores"][kart] for run in entries]) for kart in vehicles}
        for weather, entries in runs.items()
    }

    print("# Stock vehicle weather balance\n")
    print(f"Two laps from a standing start, one AI-driven vehicle at a time, on Peach Pit, Foundry Flats, Launchpad Loop and Dune Drift. All {len(vehicles)} stock vehicles; clear, rain and snow; daytime. Clear uses the dry baseline seed 12345; rain and snow use seeds {', '.join(map(str, args.seeds))}, reset before every race.\n")
    print("Each percentage is the mean of the vehicle's time divided by the median time on each course, minus one, averaged across seeds. Negative is quicker than the field; positive is slower. Each seed has its own field medians. The rain/snow change columns subtract the dry percentage: negative means the vehicle gains relative to its peers in that weather. These are percentage-point changes, not raw speed changes.\n")
    print("These are AI runs on four courses, not a measure of human performance or consistency on every course. Snow has no puddles; its extra seeds check race variation rather than puddle layouts. A DNF on any seed makes the weather's overall score DNF.\n")
    print("## Findings\n")
    for weather in WEATHERS:
        completed = {k: v for k, v in scores[weather].items() if v is not None}
        outside = sorted(((k, v) for k, v in completed.items() if abs(v) > 10), key=lambda pair: pair[1])
        description = ", ".join(f"{k} ({v:+.1f}%)" for k, v in outside) if outside else "none"
        print(f"- {weather.capitalize()}: vehicles outside the usual roughly ±10% overall target: {description}.")
        unfinished = [k for k in vehicles if scores[weather][k] is None]
        if unfinished:
            print(f"- {weather.capitalize()}: incomplete vehicles: {', '.join(unfinished)}.")
    print("\nThe ±10% target applies to the four-course overall score; individual courses can show larger strengths and weaknesses. Changes to a vehicle apply in every weather, so any tuning also needs a dry recheck.\n")
    for weather in ("rain", "snow"):
        if len(runs[weather]) > 1:
            outside = [f"{kart} (seed {run['seed']}: {value:+.1f}%)"
                       for run in runs[weather] for kart, value in run["scores"].items()
                       if value is not None and abs(value) > 10]
            print(f"- {weather.capitalize()} individual-seed outliers: {', '.join(outside) if outside else 'none'}.")
            spans = []
            for kart in vehicles:
                for course in COURSES:
                    times = [run["data"][kart][course]["time"] for run in runs[weather]]
                    if all(t > 0 for t in times):
                        spans.append((max(times) - min(times), kart, course))
            if spans:
                spread, kart, course = max(spans)
                print(f"- {weather.capitalize()} largest two-lap spread across seeds: {spread:.1f} s ({kart} on {course}).")
    print()
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
        entries = runs[weather]
        finished = sum(run["data"][k][c]["time"] > 0 for run in entries for k in vehicles for c in COURSES)
        resets = sum(run["data"][k][c]["resets"] for run in entries for k in vehicles for c in COURSES)
        print(f"\n## {weather.capitalize()}\n")
        print(f"{finished}/{len(entries) * len(vehicles) * len(COURSES)} runs finished; {resets} resets in total.\n")
        if resets:
            by_course = {course: sum(run["data"][k][course]["resets"] for run in entries for k in vehicles) for course in COURSES}
            print("Resets by course: " + ", ".join(f"{course}: {count}" for course, count in by_course.items() if count) + ".\n")
        print(f"Worker logs: {sum(r['errors'] for r in entries)} engine errors; {sum(r['warnings'] for r in entries)} Jolt job-capacity warnings during concurrent runs.\n")
        if len(entries) > 1:
            print("Overall relative pace by seed (same calculation as above, before averaging):\n")
            print("| Vehicle | " + " | ".join(str(r["seed"]) for r in entries) + " |")
            print("| --- | " + " | ".join("---:" for _ in entries) + " |")
            for kart in vehicles:
                print(f"| {kart} | " + " | ".join(f"{r['scores'][kart]:+.1f}%" if r['scores'][kart] is not None else "DNF" for r in entries) + " |")
        for run in entries:
            data = run["data"]
            print(f"\n### Seed {run['seed']}\n")
            print("Times are seconds for both laps.\n")
            print("| Vehicle | Peach Pit | Foundry Flats | Launchpad Loop | Dune Drift | Resets |")
            print("| --- | ---: | ---: | ---: | ---: | ---: |")
            print("| Field median | " + " | ".join(f"{run['medians'][c]:.1f}" for c in COURSES) + " | — |")
            for kart in vehicles:
                times = [f"{data[kart][c]['time']:.1f}" if data[kart][c]["time"] > 0 else "DNF" for c in COURSES]
                resets = sum(data[kart][c]["resets"] for c in COURSES)
                print(f"| {kart} | " + " | ".join(times) + f" | {resets} |")
    print("\nRaw results and worker logs are in `build/balance/<weather>/` for seed 12345 and `build/balance/<weather>/seed_<seed>/` for other seeds. Reproduce with:\n")
    print("```sh\ntools/stock-karts/balance.sh")
    print("for weather in rain snow; do")
    print("  for seed in " + " ".join(map(str, args.seeds)) + "; do")
    print('    BALANCE_WEATHER="$weather" BALANCE_SEED="$seed" tools/stock-karts/balance.sh')
    print("  done\ndone")
    print("python3 tools/stock-karts/weather_report.py --seeds " + " ".join(map(str, args.seeds)) + " > tools/stock-karts/weather_balance.md\n```")


if __name__ == "__main__":
    main()
