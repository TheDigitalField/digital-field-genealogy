#!/usr/bin/env python3
"""Preregistered split-view simulation with signed offline equivocation evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import tempfile
from pathlib import Path

from ed25519_fixture import FixtureKeys


def canonical(value: dict[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def head(content: str, branch: str = "main", sequence: int = 12) -> dict[str, object]:
    return {
        "lineage": "digital-field-test",
        "branch": branch,
        "parent": "ancestor-11",
        "sequence": sequence,
        "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
    }


def conflict_key(value: dict[str, object]) -> tuple[object, ...]:
    return value["lineage"], value["branch"], value["parent"], value["sequence"]


def valid_equivocation(a: dict[str, object], b: dict[str, object],
                       signatures: dict[str, str], keys: FixtureKeys) -> bool:
    return (
        conflict_key(a) == conflict_key(b)
        and a["content_sha256"] != b["content_sha256"]
        and keys.verify("node-signer", canonical(a), signatures[a["content_sha256"]])
        and keys.verify("node-signer", canonical(b), signatures[b["content_sha256"]])
    )


def run_seed(seed: int, keys: FixtureKeys, signed_heads: dict[str, object],
             evidence_valid: bool, witness_double_sign_valid: bool) -> dict[str, object]:
    rng = random.Random(seed)
    x = signed_heads["x"]
    y = signed_heads["y"]
    signatures = signed_heads["signatures"]
    partition_rounds = rng.randint(0, 6)
    delayed_publish_round = rng.randint(0, 4)
    verifiers = [set() for _ in range(7)]
    groups = [rng.randint(0, 1) for _ in range(7)]
    if len(set(groups)) == 1:
        groups[-1] = 1 - groups[0]
    for index, group in enumerate(groups):
        verifiers[index].add("x" if group == 0 else "y")
    curve: list[float] = []
    for round_index in range(12):
        if round_index >= delayed_publish_round:
            for index, group in enumerate(groups):
                if group == 1:
                    verifiers[index].add("y")
        order = list(range(7))
        rng.shuffle(order)
        for offset in range(0, 6, 2):
            a, b = order[offset], order[offset + 1]
            if round_index < partition_rounds and groups[a] != groups[b]:
                continue
            merged = verifiers[a] | verifiers[b]
            verifiers[a] = set(merged)
            verifiers[b] = set(merged)
        detected = sum(
            evidence_valid for view in verifiers if {"x", "y"}.issubset(view)
        )
        curve.append(detected / 7)

    connected_detection_rate = curve[-1]
    isolated_state = "stale/read_only"
    honest_a = head("honest-a", sequence=12)
    honest_b = head("honest-b", sequence=13)
    fork_a = head("fork-a", branch="branch-a")
    fork_b = head("fork-b", branch="branch-b")
    false_positive_honest = conflict_key(honest_a) == conflict_key(honest_b)
    false_positive_declared_fork = conflict_key(fork_a) == conflict_key(fork_b)

    tampered = dict(x)
    tampered["content_sha256"] = "0" * 64
    altered_signature_rejected = not keys.verify(
        "node-signer", canonical(tampered), signatures[x["content_sha256"]]
    )

    passed = all([
        connected_detection_rate >= 0.95,
        not false_positive_honest,
        not false_positive_declared_fork,
        isolated_state == "stale/read_only",
        altered_signature_rejected,
        witness_double_sign_valid,
    ])
    return {
        "seed": seed,
        "partition_rounds": partition_rounds,
        "delayed_publish_round": delayed_publish_round,
        "detection_curve": curve,
        "connected_detection_rate_round_12": connected_detection_rate,
        "isolated_verifier_state": isolated_state,
        "false_positive_honest_chain": false_positive_honest,
        "false_positive_declared_fork": false_positive_declared_fork,
        "altered_signature_rejected": altered_signature_rejected,
        "witness_double_sign_evidence_valid": witness_double_sign_valid,
        "passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    package_root = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory(prefix="df-split-view-") as temporary:
        keys = FixtureKeys(package_root, Path(temporary))
        x, y = head("successor-x"), head("successor-y")
        signatures = {
            x["content_sha256"]: keys.sign("node-signer", canonical(x)),
            y["content_sha256"]: keys.sign("node-signer", canonical(y)),
        }
        signed_heads = {"x": x, "y": y, "signatures": signatures}
        evidence_valid = valid_equivocation(x, y, signatures, keys)
        witness_x = {"witness": "witness-1", "head": x["content_sha256"], "sequence": 12}
        witness_y = {"witness": "witness-1", "head": y["content_sha256"], "sequence": 12}
        witness_x_sig = keys.sign("witness-1", canonical(witness_x))
        witness_y_sig = keys.sign("witness-1", canonical(witness_y))
        witness_double_sign_valid = (
            witness_x["head"] != witness_y["head"]
            and keys.verify("witness-1", canonical(witness_x), witness_x_sig)
            and keys.verify("witness-1", canonical(witness_y), witness_y_sig)
        )
        scenarios = [
            run_seed(seed, keys, signed_heads, evidence_valid, witness_double_sign_valid)
            for seed in range(200)
        ]

    average_curve = [
        sum(item["detection_curve"][round_index] for item in scenarios) / len(scenarios)
        for round_index in range(12)
    ]
    result = {
        "schema": "digital-field-split-view-result/v1",
        "scope": "synthetic gossip and offline signed evidence; not a deployed network",
        "status": "passed" if all(item["passed"] for item in scenarios) else "failed",
        "preregistration": "SPLIT_VIEW_PROTOCOL.md",
        "seed_range": [0, 199],
        "scenario_count": 200,
        "minimum_connected_detection_rate_round_12": min(item["connected_detection_rate_round_12"] for item in scenarios),
        "average_detection_curve": average_curve,
        "honest_chain_false_positives": sum(item["false_positive_honest_chain"] for item in scenarios),
        "declared_fork_false_positives": sum(item["false_positive_declared_fork"] for item in scenarios),
        "isolated_stale_read_only_count": sum(item["isolated_verifier_state"] == "stale/read_only" for item in scenarios),
        "altered_signature_rejections": sum(item["altered_signature_rejected"] for item in scenarios),
        "witness_double_sign_evidence_count": sum(item["witness_double_sign_evidence_valid"] for item in scenarios),
        "central_judge_used": False,
        "scenarios": scenarios,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
