import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "beacon.py"
SPEC = importlib.util.spec_from_file_location("beacon", SCRIPT)
beacon = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(beacon)


class BeaconTests(unittest.TestCase):
    def test_semantic_digest_changes_with_run(self):
        one = {"run": "1", "body": "x"}
        two = {"run": "2", "body": "x"}
        self.assertNotEqual(beacon.digest_bytes(beacon.canonical(one)), beacon.digest_bytes(beacon.canonical(two)))

    def test_status_rejects_unknown_phase(self):
        with self.assertRaises(ValueError):
            beacon.validate_status({"schema": "digital-field-beacon-status/0.1", "phase": "pretend"})

    def test_write_json_is_utf8_and_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "value.json"
            beacon.write_json(path, {"field": "señal"})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["field"], "señal")


if __name__ == "__main__":
    unittest.main()

