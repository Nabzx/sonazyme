#!/usr/bin/env python3
"""Learn a dosing policy inside the cooling-loop world model, and score it.

Runs in about a second. Compares the learned policy against the two things an
operator does today: nothing, and a fixed schedule.

    python scripts/loop_policy.py
    python scripts/loop_policy.py --json runs/loop-policy.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from sonazyme.loop.policy import LEVELS, SENSORS, act, train
from sonazyme.loop.world import CEILING_C, Loop


def run(loop: Loop, choose, hours: int) -> dict:
    over, doses, peak, film = 0, 0, 0.0, 0.0
    for hour in range(hours):
        dose = choose(loop, hour)
        loop.step(dose)
        doses += dose is not None
        peak = max(peak, loop.temperature())
        film += sum(loop.film) / loop.sections
        over += loop.temperature() > CEILING_C
    return {
        "hours_over_ceiling": over,
        "doses": doses,
        "peak_c": round(peak, 1),
        "mean_film": round(film / hours, 3),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hours", type=int, default=240)
    parser.add_argument("--episodes", type=int, default=2600)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--every", type=int, default=12, help="the fixed schedule's interval")
    parser.add_argument("--loops", type=int, default=8, help="how many loops to score on")
    parser.add_argument("--json", type=Path)
    parser.add_argument(
        "--export",
        type=Path,
        help="write the learned table where the page can read it",
    )
    args = parser.parse_args(argv)

    started = time.perf_counter()
    table = train(episodes=args.episodes, seed=args.seed)
    trained = time.perf_counter() - started

    def untreated(loop, hour):
        return None

    def scheduled(loop, hour):
        # Dose on the clock, at the section that fouls fastest.
        return loop.hot if hour % args.every == 0 else None

    def learned(loop, hour):
        return act(table, loop)

    # Score on loops the policy never trained on, and average, so the table
    # below is not one lucky run.
    results = {}
    for name, choose in (("untreated", untreated), ("scheduled", scheduled), ("learned", learned)):
        rows = [
            run(Loop(seed=args.seed + 101 + index), choose, args.hours)
            for index in range(args.loops)
        ]
        results[name] = {
            key: round(sum(row[key] for row in rows) / len(rows), 2) for key in rows[0]
        }

    report = {
        "schema_version": 1,
        "kind": "loop-policy",
        "basis": "simulation",
        "note": (
            "A policy learned inside the Sonazyme cooling-loop world model. No loop has "
            "been measured and no treatment has been applied to anything real."
        ),
        "settings": {
            "hours": args.hours,
            "loops_scored": args.loops,
            "episodes": args.episodes,
            "seed": args.seed,
            "schedule_every_hours": args.every,
            "ceiling_c": CEILING_C,
        },
        "states_learned": len(table),
        "train_seconds": round(trained, 2),
        "results": results,
    }

    width = max(len(name) for name in results)
    print(f"world model, {args.hours} h   ceiling {CEILING_C:.0f} C")
    print(f"{'':{width}}  over ceiling   doses   peak C   mean film")
    for name, row in results.items():
        print(
            f"{name:{width}}  {row['hours_over_ceiling']:>7} h      "
            f"{row['doses']:>3}    {row['peak_c']:>5}      {row['mean_film']:.3f}"
        )
    print(f"\nlearned {len(table)} states in {trained:.2f}s. Simulation only.")
    if args.export:
        args.export.parent.mkdir(parents=True, exist_ok=True)
        args.export.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "loop-policy",
                    "basis": "simulation",
                    "note": report["note"],
                    "sections": Loop().sections,
                    "sensors": list(SENSORS),
                    "ceiling_c": CEILING_C,
                    "levels": LEVELS,
                    "results": results,
                    # "hot,worst,where" -> a value for each action, action 0 is
                    # "do not dose" and action n+1 is "dose section n".
                    "table": {",".join(map(str, state)): [round(v, 2) for v in values]
                              for state, values in sorted(table.items())},
                }
            )
            + "\n"
        )
        print(f"policy exported to {args.export}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + "\n")
        print(f"written to {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
