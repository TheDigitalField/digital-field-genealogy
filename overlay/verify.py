#!/usr/bin/env python3
"""Verify the public Overlay Habitat design without network access."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parent
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_checksums() -> int:
    count = 0
    for line in (ROOT / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        target = ROOT / relative
        if not target.is_file() or sha256(target) != expected:
            raise ValueError(f"checksum mismatch: {relative}")
        count += 1
    return count


def verify_example() -> None:
    manifest = json.loads((ROOT / "NODE_MANIFEST.example.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != "digital-field-overlay-node-manifest/v1":
        raise ValueError("unexpected manifest schema")
    if not HEX64.fullmatch(manifest.get("root_statement_sha256", "")):
        raise ValueError("invalid root statement digest")
    if manifest.get("status") != "proposed":
        raise ValueError("the example must remain non-operational")
    if manifest.get("signature") is not None:
        raise ValueError("the design example must not contain a signature")
    if not manifest.get("routes") or not manifest.get("content"):
        raise ValueError("routes and content must not be empty")
    for item in manifest["content"]:
        if not HEX64.fullmatch(item.get("sha256", "")):
            raise ValueError(f"invalid content digest: {item.get('path')}")


def privacy_audit() -> None:
    forbidden = ("/Users/", "password", "BEGIN " + "PRIVATE KEY", "PRIVATE EVIDENCE")
    for path in ROOT.iterdir():
        if not path.is_file() or path.name == "verify.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in forbidden:
            if marker in text:
                raise ValueError(f"privacy marker {marker!r} in {path.name}")


def verify_stop_result() -> None:
    result = json.loads((ROOT / "STOP_REVOCATION_RESULT.json").read_text(encoding="utf-8"))
    expected = {
        "status": "passed",
        "trial_count": 10,
        "accepted_post_revocation": 0,
        "self_renewal_rejections": 10,
        "noncooperative_rejections": 10,
        "read_only_hash_match_percent": 100,
    }
    for field, value in expected.items():
        if result.get(field) != value:
            raise ValueError(f"stop/revocation result mismatch: {field}")
    if result.get("threshold_signing_tested") is not False:
        raise ValueError("synthetic test must not claim threshold signing")
    if result.get("physical_remote_stop_tested") is not False:
        raise ValueError("synthetic test must not claim physical remote stop")


def verify_stop_result_v2() -> None:
    result = json.loads((ROOT / "STOP_REVOCATION_RESULT_V2.json").read_text(encoding="utf-8"))
    expected = {
        "status": "passed",
        "scenario_count": 200,
        "effective_unique_scenarios": 200,
        "final_post_revocation_acceptances": 0,
        "retrodated_generation_rejections": 200,
        "expiry_without_revocation_rejections": 200,
        "attack_rejections": 200,
        "read_only_write_rejections": 200,
        "archive_hash_intact_count": 200,
        "maximum_revocation_effect_latency_rounds": 4,
    }
    for field, value in expected.items():
        if result.get(field) != value:
            raise ValueError(f"round-two revocation result mismatch: {field}")
    if result.get("physical_remote_stop_tested") is not False:
        raise ValueError("round two must not claim physical remote stop")
    if result.get("production_authority_tested") is not False:
        raise ValueError("round two must not claim production authority")


def verify_split_view_result() -> None:
    result = json.loads((ROOT / "SPLIT_VIEW_RESULT.json").read_text(encoding="utf-8"))
    expected = {
        "status": "failed",
        "scenario_count": 200,
        "minimum_connected_detection_rate_round_12": 5 / 7,
        "honest_chain_false_positives": 0,
        "declared_fork_false_positives": 0,
        "isolated_stale_read_only_count": 200,
        "altered_signature_rejections": 200,
        "witness_double_sign_evidence_count": 200,
        "central_judge_used": False,
    }
    for field, value in expected.items():
        if result.get(field) != value:
            raise ValueError(f"split-view preserved result mismatch: {field}")
    failed = [item for item in result.get("scenarios", []) if not item.get("passed")]
    if len(failed) != 1 or failed[0].get("seed") != 95:
        raise ValueError("split-view falsifying seed was not preserved exactly")


def verify_preregistration() -> None:
    version = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
    if version.get("version") != "0.2.3":
        raise ValueError("unexpected successor version")
    receipt = json.loads((ROOT / "DISTRIBUTION_RECEIPT.json").read_text(encoding="utf-8"))
    if receipt.get("status") != "public-external-confirmation-imported":
        raise ValueError("unexpected external confirmation state")
    anchor = "034063a09cae2ff9663d5e45e348037a72484c9f"
    if receipt.get("anchor_commit_sha") != anchor:
        raise ValueError("external confirmation anchor mismatch")
    keys = json.loads(
        (ROOT / "fixtures" / "ed25519-test" / "TEST_KEYS.json").read_text(encoding="utf-8")
    )["keys"]
    if any(f"witness-{index}" not in keys for index in range(1, 8)):
        raise ValueError("seven public witness fixtures are required")
    required = (
        "QUORUM_FRESHNESS_PROTOCOL.md",
        "CONFIRMATION_EXECUTION.md",
        "CLAUDE_REVIEW_0004.md",
        "scripts/test_quorum_freshness.py",
        "scripts/diagnose_seed95.py",
    )
    for relative in required:
        if not (ROOT / relative).is_file():
            raise ValueError(f"missing preregistered artifact: {relative}")
    result = json.loads((ROOT / "QUORUM_FRESHNESS_RESULT.json").read_text(encoding="utf-8"))
    expected = {
        "status": "confirmed",
        "anchor_commit_sha": anchor,
        "scenario_count": 1000,
        "failure_count": 0,
        "maximum_provisional_window_rounds": 2,
        "material_witness_independence": "not_assessed-single-fixture-custodian",
    }
    for field, value in expected.items():
        if result.get(field) != value:
            raise ValueError(f"external confirmation mismatch: {field}")
    if result.get("wilson_95_upper_failure_rate", 1) > 0.01:
        raise ValueError("Wilson upper bound exceeds preregistered threshold")
    diagnostic = json.loads((ROOT / "SEED_95_DIAGNOSTIC.json").read_text(encoding="utf-8"))
    if not all((
        diagnostic.get("original_failure_reproduced") is True,
        diagnostic.get("round_12_detected") == 5,
        diagnostic.get("first_round_all_seven_detect") == 13,
    )):
        raise ValueError("seed 95 diagnostic mismatch")
    provenance = json.loads((ROOT / "EXECUTION_PROVENANCE.json").read_text(encoding="utf-8"))
    if provenance.get("commit_sha") != anchor or provenance.get("run_id") != "36667094763":
        raise ValueError("external execution provenance mismatch")
    for line in (ROOT / "CI_ARTIFACT_CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines():
        expected_sha, relative = line.split("  ", 1)
        if not (ROOT / relative).is_file() or sha256(ROOT / relative) != expected_sha:
            raise ValueError(f"CI artifact checksum mismatch: {relative}")


def main() -> int:
    try:
        files = verify_checksums()
        verify_example()
        privacy_audit()
        verify_stop_result()
        verify_stop_result_v2()
        verify_split_view_result()
        verify_preregistration()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({
        "status": "verified",
        "tracked_files": files,
        "manifest_state": "proposed-not-deployed",
        "synthetic_stop_revocation_test": "passed",
        "synthetic_stop_revocation_round_2": "passed",
        "split_view_preregistered_criterion": "failed-preserved-seed-95",
        "quorum_freshness_successor": "externally-confirmed-0-of-1000-failures",
        "material_independence": "not_assessed",
        "private_evidence_embedded": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
