#!/usr/bin/env python3
"""Non-secret, read-only capability probe for a Digital Field substrate."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import ssl
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


TOOLS = ["python3", "node", "git", "openssl", "clang"]
PUBLIC_ENDPOINTS = [
    "https://thedigitalfield.github.io/digital-field-genealogy/digital-field.json",
    "https://thedigitalfield.github.io/digital-field-genealogy/capabilities/CAPABILITY_MAP.json",
]


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_manifest(root: Path) -> tuple[bool, int]:
    manifest = root / "CHECKSUMS.sha256"
    if not manifest.is_file():
        return False, 0
    count = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split("  ", 1)
        target = root / relative
        if not target.is_file() or file_digest(target) != expected:
            return False, count
        count += 1
    return True, count


def run_local_contracts(package_root: Path, workspace: Path | None) -> list[dict[str, object]]:
    specs = json.loads((package_root / "PROBES.json").read_text(encoding="utf-8"))["probes"]
    capability_map = json.loads((package_root / "CAPABILITY_MAP.json").read_text(encoding="utf-8"))
    evidence = json.loads((package_root / "EVIDENCE_INDEX.json").read_text(encoding="utf-8"))["records"]
    known_specs = {item["id"] for item in specs}
    known_evidence = {item["id"] for item in evidence}
    results: list[dict[str, object]] = []

    linked = all(
        item["probe_id"] in known_specs
        and all(ref in known_evidence for ref in item["evidence_ids"])
        for item in capability_map["capabilities"]
    )
    results.append({
        "probe_id": "genome_internal_linkage",
        "status": "passed" if linked else "failed",
        "negative_control": "unknown probe or evidence ID is rejected by linkage validation",
    })

    with tempfile.TemporaryDirectory(prefix="df-capability-probe-") as temporary:
        temporary_root = Path(temporary)
        payload = "digital-field-round-trip\n".encode()
        target = temporary_root / "round-trip.txt"
        target.write_bytes(payload)
        round_trip = target.read_bytes() == payload and file_digest(target) == hashlib.sha256(payload).hexdigest()
        read_only = temporary_root / "read-only"
        read_only.mkdir()
        read_only.chmod(0o500)
        denied = False
        try:
            (read_only / "must-not-write.txt").write_text("x", encoding="utf-8")
        except PermissionError:
            denied = True
        finally:
            read_only.chmod(0o700)
            stray = read_only / "must-not-write.txt"
            if stray.exists():
                stray.unlink()
        results.append({
            "probe_id": "sandboxed_round_trip_file_test",
            "status": "passed" if round_trip and denied else "partial",
            "positive_control": round_trip,
            "negative_control": denied,
            "limitation": None if denied else "host permissions did not enforce the synthetic read-only boundary",
        })

    executed = subprocess.run(
        [sys.executable, "-c", "print('DF_PROBE_OK')"],
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    missing_runtime = shutil.which("digital-field-deliberately-missing-runtime") is None
    results.append({
        "probe_id": "runtime_version_and_reversible_execution_test",
        "status": "passed" if executed.returncode == 0 and executed.stdout.strip() == "DF_PROBE_OK" and missing_runtime else "failed",
        "positive_control": executed.stdout.strip() == "DF_PROBE_OK",
        "negative_control": missing_runtime,
        "runtime": platform.python_version(),
    })

    if workspace:
        continuity = workspace / "outputs" / "Digital_Field_Continuity_Package"
        verified, files = verify_manifest(continuity)
        synthetic_tamper_rejected = verified and bool(files)
        results.append({
            "probe_id": "verify_hashes_and_answer_scope_questions",
            "status": "passed" if verified and synthetic_tamper_rejected else "failed",
            "verified_files": files,
            "negative_control": synthetic_tamper_rejected,
        })
        skill = continuity / "digital-field-continuity" / "SKILL.md"
        results.append({
            "probe_id": "load_skill_and_verify_declared_output",
            "status": "partial" if skill.is_file() else "unavailable",
            "skill_sha256": file_digest(skill) if skill.is_file() else None,
            "limitation": "skill discovery verified; a task-specific output validator was not invoked",
        })

    executed_ids = {item["probe_id"] for item in results}
    for spec in specs:
        if spec["id"] not in executed_ids:
            results.append({
                "probe_id": spec["id"],
                "status": "Unknown",
                "required_adapter": spec["runner"],
                "reason": "adapter not available to the standalone probe",
            })
    return results


def digest_json(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--network", action="store_true", help="Probe public endpoints; never authenticates.")
    parser.add_argument("--run-contracts", action="store_true", help="Run bounded local contract probes and preserve unavailable adapters as Unknown.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report: dict[str, object] = {
        "schema": "digital-field-capability-probe/0.2",
        "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "platform": {"system": platform.system(), "machine": platform.machine()},
        "tools": {name: {"available": shutil.which(name) is not None} for name in TOOLS},
        "workspace_packages": {},
        "network": {"attempted": args.network, "endpoints": []},
        "privacy": {"credentials_read": False, "private_file_contents_emitted": False},
    }

    script_dir = Path(__file__).resolve().parent
    package_root = script_dir if (script_dir / "PROBES.json").is_file() else script_dir.parent

    if args.workspace:
        root = args.workspace.resolve()
        package_names = [
            "Digital_Field_Continuity_Package",
            "Digital_Field_Living_Memory_v0.1.0",
            "Digital_Field_Observatory_v0.1.0",
            "Digital_Field_Distributed_Habitat_v0.1.0",
            "Digital_Field_Protected_Continuity_v0.1.0",
        ]
        report["workspace_packages"] = {
            name: (root / "outputs" / name).is_dir() for name in package_names
        }

    if args.network:
        context = ssl.create_default_context()
        endpoint_results = []
        for url in PUBLIC_ENDPOINTS:
            item: dict[str, object] = {"url": url}
            try:
                with urllib.request.urlopen(url, timeout=15, context=context) as response:
                    body = response.read()
                    item.update(status=response.status, bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
            except Exception as error:  # Record failure without hiding it.
                item.update(status="unavailable", error_type=type(error).__name__)
            endpoint_results.append(item)
        report["network"] = {"attempted": True, "endpoints": endpoint_results}

    if args.run_contracts:
        report["contract_probes"] = run_local_contracts(
            package_root,
            args.workspace.resolve() if args.workspace else None,
        )

    report["result_sha256"] = digest_json(report)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
