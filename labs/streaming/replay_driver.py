"""Raw synthetic transport trace emitter, NOT Kafka/Flink or logical deduplication."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

SCENARIOS = Path(__file__).resolve().parent / "scenarios"
NAMES = {"clean", "replay", "out_of_order", "conflict"}


def load_trace(name: str) -> list[dict]:
    if name not in NAMES:
        raise ValueError(f"Unknown scenario: {name}")
    rows = [json.loads(line) for line in (SCENARIOS / f"{name}.jsonl").read_text().splitlines() if line.strip()]
    if not rows or [r.get("step") for r in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("Invalid contiguous trace steps")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=sorted(NAMES), required=True)
    parser.add_argument("--from-step", type=int, default=1)
    parser.add_argument("--repeat-step", type=int, default=None)
    args = parser.parse_args()
    trace = load_trace(args.scenario)
    if not (1 <= args.from_step <= len(trace) + 1):
        parser.error("invalid --from-step")
    if args.repeat_step is not None and not (1 <= args.repeat_step <= len(trace)):
        parser.error("invalid --repeat-step")
    for observation in trace[args.from_step - 1:]:
        print(json.dumps(observation, sort_keys=True))
    if args.repeat_step is not None:
        print(json.dumps(trace[args.repeat_step - 1], sort_keys=True))


if __name__ == "__main__":
    main()
