import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

from akd1000_bringup import runtime


class FakeClockMode:
    Performance = "clock-performance"
    Economy = "clock-economy"
    LowPower = "clock-low-power"


class FakeMapMode:
    AllNps = "map-all"
    HwPr = "map-hwpr"
    Minimal = "map-minimal"


class FakeSoc:
    def __init__(self):
        self.clock_mode = None


class FakeDevice:
    def __init__(self):
        self.soc = FakeSoc()
        self.desc = "fake AKD1000"
        self.version = "BC.00.000.002"
        self.ip_version = "IpVersion.v1"


class FakeModel:
    last = None

    def __init__(self, filename):
        self.filename = filename
        self.map_call = None
        self.input_shape = [1, 1, 8]
        self.output_shape = [1, 1, 180]
        self.ip_version = "IpVersion.v1"
        self.external_memory_size = 132480
        self.component_count = {}
        FakeModel.last = self

    def map(self, device, *, hw_only, mode):
        self.map_call = (device, hw_only, mode)

    def predict(self, inputs):
        return np.asarray(inputs) + 2

    def forward(self, inputs):
        return np.asarray(inputs) + 1


def fake_sdk(device_list):
    return SimpleNamespace(
        devices=lambda: device_list,
        soc=SimpleNamespace(ClockMode=FakeClockMode),
        MapMode=FakeMapMode,
        Model=FakeModel,
    )


class RuntimeTests(unittest.TestCase):
    def test_map_model_uses_hardware_only(self):
        with tempfile.TemporaryDirectory() as directory:
            fbz = Path(directory) / "valid.fbz"
            fbz.write_bytes(b"fbz")
            device = FakeDevice()
            with patch.object(
                runtime, "_load_akida", return_value=(fake_sdk([device]), FakeMapMode)
            ):
                mapped = runtime.map_model(fbz, clock_mode="Performance", map_mode="AllNps")
            self.assertEqual(device.soc.clock_mode, "clock-performance")
            self.assertEqual(mapped.model.map_call, (device, True, "map-all"))
            self.assertTrue(runtime.describe_mapping(mapped)["hw_only"])

    def test_map_model_distinguishes_missing_hardware(self):
        with tempfile.TemporaryDirectory() as directory:
            fbz = Path(directory) / "valid.fbz"
            fbz.write_bytes(b"fbz")
            with (
                patch.object(runtime, "_load_akida", return_value=(fake_sdk([]), FakeMapMode)),
                self.assertRaisesRegex(runtime.RuntimeUnavailableError, "returned no hardware"),
            ):
                runtime.map_model(fbz)

    def test_run_raw_accepts_uint8_inputs(self):
        model = FakeModel("generic.fbz")
        mapped = runtime.MappedModel(model, FakeDevice(), "Performance", "AllNps")
        inputs = np.zeros((1, 1, 1, 8), dtype=np.uint8)
        output = runtime.run_raw(mapped, inputs)
        self.assertEqual(output.shape, inputs.shape)
        self.assertTrue(np.all(output == 1))

    def test_run_raw_rejects_float_before_inference(self):
        model = FakeModel("generic.fbz")
        mapped = runtime.MappedModel(model, FakeDevice(), "Performance", "AllNps")
        inputs = np.zeros((1, 1, 1, 8), dtype=np.float32)
        for method in ("forward", "predict"):
            with self.subTest(method=method), patch.object(model, method, new=Mock()) as call:
                with self.assertRaisesRegex(TypeError, "must use uint8, got float32"):
                    runtime.run_raw(mapped, inputs, method)
                call.assert_not_called()

    def test_run_raw_rejects_shape_outside_model_contract(self):
        model = FakeModel("generic.fbz")
        mapped = runtime.MappedModel(model, FakeDevice(), "Performance", "AllNps")
        with self.assertRaisesRegex(ValueError, "model.input_shape"):
            runtime.run_raw(mapped, np.zeros((1, 8), dtype=np.uint8))


if __name__ == "__main__":
    unittest.main()
