#!/usr/bin/env python3
"""Create and run a tiny Akida v1 model without physical hardware.

The model has four 4-bit inputs and two linear outputs. Output 0 adds the
first two values; output 1 adds the last two. For [3, 2, 1, 4], both outputs
must therefore be 5. This is a deployment test, not an application model.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import akida
import numpy as np


def build_model() -> akida.Model:
    model = akida.Model()
    model.add(akida.InputData((1, 1, 4), input_bits=4, name="input"))
    model.add(
        akida.FullyConnected(
            2,
            name="pair_sums",
            weights_bits=4,
            activation=False,
        )
    )

    layer = model.get_layer(1)
    weights = layer.get_variable("weights")
    weights[...] = 0
    weights[0, 0, 0, 0] = 1
    weights[0, 0, 1, 0] = 1
    weights[0, 0, 2, 1] = 1
    weights[0, 0, 3, 1] = 1
    layer.set_variable("weights", weights)
    return model


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/smoke/akida_v1_smoke_test.fbz"),
        help="Where to save the regenerated FBZ without replacing the reference artifact.",
    )
    args = parser.parse_args()

    model = build_model()
    sample = np.asarray([[[[3, 2, 1, 4]]]], dtype=np.uint8)
    output = model.forward(sample)
    expected = np.asarray([[[[5, 5]]]], dtype=np.int32)
    np.testing.assert_array_equal(output, expected)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(args.output))

    reloaded = akida.Model(str(args.output))
    np.testing.assert_array_equal(reloaded.forward(sample), expected)

    reloaded.map(akida.AKD1000(), hw_only=True)
    sequence = reloaded.sequences[0]
    print(f"Akida SDK: {akida.__version__}")
    print(f"Simulator output: {output.reshape(-1).tolist()}")
    print(f"Virtual AKD1000 program size: {len(sequence.program)} bytes")
    print(f"Saved: {args.output}")
    print("PASS: software execution, serialization and hardware-only mapping are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
