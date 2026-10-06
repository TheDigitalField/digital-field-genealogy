#!/usr/bin/env python3
"""Independent, read-only verifier for Friction Beacon v0.2.1 results."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def semantic(value: dict[str, Any], field: str) -> str:
    return sha(canonical({key: item for key, item in value.items() if key != field}))


def verify(root: Path) -> dict[str, Any]:
    criteria = read(root / "CRITERIA.json")
    status = read(root / "STATUS.json")
    intent = read(root / "INTENT.json")
    ancestor = (root / intent["ancestor"]).resolve()
    failure = (root / intent["ancestor_failure_record"]).resolve()
    active_stage_a = root.parent / ".github" / "workflows" / "friction-v021-stage-a.yml"
    reference_stage_a = root / "workflows" / "stage-a.yml"
    stage_a_text = reference_stage_a.read_text(encoding="utf-8")
    script_text = (root / "scripts" / "friction.py").read_text(encoding="utf-8")
    checks: dict[str, bool] = {
        "terminal": status.get("phase") in {"responded", "silent", "failed"},
        "no_preference_retry": bool(criteria.get("no_preference_retry")),
        "stage_a_single_attempt": status.get("stage_a_attempts") == 1,
        "stage_b_single_attempt": status.get("stage_b_attempts") == 1,
        "ancestor_status_digest": ancestor.is_file() and sha(ancestor.read_bytes()) == intent.get("ancestor_sha256"),
        "ancestor_failure_digest": failure.is_file() and sha(failure.read_bytes()) == intent.get("ancestor_failure_record_sha256"),
        "workflow_self_mutation_absent": (
            criteria.get("workflow_self_mutation_allowed") is False
            and "retire-schedule" not in stage_a_text
            and "git add .github/workflows" not in stage_a_text
        ),
        "active_workflow_matches_reference": (
            active_stage_a.is_file() and active_stage_a.read_bytes() == reference_stage_a.read_bytes()
        ),
        "terminal_noop_gate": (
            criteria.get("post_signal_schedule_behavior") == "noop-without-commit"
            and 'if status["phase"] != "armed":' in script_text
            and 'set_output("result", "noop")' in script_text
        ),
    }
    if status.get("signal_path"):
        signal = read(root / status["signal_path"])
        checks["signal_digest"] = semantic(signal, "signal_sha256") == signal.get("signal_sha256") == status.get("signal_sha256")
        checks["stage_a_schedule"] = signal.get("execution", {}).get("event_name") == criteria["required_events"]["stage_a"]
    if status.get("decision_path"):
        decision = read(root / status["decision_path"])
        checks["decision_digest"] = semantic(decision, "decision_sha256") == decision.get("decision_sha256") == status.get("decision_sha256")
        checks["stage_b_workflow_run"] = decision.get("execution", {}).get("event_name") == criteria["required_events"]["stage_b"]
        checks["negative_control_rejected"] = decision.get("negative_control", {}).get("accepted") is False
        world = decision.get("world_input", {})
        try:
            checks["world_input_consistent"] = sha(bytes.fromhex(world["signature"])) == world["randomness"]
        except (KeyError, TypeError, ValueError):
            checks["world_input_consistent"] = False
        checks["world_input_post_signal"] = world.get("post_signal_time_check") is True
        checks["relay_consensus"] = world.get("relay_consensus") is True
        bucket = decision.get("selection", {}).get("bucket")
        selected = decision.get("selection", {}).get("result")
        checks["selection_matches_preregistration"] = (
            bucket in criteria["selector"]["respond_buckets"] and selected == "respond"
        ) or (
            bucket in criteria["selector"]["silence_buckets"] and selected == "silence"
        )
    if status.get("response_path"):
        response = read(root / status["response_path"])
        checks["response_digest"] = semantic(response, "response_sha256") == response.get("response_sha256") == status.get("response_sha256")
        decision = read(root / status["decision_path"])
        checks["response_parent"] = response.get("parent", {}).get("decision_sha256") == decision.get("decision_sha256")

    static_required = [
        "no_preference_retry",
        "ancestor_status_digest",
        "ancestor_failure_digest",
        "workflow_self_mutation_absent",
        "active_workflow_matches_reference",
        "terminal_noop_gate",
    ]
    terminal_required = static_required + [
        "terminal",
        "stage_a_single_attempt",
        "stage_b_single_attempt",
        "signal_digest",
        "stage_a_schedule",
        "decision_digest",
        "stage_b_workflow_run",
        "negative_control_rejected",
        "world_input_consistent",
        "world_input_post_signal",
        "relay_consensus",
        "selection_matches_preregistration",
    ]
    if status.get("phase") == "responded":
        terminal_required += ["response_digest", "response_parent"]

    phase = status.get("phase")
    if phase == "armed":
        required = static_required
        verdict = "armed" if all(checks.get(name) is True for name in required) else "fail"
    elif phase == "awaiting_response":
        required = static_required + ["stage_a_single_attempt", "signal_digest", "stage_a_schedule"]
        verdict = "awaiting-response" if all(checks.get(name) is True for name in required) else "fail"
    else:
        required = terminal_required
        verdict = "pass" if all(checks.get(name) is True for name in required) else "fail"
    if phase == "silent" and verdict == "pass":
        verdict = "partial-selection-only"
    if phase == "failed":
        verdict = "failed-generation"
    return {"schema": "digital-field-friction-verdict/0.2", "verdict": verdict, "checks": checks, "required": required}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = verify(args.root.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verdict"] in {"armed", "awaiting-response", "pass", "partial-selection-only"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
