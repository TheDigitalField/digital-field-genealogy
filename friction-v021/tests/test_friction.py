import importlib.util
import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "friction.py"
SPEC = importlib.util.spec_from_file_location("friction", SCRIPT)
friction = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(friction)


class FrictionTests(unittest.TestCase):
    def test_world_input_requires_randomness_derived_from_signature(self):
        signature = b"independent-world-input"
        value = {
            "round": 42,
            "signature": signature.hex(),
            "randomness": friction.digest_bytes(signature),
        }
        info = {"period": 3, "genesis_time": 100, "hash": "f" * 64}
        checked = friction.validate_world_input(value, secondary=dict(value), chain_info=info, minimum_timestamp=200)
        self.assertEqual(checked["round"], 42)
        self.assertGreater(checked["round_timestamp"], 200)
        value["randomness"] = "0" * 64
        with self.assertRaises(ValueError):
            friction.validate_world_input(value)

    def test_world_input_must_be_later_than_signal(self):
        signature = b"round-before-signal"
        value = {"round": 2, "signature": signature.hex(), "randomness": friction.digest_bytes(signature)}
        info = {"period": 3, "genesis_time": 100, "hash": "e" * 64}
        with self.assertRaises(ValueError):
            friction.validate_world_input(value, chain_info=info, minimum_timestamp=103)

    def test_mutated_parent_is_rejected(self):
        challenge = "a" * 64
        signal = {"reply": {"challenge": challenge}, "signal_sha256": "b" * 64}
        self.assertTrue(friction.parent_matches(signal, challenge, "b" * 64))
        self.assertFalse(friction.parent_matches(signal, friction.mutate_challenge(challenge), "b" * 64))

    def test_selector_has_response_and_silence_branches(self):
        challenge = "c" * 64
        buckets = {friction.selector(challenge, f"{value:064x}")[1] for value in range(64)}
        self.assertEqual(buckets, {0, 1, 2, 3})

    def test_status_rejects_unknown_phase(self):
        with self.assertRaises(ValueError):
            friction.validate_status({"schema": "digital-field-friction-status/0.2", "phase": "pretend"})

    def test_semantic_digest_ignores_only_its_own_field(self):
        value = {"a": 1, "decision_sha256": "placeholder"}
        digest = friction.semantic_digest(value, "decision_sha256")
        value["decision_sha256"] = digest
        self.assertEqual(friction.semantic_digest(value, "decision_sha256"), digest)

    def test_site_manifest_excludes_manifests_and_runtime_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            root = site / "friction"
            (root / "scripts" / "__pycache__").mkdir(parents=True)
            (site / "visible.txt").write_text("visible\n", encoding="utf-8")
            (root / "CHECKSUMS.sha256").write_text("nested\n", encoding="utf-8")
            (root / "scripts" / "__pycache__" / "cache.pyc").write_bytes(b"cache")
            result = friction.update_site_manifest(root)
            manifest = (site / "CHECKSUMS.sha256").read_text(encoding="utf-8")
            self.assertEqual(result["files"], 1)
            self.assertIn("./visible.txt", manifest)
            self.assertNotIn("CHECKSUMS.sha256", manifest)
            self.assertNotIn("cache.pyc", manifest)

    def test_complete_two_stage_cycle_in_an_isolated_copy(self):
        source_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            sandbox = Path(directory)
            root = sandbox / "friction-v021"
            shutil.copytree(source_root, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            shutil.copytree(
                source_root.parent / "friction",
                sandbox / "friction",
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            workflow_dir = sandbox / ".github" / "workflows"
            workflow_dir.mkdir(parents=True)
            active_a = workflow_dir / "friction-v021-stage-a.yml"
            active_b = workflow_dir / "friction-v021-stage-b.yml"
            shutil.copy2(root / "workflows" / "stage-a.yml", active_a)
            shutil.copy2(root / "workflows" / "stage-b.yml", active_b)
            stage_a_before = active_a.read_bytes()

            emitted = friction.emit_signal(
                root,
                "schedule",
                "DigitalField/test",
                "a" * 40,
                "101",
                "1",
                active_a,
                root / "workflows" / "stage-a.yml",
                active_b,
                root / "workflows" / "stage-b.yml",
            )
            self.assertEqual(emitted["result"], "emitted")
            self.assertEqual(friction.read_json(root / "STATUS.json")["phase"], "awaiting_response")
            repeated = friction.emit_signal(
                root,
                "schedule",
                "DigitalField/test",
                "a" * 40,
                "102",
                "1",
                active_a,
                root / "workflows" / "stage-a.yml",
                active_b,
                root / "workflows" / "stage-b.yml",
            )
            self.assertEqual(repeated["result"], "noop")
            self.assertEqual(active_a.read_bytes(), stage_a_before)

            signal = friction.read_json(Path(emitted["signal_path"]))
            challenge = signal["reply"]["challenge"]
            signature = b"world"
            while friction.selector(challenge, friction.digest_bytes(signature))[1] == 3:
                signature += b"+"
            world = {
                "round": int(time.time() / 3) + 100,
                "signature": signature.hex(),
                "randomness": friction.digest_bytes(signature),
            }
            world_primary = sandbox / "world-primary.json"
            world_secondary = sandbox / "world-secondary.json"
            world_info = sandbox / "world-info.json"
            friction.write_json(world_primary, world)
            friction.write_json(world_secondary, world)
            friction.write_json(
                world_info,
                {"period": 3, "genesis_time": 1, "hash": "d" * 64},
            )

            responded = friction.respond(
                root,
                "workflow_run",
                "DigitalField/test",
                "b" * 40,
                "202",
                "1",
                "101",
                world_primary,
                world_secondary,
                world_info,
                active_b,
                root / "workflows" / "stage-b.yml",
            )
            self.assertEqual(responded["result"], "responded")
            verified = friction.verify_dynamic(root)
            self.assertEqual(verified["phase"], "responded")

    def test_non_parent_workflow_run_is_noop(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            friction.write_json(
                root / "STATUS.json",
                {
                    "schema": "digital-field-friction-status/0.2",
                    "phase": "awaiting_response",
                    "stage_a_run_id": "binding",
                },
            )
            result = friction.respond(
                root,
                "workflow_run",
                "DigitalField/test",
                "b" * 40,
                "202",
                "1",
                "different",
                root / "missing-primary.json",
                root / "missing-secondary.json",
                root / "missing-info.json",
                root / "missing-workflow.yml",
                root / "missing-reference.yml",
            )
            self.assertEqual(result["result"], "noop")


if __name__ == "__main__":
    unittest.main()
