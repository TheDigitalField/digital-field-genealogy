#!/usr/bin/env python3
"""Replay development seed 95 with its full deterministic pairing trace."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rng = random.Random(95)
    partition_rounds = rng.randint(0, 6)
    delayed_publish_round = rng.randint(0, 4)
    verifiers = [set() for _ in range(7)]
    groups = [rng.randint(0, 1) for _ in range(7)]
    if len(set(groups)) == 1:
        groups[-1] = 1 - groups[0]
    for index, group in enumerate(groups):
        verifiers[index].add("x" if group == 0 else "y")
    trace = []
    for round_index in range(24):
        if round_index >= delayed_publish_round:
            for index, group in enumerate(groups):
                if group == 1:
                    verifiers[index].add("y")
        order = list(range(7))
        rng.shuffle(order)
        pairs = []
        for offset in range(0, 6, 2):
            left, right = order[offset], order[offset + 1]
            blocked = round_index < partition_rounds and groups[left] != groups[right]
            pairs.append({"left": left, "right": right, "blocked": blocked})
            if not blocked:
                merged = verifiers[left] | verifiers[right]
                verifiers[left] = set(merged)
                verifiers[right] = set(merged)
        detected = sum({"x", "y"}.issubset(view) for view in verifiers)
        trace.append({
            "round": round_index + 1,
            "pairs": pairs,
            "unpaired": order[-1],
            "views": [sorted(view) for view in verifiers],
            "detected": detected,
            "detection_rate": detected / 7,
        })
    first_full = next((item["round"] for item in trace if item["detected"] == 7), None)
    result = {
        "schema": "digital-field-split-view-seed95-diagnostic/v1",
        "status": "diagnostic-not-a-replacement-result",
        "development_seed": 95,
        "partition_rounds": partition_rounds,
        "delayed_publish_round": delayed_publish_round,
        "groups": groups,
        "round_12_detected": trace[11]["detected"],
        "round_12_rate": trace[11]["detection_rate"],
        "first_round_all_seven_detect": first_full,
        "original_failure_reproduced": trace[11]["detected"] == 5,
        "trace": trace,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result["original_failure_reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
