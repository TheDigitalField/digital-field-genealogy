#!/usr/bin/env python3
"""OpenSSL-backed Ed25519 helpers for public, reproducible test fixtures."""

from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path


PRIVATE_DER_PREFIX = bytes.fromhex("302e020100300506032b657004220420")
PUBLIC_DER_PREFIX = bytes.fromhex("302a300506032b6570032100")


def _pem(label: str, data: bytes) -> bytes:
    body = base64.b64encode(data).decode()
    wrapped = "\n".join(body[i:i + 64] for i in range(0, len(body), 64))
    return f"-----BEGIN {label}-----\n{wrapped}\n-----END {label}-----\n".encode()


class FixtureKeys:
    def __init__(self, package_root: Path, scratch: Path):
        source = package_root / "fixtures" / "ed25519-test" / "TEST_KEYS.json"
        self.records = json.loads(source.read_text(encoding="utf-8"))["keys"]
        self.scratch = scratch
        scratch.mkdir(parents=True, exist_ok=True)
        for role, record in self.records.items():
            private_der = PRIVATE_DER_PREFIX + bytes.fromhex(record["seed_hex"])
            public_der = PUBLIC_DER_PREFIX + bytes.fromhex(record["public_hex"])
            (scratch / f"{role}-private.pem").write_bytes(_pem("PRIVATE KEY", private_der))
            (scratch / f"{role}-public.pem").write_bytes(_pem("PUBLIC KEY", public_der))

    def sign(self, role: str, message: bytes) -> str:
        message_path = self.scratch / "message.bin"
        signature_path = self.scratch / "signature.bin"
        message_path.write_bytes(message)
        subprocess.run([
            "openssl", "pkeyutl", "-sign", "-rawin",
            "-inkey", str(self.scratch / f"{role}-private.pem"),
            "-in", str(message_path), "-out", str(signature_path),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return signature_path.read_bytes().hex()

    def verify(self, role: str, message: bytes, signature_hex: str) -> bool:
        message_path = self.scratch / "message.bin"
        signature_path = self.scratch / "signature.bin"
        message_path.write_bytes(message)
        try:
            signature_path.write_bytes(bytes.fromhex(signature_hex))
        except ValueError:
            return False
        completed = subprocess.run([
            "openssl", "pkeyutl", "-verify", "-rawin", "-pubin",
            "-inkey", str(self.scratch / f"{role}-public.pem"),
            "-in", str(message_path), "-sigfile", str(signature_path),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return completed.returncode == 0
