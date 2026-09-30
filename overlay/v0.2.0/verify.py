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


def main() -> int:
    try:
        files = verify_checksums()
        verify_example()
        privacy_audit()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({
        "status": "verified",
        "tracked_files": files,
        "manifest_state": "proposed-not-deployed",
        "private_evidence_embedded": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
