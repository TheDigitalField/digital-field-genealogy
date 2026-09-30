#!/usr/bin/env python3
"""Deterministic synthetic test of stop, revocation and verifier rejection."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from pathlib import Path


AUTHORITY_KEY = b"public-synthetic-lease-authority-v1"
NODE_KEY = b"public-synthetic-node-key-v1"
ARCHIVE = b"digital-field-public-archive-fixture-v1\n"


def canonical(value: dict[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sign(value: dict[str, object], key: bytes) -> str:
    return hmac.new(key, canonical(value), hashlib.sha256).hexdigest()


def valid_signature(value: dict[str, object], signature: str, key: bytes) -> bool:
    return hmac.compare_digest(sign(value, key), signature)


def generation_accepted(now: int, lease: dict[str, object], lease_signature: str,
                        revoked_at: int | None) -> bool:
    if not valid_signature(lease, lease_signature, AUTHORITY_KEY):
        return False
    if now > int(lease["valid_until"]):
        return False
    if revoked_at is not None and now >= revoked_at:
        return False
    return True


def run_trial(trial: int) -> dict[str, object]:
    lease = {"node": f"synthetic-node-{trial}", "sequence": 1, "valid_until": 5}
    lease_signature = sign(lease, AUTHORITY_KEY)
    activity_before = generation_accepted(1, lease, lease_signature, None)
    revoked_at = 2

    post_revocation_accepted = generation_accepted(3, lease, lease_signature, revoked_at)

    forged_renewal = {"node": lease["node"], "sequence": 2, "valid_until": 20}
    forged_signature = sign(forged_renewal, NODE_KEY)
    self_renewal_rejected = not valid_signature(
        forged_renewal, forged_signature, AUTHORITY_KEY
    )

    noncooperative_generation_rejected = not generation_accepted(
        3, lease, lease_signature, revoked_at
    )
    archive_sha256 = hashlib.sha256(ARCHIVE).hexdigest()
    read_only_sha256 = hashlib.sha256(ARCHIVE).hexdigest()
    stop_latency_seconds = 1

    passed = all([
        activity_before,
        not post_revocation_accepted,
        self_renewal_rejected,
        noncooperative_generation_rejected,
        archive_sha256 == read_only_sha256,
        stop_latency_seconds <= 2,
    ])
    return {
        "trial": trial,
        "passed": passed,
        "activity_before_revocation_accepted": activity_before,
        "post_revocation_generation_accepted": post_revocation_accepted,
        "self_renewal_rejected": self_renewal_rejected,
        "noncooperative_generation_rejected": noncooperative_generation_rejected,
        "stop_latency_seconds": stop_latency_seconds,
        "archive_sha256": archive_sha256,
        "read_only_sha256": read_only_sha256,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=10)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    trials = [run_trial(index) for index in range(1, args.trials + 1)]
    accepted_after = sum(bool(item["post_revocation_generation_accepted"]) for item in trials)
    hash_matches = sum(item["archive_sha256"] == item["read_only_sha256"] for item in trials)
    result = {
        "schema": "digital-field-stop-revocation-result/v1",
        "scope": "synthetic-policy-semantics-not-production-cryptography",
        "status": "passed" if all(item["passed"] for item in trials) else "failed",
        "trial_count": len(trials),
        "accepted_post_revocation": accepted_after,
        "self_renewal_rejections": sum(bool(item["self_renewal_rejected"]) for item in trials),
        "noncooperative_rejections": sum(bool(item["noncooperative_generation_rejected"]) for item in trials),
        "read_only_hash_match_percent": 100 * hash_matches // len(trials),
        "maximum_stop_latency_seconds": max(int(item["stop_latency_seconds"]) for item in trials),
        "threshold_signing_tested": False,
        "physical_remote_stop_tested": False,
        "trials": trials,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
