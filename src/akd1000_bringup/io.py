"""NumPy data loaders for model inputs."""

from __future__ import annotations

from pathlib import Path

import numpy as np


def load_array(path: str | Path, key: str | None = None) -> np.ndarray:
    """Load one non-empty numeric array without imposing an application contract."""

    source = Path(path)
    if source.suffix == ".npy":
        values = np.load(source, allow_pickle=False)
    elif source.suffix == ".npz":
        with np.load(source, allow_pickle=False) as archive:
            selected = key
            if selected is None:
                candidates = [name for name in ("X", "inputs", "data_test") if name in archive]
                if len(candidates) != 1:
                    raise ValueError(
                        "Use --input-key to select exactly one array from the NPZ file."
                    )
                selected = candidates[0]
            if selected not in archive:
                raise KeyError(f"NPZ key not found: {selected}")
            values = archive[selected]
    else:
        raise ValueError("Inputs must be stored as .npy or .npz.")
    if not isinstance(values, np.ndarray) or values.size == 0:
        raise ValueError("The selected input must be a non-empty NumPy array.")
    if not np.issubdtype(values.dtype, np.number):
        raise TypeError(f"The selected input must be numeric, got {values.dtype}.")
    return values
