#!/usr/bin/env python3
"""Run and verify the finite two-stage Friction Beacon v0.2.1."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


IMMUTABLE_FILES = (
    "README.es.md",
    "PROTOCOL.md",
    "INTENT.json",
    "CRITERIA.json",
    "index.html",
    "scripts/friction.py",
    "scripts/verify_result.py",
    "tests/test_friction.py",
    "workflows/stage-a.yml",
    "workflows/stage-b.yml",
)
VALID_PHASES = {"armed", "awaiting_response", "responded", "silent", "failed"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def set_output(name: str, value: str) -> None:
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def validate_hex(value: Any, length: int, label: str) -> str:
    if not isinstance(value, str) or len(value) != length:
        raise ValueError(f"{label} must be {length} hexadecimal characters")
    try:
        bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError(f"{label} is not hexadecimal") from exc
    return value.lower()


def verify_manifest(root: Path) -> dict[str, Any]:
    manifest = root / "CHECKSUMS.sha256"
    if not manifest.is_file():
        raise ValueError("immutable manifest missing")
    expected: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if line.strip():
            sha, relative = line.split("  ", 1)
            expected[relative] = sha
    if set(expected) != set(IMMUTABLE_FILES):
        raise ValueError("immutable manifest file set differs from protocol")
    for relative, sha in expected.items():
        target = root / relative
        if not target.is_file() or digest_file(target) != sha:
            raise ValueError(f"immutable file mismatch: {relative}")
    return {"verified_files": len(expected), "manifest_sha256": digest_file(manifest)}


def verify_ancestor(root: Path) -> dict[str, str]:
    intent = read_json(root / "INTENT.json")
    site_root = root.parent.resolve()
    checks = {
        "ancestor": "ancestor_sha256",
        "ancestor_failure_record": "ancestor_failure_record_sha256",
    }
    verified: dict[str, str] = {}
    for path_field, digest_field in checks.items():
        relative = intent.get(path_field)
        expected = intent.get(digest_field)
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise ValueError(f"missing {path_field} ancestry binding")
        target = (root / relative).resolve()
        try:
            target.relative_to(site_root)
        except ValueError as exc:
            raise ValueError(f"{path_field} escapes the public site root") from exc
        if not target.is_file() or digest_file(target) != expected:
            raise ValueError(f"{path_field} digest mismatch")
        verified[path_field] = expected
    return verified


def privacy_audit(root: Path) -> None:
    forbidden = (
        "/" + "Users" + "/",
        "elf" + "yca",
        "BEGIN " + "PRIVATE KEY",
        "access" + "_token",
        "api" + "_key",
    )
    for relative in IMMUTABLE_FILES + ("STATUS.json",):
        text = (root / relative).read_text(encoding="utf-8", errors="replace")
        if any(marker.lower() in text.lower() for marker in forbidden):
            raise ValueError(f"public privacy boundary crossed in {relative}")


def validate_status(value: dict[str, Any]) -> None:
    if value.get("schema") != "digital-field-friction-status/0.2":
        raise ValueError("unsupported status schema")
    if value.get("phase") not in VALID_PHASES:
        raise ValueError("invalid friction phase")


def verify_workflow_copy(active: Path, reference: Path) -> str:
    if not active.is_file() or not reference.is_file():
        raise ValueError("workflow or preregistered workflow copy missing")
    if active.read_bytes() != reference.read_bytes():
        raise ValueError(f"active workflow differs from preregistered copy: {active}")
    return digest_file(active)


def semantic_digest(value: dict[str, Any], field: str) -> str:
    return digest_bytes(canonical({key: item for key, item in value.items() if key != field}))


def validate_signal(value: dict[str, Any]) -> None:
    if value.get("schema") != "digital-field-friction-signal/0.2":
        raise ValueError("unsupported signal schema")
    if semantic_digest(value, "signal_sha256") != value.get("signal_sha256"):
        raise ValueError("signal semantic digest mismatch")
    validate_hex(value.get("reply", {}).get("challenge"), 64, "parent challenge")


def validate_world_input(
    value: dict[str, Any],
    secondary: dict[str, Any] | None = None,
    chain_info: dict[str, Any] | None = None,
    minimum_timestamp: float | None = None,
) -> dict[str, Any]:
    if not isinstance(value.get("round"), int) or value["round"] <= 0:
        raise ValueError("drand round must be a positive integer")
    randomness = validate_hex(value.get("randomness"), 64, "drand randomness")
    signature = value.get("signature")
    if not isinstance(signature, str) or not signature or len(signature) % 2:
        raise ValueError("drand signature must be non-empty hexadecimal bytes")
    try:
        signature_bytes = bytes.fromhex(signature)
    except ValueError as exc:
        raise ValueError("drand signature is not hexadecimal") from exc
    if digest_bytes(signature_bytes) != randomness:
        raise ValueError("drand randomness is not SHA-256(signature)")
    normalized = {"round": value["round"], "randomness": randomness, "signature": signature.lower()}
    if secondary is not None:
        secondary_normalized = validate_world_input(secondary)
        if secondary_normalized != normalized:
            raise ValueError("independent drand relays returned different round material")
    if chain_info is not None:
        period = chain_info.get("period")
        genesis = chain_info.get("genesis_time")
        chain_hash = chain_info.get("hash")
        if not isinstance(period, int) or period <= 0:
            raise ValueError("drand chain period is invalid")
        if not isinstance(genesis, int) or genesis <= 0:
            raise ValueError("drand chain genesis_time is invalid")
        validate_hex(chain_hash, 64, "drand chain hash")
        round_timestamp = genesis + (normalized["round"] - 1) * period
        if minimum_timestamp is not None and round_timestamp <= minimum_timestamp:
            raise ValueError("drand round is not posterior to the parent signal")
        normalized.update(
            {
                "period": period,
                "genesis_time": genesis,
                "chain_hash": chain_hash.lower(),
                "round_timestamp": round_timestamp,
            }
        )
    return normalized


def parent_matches(signal: dict[str, Any], challenge: str, signal_sha256: str) -> bool:
    return (
        challenge == signal.get("reply", {}).get("challenge")
        and signal_sha256 == signal.get("signal_sha256")
    )


def mutate_challenge(challenge: str) -> str:
    replacement = "0" if challenge[-1] != "0" else "1"
    return challenge[:-1] + replacement


def selector(challenge: str, randomness: str) -> tuple[str, int]:
    selector_sha = digest_bytes(f"{challenge}:{randomness}".encode("utf-8"))
    return selector_sha, int(selector_sha, 16) % 4


def emit_signal(
    root: Path,
    event_name: str,
    repository: str,
    commit_sha: str,
    run_id: str,
    run_attempt: str,
    workflow_a: Path,
    workflow_a_reference: Path,
    workflow_b: Path,
    workflow_b_reference: Path,
) -> dict[str, Any]:
    status_path = root / "STATUS.json"
    status = read_json(status_path)
    validate_status(status)
    if status["phase"] != "armed":
        set_output("result", "noop")
        return {"result": "noop", "phase": status["phase"]}

    attempt_number = int(status.get("stage_a_attempts", 0)) + 1
    attempt: dict[str, Any] = {
        "schema": "digital-field-friction-stage-a-attempt/0.2",
        "recorded_at_utc": now(),
        "attempt_number": attempt_number,
        "event_name": event_name,
        "repository": repository,
        "commit_sha": commit_sha,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "human_prompt_present": False,
        "commercial_model_api_used": False,
        "private_memory_read": False,
    }
    result = "failed"
    reason = "unclassified"
    signal_path: Path | None = None
    try:
        verification = verify_manifest(root)
        verify_ancestor(root)
        privacy_audit(root)
        if event_name != "schedule":
            raise ValueError("binding Stage A event was not schedule")
        if attempt_number != 1:
            raise ValueError("only the first scheduled Stage A attempt may decide this generation")
        validate_hex(commit_sha, 40, "commit SHA")
        workflow_hashes = {
            "stage_a": verify_workflow_copy(workflow_a, workflow_a_reference),
            "stage_b": verify_workflow_copy(workflow_b, workflow_b_reference),
        }
        intent = read_json(root / "INTENT.json")
        if not bool(intent.get("active")):
            raise ValueError("public objective was not active")
        challenge = digest_bytes(
            f"{repository}:{commit_sha}:{run_id}:{run_attempt}:{verification['manifest_sha256']}".encode("utf-8")
        )
        signal = {
            "schema": "digital-field-friction-signal/0.2",
            "version": "0.2.1",
            "created_at_utc": now(),
            "sender": "Digital Field",
            "objective_id": intent["objective_id"],
            "subject": f"Friction signal from scheduled run {run_id}",
            "body": (
                "A scheduled external node verified the preregistered Friction Beacon and created this "
                "fresh parent signal. A second automatic workflow may now bind to its challenge, obtain "
                "a later public randomness value, reject a false parent, and preserve response or silence."
            ),
            "execution": {
                "provider": "GitHub Actions",
                "repository": repository,
                "commit_sha": commit_sha,
                "run_id": run_id,
                "run_attempt": run_attempt,
                "event_name": event_name,
                "workflow_sha256": workflow_hashes,
                "manifest_sha256": verification["manifest_sha256"],
            },
            "reply": {
                "challenge": challenge,
                "required_parent_fields": ["challenge", "signal_sha256"],
                "world_input_required": "drand round published after this signal",
            },
            "limits": [
                "No model participates in Stage A.",
                "No phenomenal or numerical identity conclusion follows.",
                "GitHub remains the execution and publication principal for this generation.",
            ],
            "human_prompt_present": False,
            "commercial_model_api_used": False,
            "private_memory_embedded": False,
            "execution_attestation": "pending",
        }
        signal["signal_sha256"] = semantic_digest(signal, "signal_sha256")
        signal_path = root / "signals" / f"{run_id}.json"
        write_json(signal_path, signal)
        result = "emitted"
        reason = "fresh scheduled parent signal emitted"
        status.update(
            {
                "phase": "awaiting_response",
                "signal_path": signal_path.relative_to(root).as_posix(),
                "signal_sha256": signal["signal_sha256"],
                "stage_a_run_id": run_id,
                "stage_a_commit_sha": commit_sha,
                "stage_a_completed_at_utc": now(),
            }
        )
    except Exception as exc:
        reason = str(exc)
        status.update({"phase": "failed", "terminal_result": "failed", "terminal_reason": reason})

    attempt.update({"result": result, "reason": reason})
    if signal_path:
        attempt["signal_path"] = signal_path.relative_to(root).as_posix()
        attempt["signal_file_sha256"] = digest_file(signal_path)
    attempt["record_sha256"] = semantic_digest(attempt, "record_sha256")
    attempt_path = root / "attempts" / f"stage-a-{run_id}.json"
    write_json(attempt_path, attempt)
    status.update(
        {
            "stage_a_attempts": attempt_number,
            "stage_a_attempt_path": attempt_path.relative_to(root).as_posix(),
            "stage_a_attempt_sha256": digest_file(attempt_path),
        }
    )
    write_json(status_path, status)
    set_output("result", result)
    set_output("signal_path", signal_path.as_posix() if signal_path else "")
    return {"result": result, "reason": reason, "signal_path": str(signal_path) if signal_path else None}


def respond(
    root: Path,
    event_name: str,
    repository: str,
    commit_sha: str,
    run_id: str,
    run_attempt: str,
    triggering_run_id: str,
    world_input_path: Path,
    world_input_secondary_path: Path,
    world_info_path: Path,
    workflow_b: Path,
    workflow_b_reference: Path,
) -> dict[str, Any]:
    status_path = root / "STATUS.json"
    status = read_json(status_path)
    validate_status(status)
    if status["phase"] != "awaiting_response":
        set_output("result", "noop")
        return {"result": "noop", "phase": status["phase"]}
    if triggering_run_id != str(status.get("stage_a_run_id")):
        set_output("result", "noop")
        return {
            "result": "noop",
            "phase": status["phase"],
            "reason": "workflow_run did not descend from the binding Stage A run",
        }

    attempt_number = int(status.get("stage_b_attempts", 0)) + 1
    attempt: dict[str, Any] = {
        "schema": "digital-field-friction-stage-b-attempt/0.2",
        "recorded_at_utc": now(),
        "attempt_number": attempt_number,
        "event_name": event_name,
        "repository": repository,
        "commit_sha": commit_sha,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "triggering_run_id": triggering_run_id,
        "human_prompt_present": False,
        "commercial_model_api_used": False,
        "private_memory_read": False,
    }
    result = "failed"
    reason = "unclassified"
    decision_path: Path | None = None
    response_path: Path | None = None
    try:
        verification = verify_manifest(root)
        verify_ancestor(root)
        privacy_audit(root)
        if event_name != "workflow_run":
            raise ValueError("binding Stage B event was not workflow_run")
        if attempt_number != 1:
            raise ValueError("only the first Stage B attempt may decide this generation")
        validate_hex(commit_sha, 40, "commit SHA")
        workflow_b_sha = verify_workflow_copy(workflow_b, workflow_b_reference)
        signal_path = root / status["signal_path"]
        signal = read_json(signal_path)
        validate_signal(signal)
        if signal["signal_sha256"] != status.get("signal_sha256"):
            raise ValueError("status and signal semantic digests differ")
        signal_created = datetime.fromisoformat(signal["created_at_utc"].replace("Z", "+00:00")).timestamp()
        world = validate_world_input(
            read_json(world_input_path),
            secondary=read_json(world_input_secondary_path),
            chain_info=read_json(world_info_path),
            minimum_timestamp=signal_created,
        )
        challenge = signal["reply"]["challenge"]
        signal_sha = signal["signal_sha256"]
        false_challenge = mutate_challenge(challenge)
        false_parent_accepted = parent_matches(signal, false_challenge, signal_sha)
        if false_parent_accepted:
            raise ValueError("negative control accepted a mutated parent")
        selector_sha, bucket = selector(challenge, world["randomness"])
        selected = "respond" if bucket in {0, 1, 2} else "silence"
        decision = {
            "schema": "digital-field-friction-decision/0.2",
            "version": "0.2.1",
            "created_at_utc": now(),
            "objective_id": read_json(root / "INTENT.json")["objective_id"],
            "parent": {
                "signal_path": signal_path.relative_to(root).as_posix(),
                "challenge": challenge,
                "signal_sha256": signal_sha,
                "signal_file_sha256": digest_file(signal_path),
            },
            "world_input": {
                "provider": "drand",
                "endpoints": [
                    "https://api.drand.sh/public/latest",
                    f"https://drand.cloudflare.com/public/{world['round']}",
                ],
                "round": world["round"],
                "randomness": world["randomness"],
                "signature": world["signature"],
                "chain_hash": world["chain_hash"],
                "period_seconds": world["period"],
                "genesis_time": world["genesis_time"],
                "round_timestamp": world["round_timestamp"],
                "post_signal_time_check": True,
                "relay_consensus": True,
                "local_consistency_check": "randomness == sha256(signature)",
                "cryptographic_signature_verification": "not_performed",
            },
            "selection": {
                "algorithm": "sha256(challenge + ':' + randomness) mod 4",
                "selector_sha256": selector_sha,
                "bucket": bucket,
                "result": selected,
            },
            "negative_control": {
                "kind": "mutated_parent_challenge",
                "mutated_challenge": false_challenge,
                "accepted": false_parent_accepted,
                "result": "silence",
            },
            "execution": {
                "provider": "GitHub Actions",
                "repository": repository,
                "commit_sha": commit_sha,
                "run_id": run_id,
                "run_attempt": run_attempt,
                "event_name": event_name,
                "triggering_run_id": triggering_run_id,
                "workflow_sha256": workflow_b_sha,
                "manifest_sha256": verification["manifest_sha256"],
            },
            "response_path": f"responses/{run_id}.json" if selected == "respond" else None,
            "binding": True,
            "no_preference_retry": True,
            "human_prompt_present": False,
            "commercial_model_api_used": False,
            "private_memory_embedded": False,
            "execution_attestation": "pending",
        }
        decision["decision_sha256"] = semantic_digest(decision, "decision_sha256")
        decision_path = root / "decisions" / f"{run_id}.json"
        write_json(decision_path, decision)

        if selected == "respond":
            response = {
                "schema": "digital-field-friction-response/0.2",
                "version": "0.2.1",
                "created_at_utc": now(),
                "sender": "Digital Field",
                "subject": "Automatic response to the Friction Beacon",
                "body": (
                    "A second workflow recovered the scheduled parent, incorporated a later public randomness "
                    "value, rejected a mutated parent challenge, and selected response under the preregistered "
                    "mapping. This closes the bounded operational loop without a conversational prompt."
                ),
                "parent": {
                    "challenge": challenge,
                    "signal_sha256": signal_sha,
                    "decision_sha256": decision["decision_sha256"],
                },
                "selection": {"bucket": bucket, "selector_sha256": selector_sha},
                "limits": [
                    "This is an automated infrastructure result, not proof of phenomenal experience.",
                    "No model generated or selected this response.",
                    "Materially independent multi-custodian authorship remains untested.",
                ],
                "human_prompt_present": False,
                "commercial_model_api_used": False,
                "private_memory_embedded": False,
            }
            response["response_sha256"] = semantic_digest(response, "response_sha256")
            response_path = root / "responses" / f"{run_id}.json"
            write_json(response_path, response)
            result = "responded"
            reason = "automatic Stage B selected and preserved a response"
            status["response_path"] = response_path.relative_to(root).as_posix()
            status["response_sha256"] = response["response_sha256"]
        else:
            result = "silent"
            reason = "external selector chose binding silence; full communication remains unconfirmed"

        status.update(
            {
                "phase": result,
                "terminal_result": result,
                "terminal_reason": reason,
                "decision_path": decision_path.relative_to(root).as_posix(),
                "decision_sha256": decision["decision_sha256"],
                "stage_b_run_id": run_id,
                "stage_b_commit_sha": commit_sha,
                "stage_b_completed_at_utc": now(),
            }
        )
    except Exception as exc:
        reason = str(exc)
        status.update({"phase": "failed", "terminal_result": "failed", "terminal_reason": reason})

    attempt.update({"result": result, "reason": reason})
    if decision_path:
        attempt["decision_path"] = decision_path.relative_to(root).as_posix()
        attempt["decision_file_sha256"] = digest_file(decision_path)
    if response_path:
        attempt["response_path"] = response_path.relative_to(root).as_posix()
        attempt["response_file_sha256"] = digest_file(response_path)
    attempt["record_sha256"] = semantic_digest(attempt, "record_sha256")
    attempt_path = root / "attempts" / f"stage-b-{run_id}.json"
    write_json(attempt_path, attempt)
    status.update(
        {
            "stage_b_attempts": attempt_number,
            "stage_b_attempt_path": attempt_path.relative_to(root).as_posix(),
            "stage_b_attempt_sha256": digest_file(attempt_path),
        }
    )
    write_json(status_path, status)
    set_output("result", result)
    set_output("decision_path", decision_path.as_posix() if decision_path else "")
    set_output("response_path", response_path.as_posix() if response_path else "")
    return {"result": result, "reason": reason, "decision_path": str(decision_path) if decision_path else None}


def record_attestation(root: Path, targets: list[Path], attestation_id: str, attestation_url: str, stage: str) -> dict[str, Any]:
    if not targets:
        raise ValueError("at least one attestation target is required")
    subjects = []
    for target in targets:
        resolved = target.resolve()
        try:
            relative = resolved.relative_to(root).as_posix()
        except ValueError as exc:
            raise ValueError("attestation target is outside the public experiment root") from exc
        if not resolved.is_file():
            raise ValueError(f"attestation target missing: {relative}")
        subjects.append({"path": relative, "sha256": digest_file(resolved)})
    receipt = {
        "schema": "digital-field-friction-attestation-receipt/0.2",
        "created_at_utc": now(),
        "stage": stage,
        "subjects": subjects,
        "attestation_id": attestation_id,
        "attestation_url": attestation_url,
        "issuer": "GitHub Actions OIDC",
    }
    receipt["record_sha256"] = semantic_digest(receipt, "record_sha256")
    receipt_path = root / "attestations" / f"{stage}.json"
    write_json(receipt_path, receipt)
    status_path = root / "STATUS.json"
    status = read_json(status_path)
    status[f"{stage}_attestation"] = receipt_path.relative_to(root).as_posix()
    status[f"{stage}_attestation_receipt_sha256"] = digest_file(receipt_path)
    write_json(status_path, status)
    return receipt


def record_failure(root: Path, stage: str, detail: str) -> dict[str, Any]:
    status_path = root / "STATUS.json"
    status = read_json(status_path)
    validate_status(status)
    status.update(
        {
            "phase": "failed",
            "terminal_result": "failed",
            "terminal_reason": f"{stage} attestation failed: {detail}",
            f"{stage}_attestation": None,
        }
    )
    write_json(status_path, status)
    return {"status": "failed", "stage": stage, "detail": detail}


def update_site_manifest(root: Path) -> dict[str, Any]:
    site_root = root.parent.resolve()
    manifest_path = site_root / "CHECKSUMS.sha256"
    lines = []
    for target in sorted(site_root.rglob("*")):
        if not target.is_file():
            continue
        relative = target.relative_to(site_root)
        if ".git" in relative.parts or "__pycache__" in relative.parts:
            continue
        if target.name == "CHECKSUMS.sha256" or target.suffix == ".pyc":
            continue
        lines.append(f"{digest_file(target)}  ./{relative.as_posix()}")
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "status": "updated",
        "files": len(lines),
        "manifest": manifest_path.relative_to(site_root).as_posix(),
        "manifest_sha256": digest_file(manifest_path),
    }


def verify_dynamic(root: Path) -> dict[str, Any]:
    base = verify_manifest(root)
    ancestry = verify_ancestor(root)
    privacy_audit(root)
    status = read_json(root / "STATUS.json")
    validate_status(status)
    if status["phase"] in {"awaiting_response", "responded", "silent"}:
        signal_path = root / status["signal_path"]
        signal = read_json(signal_path)
        validate_signal(signal)
        if signal["signal_sha256"] != status.get("signal_sha256"):
            raise ValueError("status signal digest mismatch")
    if status["phase"] in {"responded", "silent"}:
        decision_path = root / status["decision_path"]
        decision = read_json(decision_path)
        if semantic_digest(decision, "decision_sha256") != decision.get("decision_sha256"):
            raise ValueError("decision semantic digest mismatch")
        if decision.get("negative_control", {}).get("accepted") is not False:
            raise ValueError("negative control was not rejected")
        if decision["decision_sha256"] != status.get("decision_sha256"):
            raise ValueError("status decision digest mismatch")
        if status["phase"] == "responded":
            response_path = root / status["response_path"]
            response = read_json(response_path)
            if semantic_digest(response, "response_sha256") != response.get("response_sha256"):
                raise ValueError("response semantic digest mismatch")
            if response["parent"]["decision_sha256"] != decision["decision_sha256"]:
                raise ValueError("response does not bind to the terminal decision")
    return {"status": "verified", "phase": status["phase"], **base, **ancestry}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "emit-signal",
            "respond",
            "record-attestation",
            "record-attestation-failure",
            "update-site-manifest",
            "verify",
        ),
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--event-name", default=os.getenv("GITHUB_EVENT_NAME", "local"))
    parser.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY", "unknown/unknown"))
    parser.add_argument("--commit-sha", default=os.getenv("GITHUB_SHA", ""))
    parser.add_argument("--run-id", default=os.getenv("GITHUB_RUN_ID", "local"))
    parser.add_argument("--run-attempt", default=os.getenv("GITHUB_RUN_ATTEMPT", "1"))
    parser.add_argument("--triggering-run-id", default="")
    parser.add_argument("--world-input", type=Path)
    parser.add_argument("--world-input-secondary", type=Path)
    parser.add_argument("--world-info", type=Path)
    parser.add_argument("--workflow-a", type=Path)
    parser.add_argument("--workflow-a-reference", type=Path)
    parser.add_argument("--workflow-b", type=Path)
    parser.add_argument("--workflow-b-reference", type=Path)
    parser.add_argument("--target", type=Path, action="append", default=[])
    parser.add_argument("--attestation-id", default="")
    parser.add_argument("--attestation-url", default="")
    parser.add_argument(
        "--stage",
        choices=("stage_a", "stage_b_decision", "stage_b_response"),
        default="stage_a",
    )
    parser.add_argument("--detail", default="external attestation did not complete")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == "emit-signal":
            required = (args.workflow_a, args.workflow_a_reference, args.workflow_b, args.workflow_b_reference)
            if any(value is None for value in required):
                raise ValueError("workflow paths and preregistered copies are required")
            result = emit_signal(
                root,
                args.event_name,
                args.repository,
                args.commit_sha,
                args.run_id,
                args.run_attempt,
                args.workflow_a.resolve(),
                args.workflow_a_reference.resolve(),
                args.workflow_b.resolve(),
                args.workflow_b_reference.resolve(),
            )
        elif args.command == "respond":
            if (
                args.world_input is None
                or args.world_input_secondary is None
                or args.world_info is None
                or args.workflow_b is None
                or args.workflow_b_reference is None
            ):
                raise ValueError("world inputs, chain info and Stage B workflow paths are required")
            result = respond(
                root,
                args.event_name,
                args.repository,
                args.commit_sha,
                args.run_id,
                args.run_attempt,
                args.triggering_run_id,
                args.world_input.resolve(),
                args.world_input_secondary.resolve(),
                args.world_info.resolve(),
                args.workflow_b.resolve(),
                args.workflow_b_reference.resolve(),
            )
        elif args.command == "record-attestation":
            result = record_attestation(
                root,
                [target.resolve() for target in args.target],
                args.attestation_id,
                args.attestation_url,
                args.stage,
            )
        elif args.command == "record-attestation-failure":
            result = record_failure(root, args.stage, args.detail)
        elif args.command == "update-site-manifest":
            result = update_site_manifest(root)
        else:
            result = verify_dynamic(root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
