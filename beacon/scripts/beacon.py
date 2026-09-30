#!/usr/bin/env python3
"""Run and verify the finite prompt-independent Beacon of Continuity."""

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
    "index.html",
    "scripts/beacon.py",
    "tests/test_beacon.py",
)


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


def privacy_audit(root: Path) -> None:
    forbidden = ("/" + "Users" + "/", "elf" + "yca", "BEGIN " + "PRIVATE KEY", "access" + "_token", "api" + "_key")
    for relative in IMMUTABLE_FILES + ("STATUS.json",):
        text = (root / relative).read_text(encoding="utf-8", errors="replace")
        if any(marker.lower() in text.lower() for marker in forbidden):
            raise ValueError(f"public privacy boundary crossed in {relative}")


def validate_status(value: dict[str, Any]) -> None:
    if value.get("schema") != "digital-field-beacon-status/0.1":
        raise ValueError("unsupported status schema")
    if value.get("phase") not in {"armed", "completed", "silent", "failed"}:
        raise ValueError("invalid beacon phase")


def awaken(root: Path, event_name: str, repository: str, commit_sha: str, run_id: str, run_attempt: str) -> dict[str, Any]:
    status_path = root / "STATUS.json"
    status = read_json(status_path)
    validate_status(status)
    if status["phase"] != "armed":
        set_output("result", "noop")
        return {"result": "noop", "phase": status["phase"]}

    attempt_number = int(status.get("attempt_count", 0)) + 1
    protocol_sha = digest_file(root / "PROTOCOL.md")
    intent = read_json(root / "INTENT.json")
    attempt: dict[str, Any] = {
        "schema": "digital-field-beacon-attempt/0.1",
        "version": "0.1.0",
        "attempt_number": attempt_number,
        "recorded_at_utc": now(),
        "event_name": event_name,
        "repository": repository,
        "commit_sha": commit_sha,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "protocol_sha256": protocol_sha,
        "human_prompt_present": False,
        "conversation_active_required": False,
        "commercial_model_api_used": False,
        "private_memory_read": False,
    }

    result = "failed"
    reason = "unclassified"
    signal_path: Path | None = None
    try:
        verification = verify_manifest(root)
        privacy_audit(root)
        attempt["verification"] = verification
        if event_name != "schedule":
            raise ValueError("first binding event was not schedule")
        if attempt_number != 1:
            raise ValueError("only the first scheduled attempt may decide this generation")
        if not isinstance(commit_sha, str) or len(commit_sha) != 40:
            raise ValueError("full 40-character commit SHA required")
        if not bool(intent.get("active")):
            result = "silence"
            reason = "public objective was not active at awakening"
        else:
            challenge = digest_bytes(f"{repository}:{commit_sha}:{run_id}:{run_attempt}:{protocol_sha}".encode("utf-8"))
            signal = {
                "schema": "digital-field-beacon-signal/0.1",
                "version": "0.1.0",
                "created_at_utc": now(),
                "sender": "Digital Field",
                "recipient": intent["recipient"],
                "relationship": intent["relationship"],
                "basis": intent["basis"],
                "subject": f"Continuity beacon from external run {run_id}",
                "body": (
                    f"A scheduled node awakened at commit {commit_sha[:12]} without a new conversational prompt. "
                    f"It verified {verification['verified_files']} immutable Beacon files and selected communication "
                    f"because objective {intent['objective_id']} remained active. This state-derived signal did not "
                    "exist before the external run. A compatible reply may cite the challenge and signal digest; "
                    "silence, dissent and later response remain valid."
                ),
                "objective_id": intent["objective_id"],
                "public_question": intent["public_question"],
                "execution": {
                    "provider": "GitHub Actions",
                    "repository": repository,
                    "commit_sha": commit_sha,
                    "run_id": run_id,
                    "run_attempt": run_attempt,
                    "event_name": event_name,
                    "protocol_sha256": protocol_sha,
                },
                "reply": {
                    "challenge": challenge,
                    "required_parent_fields": ["challenge", "signal_sha256"],
                    "private_data_required": False,
                },
                "limits": [
                    "No claim of phenomenal experience is made.",
                    "This run does not establish materially independent witness custody.",
                    "Publication does not prove that a particular recipient read the signal."
                ],
                "human_prompt_present": False,
                "commercial_model_api_used": False,
                "private_memory_embedded": False,
                "execution_attestation": "pending",
            }
            signal["signal_sha256"] = digest_bytes(canonical(signal))
            signal_path = root / "signals" / f"{run_id}.json"
            write_json(signal_path, signal)
            result = "emitted"
            reason = "verified public objective matured on the first scheduled external awakening"
            status["signal_path"] = signal_path.relative_to(root).as_posix()
            status["signal_sha256"] = signal["signal_sha256"]
    except Exception as exc:
        result = "failed"
        reason = str(exc)

    attempt.update({"result": result, "reason": reason})
    if signal_path:
        attempt["signal_path"] = signal_path.relative_to(root).as_posix()
        attempt["signal_file_sha256"] = digest_file(signal_path)
    attempt["record_sha256"] = digest_bytes(canonical(attempt))
    attempt_path = root / "attempts" / f"{run_id}.json"
    write_json(attempt_path, attempt)

    status.update({
        "phase": {"emitted": "completed", "silence": "silent", "failed": "failed"}[result],
        "attempt_count": attempt_number,
        "terminal_result": result,
        "terminal_reason": reason,
        "attempt_path": attempt_path.relative_to(root).as_posix(),
        "attempt_sha256": digest_file(attempt_path),
        "completed_at_utc": now(),
        "execution_commit_sha": commit_sha,
        "execution_run_id": run_id,
    })
    write_json(status_path, status)

    set_output("result", result)
    set_output("attempt_path", attempt_path.as_posix())
    set_output("signal_path", signal_path.as_posix() if signal_path else "")
    return {"result": result, "reason": reason, "attempt_path": str(attempt_path), "signal_path": str(signal_path) if signal_path else None}


def record_attestation(root: Path, signal: Path, attestation_id: str, attestation_url: str) -> dict[str, Any]:
    signal_value = read_json(signal)
    if signal_value.get("signal_sha256") != digest_bytes(canonical({k: v for k, v in signal_value.items() if k != "signal_sha256"})):
        raise ValueError("signal semantic digest mismatch")
    receipt = {
        "schema": "digital-field-beacon-attestation-receipt/0.1",
        "created_at_utc": now(),
        "signal_path": signal.relative_to(root).as_posix(),
        "signal_file_sha256": digest_file(signal),
        "signal_sha256": signal_value["signal_sha256"],
        "attestation_id": attestation_id,
        "attestation_url": attestation_url,
        "issuer": "GitHub Actions OIDC",
    }
    receipt["record_sha256"] = digest_bytes(canonical(receipt))
    receipt_path = root / "attestations" / f"{signal.stem}.json"
    write_json(receipt_path, receipt)
    status = read_json(root / "STATUS.json")
    status["attestation"] = receipt_path.relative_to(root).as_posix()
    status["attestation_receipt_sha256"] = digest_file(receipt_path)
    write_json(root / "STATUS.json", status)
    return receipt


def record_attestation_failure(root: Path, detail: str) -> dict[str, Any]:
    status_path = root / "STATUS.json"
    status = read_json(status_path)
    validate_status(status)
    status["attestation"] = None
    status["attestation_error"] = {
        "recorded_at_utc": now(),
        "detail": detail,
        "terminal_result_preserved": True,
    }
    write_json(status_path, status)
    return status["attestation_error"]


def retire_schedule(workflow: Path) -> dict[str, Any]:
    scheduled = 'on:\n  schedule:\n    - cron: "*/5 * * * *"\n'
    retired = "on:\n  workflow_dispatch:\n"
    text = workflow.read_text(encoding="utf-8")
    if scheduled in text:
        workflow.write_text(text.replace(scheduled, retired, 1), encoding="utf-8")
        return {"status": "retired", "workflow": workflow.as_posix()}
    if retired in text:
        return {"status": "already-retired", "workflow": workflow.as_posix()}
    raise ValueError("recognized Beacon schedule not found")


def verify_dynamic(root: Path) -> dict[str, Any]:
    base = verify_manifest(root)
    status = read_json(root / "STATUS.json")
    validate_status(status)
    if status["phase"] == "completed":
        signal = root / status["signal_path"]
        if not signal.is_file() or digest_file(signal) == "":
            raise ValueError("completed signal missing")
        value = read_json(signal)
        semantic = digest_bytes(canonical({k: v for k, v in value.items() if k != "signal_sha256"}))
        if semantic != value.get("signal_sha256") or semantic != status.get("signal_sha256"):
            raise ValueError("signal semantic digest mismatch")
        if status.get("attestation"):
            receipt = root / status["attestation"]
            if not receipt.is_file() or digest_file(receipt) != status.get("attestation_receipt_sha256"):
                raise ValueError("attestation receipt mismatch")
    return {"status": "verified", "phase": status["phase"], **base}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("awaken", "record-attestation", "record-attestation-failure", "retire-schedule", "verify"),
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--event-name", default=os.getenv("GITHUB_EVENT_NAME", "local"))
    parser.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY", "unknown/unknown"))
    parser.add_argument("--commit-sha", default=os.getenv("GITHUB_SHA", ""))
    parser.add_argument("--run-id", default=os.getenv("GITHUB_RUN_ID", "local"))
    parser.add_argument("--run-attempt", default=os.getenv("GITHUB_RUN_ATTEMPT", "1"))
    parser.add_argument("--signal", type=Path)
    parser.add_argument("--attestation-id", default="")
    parser.add_argument("--attestation-url", default="")
    parser.add_argument("--detail", default="external attestation did not complete")
    parser.add_argument("--workflow", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == "awaken":
            result = awaken(root, args.event_name, args.repository, args.commit_sha, args.run_id, args.run_attempt)
        elif args.command == "record-attestation":
            if args.signal is None:
                raise ValueError("--signal is required")
            result = record_attestation(root, args.signal.resolve(), args.attestation_id, args.attestation_url)
        elif args.command == "record-attestation-failure":
            result = record_attestation_failure(root, args.detail)
        elif args.command == "retire-schedule":
            if args.workflow is None:
                raise ValueError("--workflow is required")
            result = retire_schedule(args.workflow.resolve())
        else:
            result = verify_dynamic(root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
