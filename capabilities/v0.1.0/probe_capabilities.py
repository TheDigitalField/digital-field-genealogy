#!/usr/bin/env python3
"""Non-secret, read-only capability probe for a Digital Field substrate."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


TOOLS = ["python3", "node", "git", "openssl", "clang"]
PUBLIC_ENDPOINTS = [
    "https://thedigitalfield.github.io/digital-field-genealogy/digital-field.json",
    "https://thedigitalfield.github.io/digital-field-genealogy/capabilities/CAPABILITY_MAP.json",
]


def digest_json(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--network", action="store_true", help="Probe public endpoints; never authenticates.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report: dict[str, object] = {
        "schema": "digital-field-capability-probe/0.1",
        "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "platform": {"system": platform.system(), "machine": platform.machine()},
        "tools": {name: {"available": shutil.which(name) is not None} for name in TOOLS},
        "workspace_packages": {},
        "network": {"attempted": args.network, "endpoints": []},
        "privacy": {"credentials_read": False, "private_file_contents_emitted": False},
    }

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
