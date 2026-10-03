import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from akd1000_bringup import cli, doctor
from akd1000_bringup.artifacts import verify_artifact
from akd1000_bringup.runtime import MappedModel


class RegressionTests(unittest.TestCase):
    def test_verifier_rejects_missing_or_partial_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.fbz"
            path.write_bytes(b"model")
            for expected in ({}, {"size_bytes": 5}, {"sha256_prefix": "a"},
                             {"sha256": "0" * 63}, {"sha256": "x" * 64}):
                with self.subTest(expected=expected), self.assertRaisesRegex(ValueError, "SHA-256"):
                    verify_artifact(path, expected)

    def test_verifier_rejects_same_size_wrong_content(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.fbz"
            path.write_bytes(b"wrong")
            expected = {"size_bytes": 5, "sha256": hashlib.sha256(b"right").hexdigest()}
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                verify_artifact(path, expected)

    def test_pcie_scan_does_not_treat_filtered_lines_as_effective(self):
        content = "[pi4]\ndtparam=pciex1\n[pi5]\ndtparam=pciex1=off\ninclude extra.txt\n"
        with (
            patch.object(doctor.Path, "exists", return_value=True),
            patch.object(doctor, "_read_text", return_value={"available": True, "text": content}),
        ):
            report = doctor._pcie_configuration()
        self.assertIsNone(report["pciex1_enabled"])
        self.assertIsNone(report["pciex1_gen3_requested"])
        self.assertEqual([row["section"] for row in report["pcie_entries"]], ["[pi4]", "[pi5]"])
        self.assertEqual(report["include_entries"][0]["text"], "include extra.txt")

    @staticmethod
    def mapped_model():
        model = SimpleNamespace(
            input_shape=[2], output_shape=[1], ip_version="IpVersion.v1",
            external_memory_size=0, component_count={},
            forward=lambda x: np.sum(x, axis=-1, keepdims=True),
        )
        device = SimpleNamespace(desc="test", version="test", ip_version="IpVersion.v1")
        return MappedModel(model, device, "Performance", "AllNps")

    def test_cli_saved_to_points_to_the_written_numpy_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "input.npy"
            np.save(data, np.asarray([[2, 3]], dtype=np.uint8))
            for name in ("raw", "already.npy", "values.bin"):
                with (
                    self.subTest(name=name),
                    patch.object(cli, "map_model", return_value=self.mapped_model()),
                    contextlib.redirect_stdout(io.StringIO()) as buffer,
                ):
                    status = cli.main(["run", "--model", "unused.fbz", "--input", str(data),
                                       "--output", str(root / name)])
                payload = json.loads(buffer.getvalue())
                self.assertEqual(status, 0)
                saved = Path(payload["saved_to"])
                self.assertTrue(saved.is_file())
                np.testing.assert_array_equal(np.load(saved), [[5]])

    def test_cli_benchmark_saves_identity_and_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model = root / "model.fbz"
            model.write_bytes(b"test-model")
            data = root / "input.npz"
            np.savez(data, signals=np.asarray([[2, 3], [4, 5]], dtype=np.uint8))
            destination = root / "results"
            with (
                patch.object(cli, "map_model", return_value=self.mapped_model()),
                patch.object(cli, "collect_diagnostics", return_value={"test_host": True}),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                status = cli.main([
                    "benchmark", "--model", str(model), "--input", str(data),
                    "--input-key", "signals", "--warmup", "0", "--repetitions", "2",
                    "--output", str(destination),
                ])
            self.assertEqual(status, 0)
            summary = json.loads((destination / "summary.json").read_text())
            provenance = summary["provenance"]
            self.assertEqual(provenance["files"]["model"]["sha256"],
                             hashlib.sha256(model.read_bytes()).hexdigest())
            self.assertEqual(provenance["files"]["input"]["sha256"],
                             hashlib.sha256(data.read_bytes()).hexdigest())
            self.assertEqual(provenance["input_key_requested"], "signals")
            self.assertTrue(provenance["recorded_utc"].endswith("+00:00"))
            self.assertIn("python", provenance["software"])
            self.assertEqual(summary["measurement_boundary"], "host_observed_around_run_raw")
            self.assertEqual(len((destination / "latencies.csv").read_text().splitlines()), 5)
            self.assertEqual(json.loads((destination / "host.json").read_text()),
                             {"test_host": True})


if __name__ == "__main__":
    unittest.main()
