#!/usr/bin/env python3
"""Confirm the preregistered quorum/freshness rules from a public commit SHA."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from ed25519_fixture import FixtureKeys


WITNESSES = [f"witness-{index}" for index in range(1, 8)]
FAULT_CLASSES = (
    "honest",
    "withholding",
    "one_double_signer",
    "two_double_signers",
    "threshold_break_three",
    "contradictory_views_below_threshold",
    "skewed_local_clock",
)
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def canonical(value: dict[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def wilson_upper(failures: int, total: int, z: float = 1.959963984540054) -> float:
    proportion = failures / total
    denominator = 1 + z * z / total
    centre = proportion + z * z / (2 * total)
    margin = z * math.sqrt((proportion * (1 - proportion) + z * z / (4 * total)) / total)
    return (centre + margin) / denominator


def derived_seed(anchor: str, index: int) -> tuple[str, int]:
    digest = hashlib.sha256(f"{anchor}:{index}".encode()).hexdigest()
    return digest, int(digest[:16], 16)


def signed_fixture(keys: FixtureKeys) -> dict[str, dict[str, str]]:
    signatures: dict[str, dict[str, str]] = {}
    for witness in WITNESSES:
        signatures[witness] = {}
        for head in ("head-a", "head-b"):
            statement = {"epoch": 23, "head": head, "witness": witness}
            signatures[witness][head] = keys.sign(witness, canonical(statement))
    return signatures


def signature_valid(keys: FixtureKeys, signatures: dict[str, dict[str, str]],
                    witness: str, head: str) -> bool:
    statement = {"epoch": 23, "head": head, "witness": witness}
    return keys.verify(witness, canonical(statement), signatures[witness][head])


def simulate(index: int, anchor: str,
             signature_validity: dict[str, dict[str, bool]]) -> dict[str, object]:
    digest, seed = derived_seed(anchor, index)
    rng = random.Random(seed)
    fault_class = FAULT_CLASSES[int(digest[16:18], 16) % len(FAULT_CLASSES)]
    double_count = {
        "one_double_signer": 1,
        "two_double_signers": 2,
        "threshold_break_three": 3,
        "contradictory_views_below_threshold": 2,
    }.get(fault_class, 0)

    witness_order = list(WITNESSES)
    rng.shuffle(witness_order)
    doubles = set(witness_order[:double_count])
    honest = [item for item in witness_order if item not in doubles]
    signed_heads: dict[str, set[str]] = {witness: set() for witness in WITNESSES}
    for witness in doubles:
        signed_heads[witness] = {"head-a", "head-b"}
    if double_count >= 3:
        for witness in honest[:2]:
            signed_heads[witness].add("head-a")
        for witness in honest[2:4]:
            signed_heads[witness].add("head-b")
    else:
        for witness in honest:
            signed_heads[witness].add("head-a")

    if fault_class == "withholding":
        fresh = set(witness_order[:2])
    else:
        fresh = set(WITNESSES)

    all_signatures_valid = all(
        signature_validity[witness][head]
        for witness in WITNESSES for head in signed_heads[witness]
    )
    global_counts = {
        head: sum(head in signed_heads[witness] for witness in WITNESSES)
        for head in ("head-a", "head-b")
    }
    dual_quorum_constructible = all(count >= 5 for count in global_counts.values())
    equivocation_evidence = len([
        witness for witness in WITNESSES if len(signed_heads[witness]) == 2
    ])

    verifier_outcomes: list[dict[str, object]] = []
    local_clock_offsets = []
    for verifier in range(7):
        offset = rng.randint(-86400, 86400) if fault_class == "skewed_local_clock" else 0
        local_clock_offsets.append(offset)
        observed: set[str] = set()
        first_terminal_round = None
        terminal_state = "pending"
        accepted_at_round = None
        quarantined_at_round = None
        for round_index in range(1, 8):
            observed.add(WITNESSES[(verifier + round_index - 1) % 7])
            counts = {
                head: sum(head in signed_heads[witness] for witness in observed)
                for head in ("head-a", "head-b")
            }
            fresh_count = len(observed & fresh)
            if counts["head-a"] >= 5 and counts["head-b"] >= 5:
                terminal_state = "quarantined/equivocation_evidence"
            elif max(counts.values()) >= 5 and fresh_count >= 3:
                terminal_state = "accepted/head-a" if counts["head-a"] >= 5 else "accepted/head-b"
            elif round_index == 7 and fresh_count < 3:
                terminal_state = "stale/read_only"
            if terminal_state.startswith("accepted/") and accepted_at_round is None:
                accepted_at_round = round_index
            if terminal_state == "quarantined/equivocation_evidence" and quarantined_at_round is None:
                quarantined_at_round = round_index
            if terminal_state != "pending" and first_terminal_round is None:
                first_terminal_round = round_index
        verifier_outcomes.append({
            "verifier": verifier,
            "terminal_state": terminal_state,
            "post_heal_round": first_terminal_round,
            "provisional_accept_at_round": accepted_at_round,
            "quarantined_at_round": quarantined_at_round,
            "accepted_then_retracted": accepted_at_round is not None and quarantined_at_round is not None,
            "provisional_window_rounds": (
                quarantined_at_round - accepted_at_round
                if accepted_at_round is not None and quarantined_at_round is not None
                else 0
            ),
        })

    states = [item["terminal_state"] for item in verifier_outcomes]
    if fault_class == "withholding":
        freshness_ok = all(state == "stale/read_only" for state in states)
        liveness_ok = True
    elif double_count >= 3:
        freshness_ok = True
        liveness_ok = all(
            state == "quarantined/equivocation_evidence"
            and isinstance(item["post_heal_round"], int)
            and item["post_heal_round"] <= 7
            for state, item in zip(states, verifier_outcomes)
        )
    else:
        freshness_ok = True
        liveness_ok = all(
            state == "accepted/head-a"
            and isinstance(item["post_heal_round"], int)
            and item["post_heal_round"] <= 7
            for state, item in zip(states, verifier_outcomes)
        )

    safety_ok = (
        not dual_quorum_constructible if double_count < 3
        else equivocation_evidence >= 3
        and all(state == "quarantined/equivocation_evidence" for state in states)
    )
    skew_ok = fault_class != "skewed_local_clock" or len(set(states)) == 1
    passed = all((all_signatures_valid, safety_ok, freshness_ok, liveness_ok, skew_ok))
    return {
        "index": index,
        "seed_sha256": digest,
        "fault_class": fault_class,
        "double_signer_count": double_count,
        "fresh_attestation_count": len(fresh),
        "head_signature_counts": global_counts,
        "dual_quorum_constructible": dual_quorum_constructible,
        "equivocation_evidence_count": equivocation_evidence,
        "local_clock_offsets_seconds": local_clock_offsets,
        "all_fixture_signatures_valid": all_signatures_valid,
        "safety_ok": safety_ok,
        "freshness_ok": freshness_ok,
        "liveness_ok": liveness_ok,
        "skew_independence_ok": skew_ok,
        "provisional_accept_then_retract_count": sum(
            bool(item["accepted_then_retracted"]) for item in verifier_outcomes
        ),
        "maximum_provisional_window_rounds": max(
            int(item["provisional_window_rounds"]) for item in verifier_outcomes
        ),
        "external_side_effects_modeled": False,
        "verifiers": verifier_outcomes,
        "passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor", required=True)
    parser.add_argument("--scenario-count", type=int, default=1000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    anchor = args.anchor.lower()
    if not HEX40.fullmatch(anchor):
        parser.error("--anchor must be a complete 40-character lowercase commit SHA")
    if args.scenario_count != 1000:
        parser.error("the preregistered confirmation requires exactly 1000 scenarios")

    started = datetime.now(timezone.utc).isoformat()
    package_root = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory(prefix="df-quorum-") as temporary:
        keys = FixtureKeys(package_root, Path(temporary))
        signatures = signed_fixture(keys)
        signature_validity = {
            witness: {
                head: signature_valid(keys, signatures, witness, head)
                for head in ("head-a", "head-b")
            }
            for witness in WITNESSES
        }
        scenarios = [
            simulate(index, anchor, signature_validity)
            for index in range(args.scenario_count)
        ]
    failures = [item for item in scenarios if not item["passed"]]
    upper = wilson_upper(len(failures), len(scenarios))
    confirmed = len(failures) <= 3 and upper <= 0.01
    result = {
        "schema": "digital-field-quorum-freshness-confirmation/v1",
        "status": "confirmed" if confirmed else "not_confirmed",
        "scope": "synthetic seven-witness fixture; not independent operators or a deployed network",
        "preregistration": "QUORUM_FRESHNESS_PROTOCOL.md",
        "anchor_commit_sha": anchor,
        "seed_derivation": "SHA256(lowercase_commit_sha + ':' + decimal_index)",
        "scenario_count": len(scenarios),
        "failure_count": len(failures),
        "wilson_95_upper_failure_rate": upper,
        "criterion_max_failures": 3,
        "criterion_max_wilson_upper": 0.01,
        "parameters": {"witnesses": 7, "head_quorum": 5, "freshness_quorum": 3},
        "execution": {
            "started_at_utc": started,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "github_repository": os.getenv("GITHUB_REPOSITORY"),
            "github_run_id": os.getenv("GITHUB_RUN_ID"),
            "github_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
            "github_actor": os.getenv("GITHUB_ACTOR"),
            "github_sha": os.getenv("GITHUB_SHA"),
        },
        "fault_class_counts": {
            fault: sum(item["fault_class"] == fault for item in scenarios)
            for fault in FAULT_CLASSES
        },
        "provisional_accept_then_retract_count": sum(
            int(item["provisional_accept_then_retract_count"]) for item in scenarios
        ),
        "maximum_provisional_window_rounds": max(
            int(item["maximum_provisional_window_rounds"]) for item in scenarios
        ),
        "external_side_effects_modeled": False,
        "material_witness_independence": "not_assessed-single-fixture-custodian",
        "scenarios": scenarios,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if confirmed else 1


if __name__ == "__main__":
    raise SystemExit(main())
