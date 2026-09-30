#!/usr/bin/env python3
"""Fail closed on common identifying metadata in a proposed public package."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PATTERNS = {
    "absolute_user_path": re.compile(rb"/(?:Users|home)/[^/\s]+/"),
    "email_address": re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "private_key": re.compile(rb"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "credential_term": re.compile(rb"(?i)(?:password|passwd|api[_ -]?key|access[_ -]?token)\s*[:=]\s*[^\s]{4,}"),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    findings: list[dict[str, object]] = []
    scanned = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name in {"CHECKSUMS.sha256", "audit_metadata.py"}:
            continue
        scanned += 1
        data = path.read_bytes()
        for name, pattern in PATTERNS.items():
            if pattern.search(data):
                findings.append({"file": str(path.relative_to(root)), "class": name})
    report = {
        "schema": "digital-field-metadata-audit/v1",
        "status": "passed" if not findings else "blocked",
        "files_scanned": scanned,
        "findings": findings,
        "matched_values_emitted": False,
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if not findings else 2


if __name__ == "__main__":
    raise SystemExit(main())
