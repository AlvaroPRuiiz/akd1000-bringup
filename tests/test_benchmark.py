import unittest
from types import SimpleNamespace
from typing import ClassVar

import numpy as np

from akd1000_bringup.benchmark import run_benchmark
from akd1000_bringup.runtime import MappedModel


class FakeModel:
    input_shape: ClassVar[list[int]] = [2]
    output_shape: ClassVar[list[int]] = [1, 1]
    ip_version = "IpVersion.v1"
    external_memory_size = 0
    component_count: ClassVar[dict] = {}

    def forward(self, values):
        return np.sum(values, axis=-1, keepdims=True)


class BenchmarkTests(unittest.TestCase):
    def test_benchmark_is_contract_neutral(self):
        device = SimpleNamespace(
            desc="fake AKD1000",
            version="test",
            ip_version="IpVersion.v1",
        )
        mapped = MappedModel(FakeModel(), device, "Performance", "AllNps")
        inputs = np.arange(6, dtype=np.float32).reshape(3, 2)
        summary, rows = run_benchmark(mapped, inputs, warmup=1, repetitions=2)
        self.assertEqual(summary["samples"], 3)
        self.assertEqual(summary["method"], "forward")
        self.assertEqual(len(rows), 6)
        self.assertEqual(set(rows[0]), {"repetition", "sample_index", "latency_ms"})

    def test_benchmark_rejects_missing_sample_axis(self):
        mapped = MappedModel(FakeModel(), SimpleNamespace(), "Performance", "AllNps")
        with self.assertRaisesRegex(ValueError, "sample dimension"):
            run_benchmark(mapped, np.asarray(1))

    def test_benchmark_rejects_wrong_sample_shape(self):
        mapped = MappedModel(FakeModel(), SimpleNamespace(), "Performance", "AllNps")
        with self.assertRaisesRegex(ValueError, "model.input_shape"):
            run_benchmark(mapped, np.zeros((3, 1), dtype=np.float32))


if __name__ == "__main__":
    unittest.main()
