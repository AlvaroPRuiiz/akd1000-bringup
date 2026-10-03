#!/usr/bin/env python3
"""Run the included deterministic Akida v1 smoke model on physical hardware."""

from __future__ import annotations

import argparse
from pathlib import Path

import akida
import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("models/akida_v1_smoke_test.fbz"),
    )
    parser.add_argument("--device-index", type=int, default=0)
    args = parser.parse_args()

    devices = list(akida.devices())
    if not devices:
        raise SystemExit("FAIL: Akida detects no hardware. Complete the manual preflight first.")
    if not 0 <= args.device_index < len(devices):
        raise SystemExit(f"FAIL: device-index is out of range; found {len(devices)} device(s).")

    device = devices[args.device_index]
    model = akida.Model(str(args.model))
    model.map(device, hw_only=True, mode=akida.MapMode.AllNps)

    sample = np.asarray([[[[3, 2, 1, 4]]]], dtype=np.uint8)
    output = model.forward(sample)
    expected = np.asarray([[[[5, 5]]]], dtype=np.int32)
    np.testing.assert_array_equal(output, expected)

    print(f"Device: {device.desc}")
    print(f"Version: {device.version}")
    print(f"Output: {output.reshape(-1).tolist()}")
    print("PASS: the FBZ executed correctly on physical hardware.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
