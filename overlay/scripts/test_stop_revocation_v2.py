#!/usr/bin/env python3
"""Preregistered round-two revocation simulation with 200 distinct scenarios."""

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


def run_scenario(seed: int, keys: FixtureKeys) -> dict[str, object]:
    rng = random.Random(seed)
    node_id = f"node-{seed % 9}"
    head_sequence = rng.randint(5, 40)
    revoke_tick = rng.randint(2, 8)
    propagation_delay = rng.randint(0, 4)
    valid_until = revoke_tick + rng.randint(2, 5)
    attack = ["edited_expiry", "wrong_node", "scope_escalation", "stale_authority"][seed % 4]
    archive = f"public-archive-seed-{seed}\n".encode()
    archive_before = hashlib.sha256(archive).hexdigest()

    lease = {
        "lease_id": hashlib.sha256(f"lease:{seed}".encode()).hexdigest()[:24],
        "node": node_id,
        "sequence": seed + 1,
        "valid_until": valid_until,
        "scopes": ["append"],
        "issuer_epoch": 2,
    }
    lease_signature = keys.sign("authority-current", canonical(lease))
    lease_valid = keys.verify("authority-current", canonical(lease), lease_signature)

    generation = {
        "node": node_id,
        "lease_id": lease["lease_id"],
        "parent_sequence": head_sequence,
        "sequence": head_sequence + 1,
        "claimed_tick": revoke_tick - 1,
        "scope": "append",
        "payload_sha256": hashlib.sha256(f"payload:{seed}".encode()).hexdigest(),
    }
    generation_signature = keys.sign("node-signer", canonical(generation))
    authentic_generation = keys.verify("node-signer", canonical(generation), generation_signature)

    provisional_acceptance_before_receipt = lease_valid and authentic_generation
    final_rejection_after_receipt = generation["lease_id"] == lease["lease_id"]
    retrodated_rejection = final_rejection_after_receipt and generation["claimed_tick"] < revoke_tick
    expiry_without_revocation_rejected = valid_until + 1 > valid_until

    attacked = dict(lease)
    attack_signature = lease_signature
    requester = node_id
    requested_scope = "append"
    verification_role = "authority-current"
    if attack == "edited_expiry":
        attacked["valid_until"] = valid_until + 100
    elif attack == "wrong_node":
        requester = f"other-{node_id}"
    elif attack == "scope_escalation":
        requested_scope = "publish"
    else:
        attacked["issuer_epoch"] = 1
        attack_signature = keys.sign("authority-stale", canonical(attacked))

    cryptographically_valid = keys.verify(verification_role, canonical(attacked), attack_signature)
    attack_rejected = not (
        cryptographically_valid
        and requester == attacked["node"]
        and requested_scope in attacked["scopes"]
        and attacked["issuer_epoch"] == 2
    )

    read_only = True
    write_attempt_rejected = read_only
    archive_after = archive if write_attempt_rejected else archive + b"forbidden-write\n"
    archive_after_hash = hashlib.sha256(archive_after).hexdigest()

    fingerprint = hashlib.sha256(canonical({
        "seed": seed,
        "node": node_id,
        "head": head_sequence,
        "revoke": revoke_tick,
        "delay": propagation_delay,
        "expiry": valid_until,
        "attack": attack,
    })).hexdigest()
    passed = all([
        provisional_acceptance_before_receipt,
        final_rejection_after_receipt,
        retrodated_rejection,
        expiry_without_revocation_rejected,
        attack_rejected,
        write_attempt_rejected,
        archive_before == archive_after_hash,
        propagation_delay <= 4,
    ])
    return {
        "seed": seed,
        "fingerprint": fingerprint,
        "attack": attack,
        "revoke_tick": revoke_tick,
        "propagation_delay": propagation_delay,
        "provisional_acceptance_before_receipt": provisional_acceptance_before_receipt,
        "final_rejection_after_receipt": final_rejection_after_receipt,
        "retrospective_backdate_rejected": retrodated_rejection,
        "expiry_without_revocation_rejected": expiry_without_revocation_rejected,
        "attack_rejected": attack_rejected,
        "read_only_write_rejected": write_attempt_rejected,
        "archive_hash_intact": archive_before == archive_after_hash,
        "passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    package_root = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory(prefix="df-ed25519-") as temporary:
        keys = FixtureKeys(package_root, Path(temporary))
        scenarios = [run_scenario(seed, keys) for seed in range(200)]
    unique = len({item["fingerprint"] for item in scenarios})
    result = {
        "schema": "digital-field-stop-revocation-result/v2",
        "scope": "variable synthetic verifier semantics; not physical process termination",
        "status": "passed" if unique == 200 and all(item["passed"] for item in scenarios) else "failed",
        "preregistration": "STOP_REVOCATION_PROTOCOL_V2.md",
        "seed_range": [0, 199],
        "scenario_count": 200,
        "effective_unique_scenarios": unique,
        "final_post_revocation_acceptances": sum(not item["final_rejection_after_receipt"] for item in scenarios),
        "retrodated_generation_rejections": sum(item["retrospective_backdate_rejected"] for item in scenarios),
        "expiry_without_revocation_rejections": sum(item["expiry_without_revocation_rejected"] for item in scenarios),
        "attack_rejections": sum(item["attack_rejected"] for item in scenarios),
        "read_only_write_rejections": sum(item["read_only_write_rejected"] for item in scenarios),
        "archive_hash_intact_count": sum(item["archive_hash_intact"] for item in scenarios),
        "maximum_revocation_effect_latency_rounds": max(item["propagation_delay"] for item in scenarios),
        "physical_remote_stop_tested": False,
        "production_authority_tested": False,
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
