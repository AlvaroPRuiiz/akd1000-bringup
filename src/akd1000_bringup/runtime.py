"""Wrapper around the Akida runtime API."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


class RuntimeUnavailableError(RuntimeError):
    """Raised when the Akida SDK or hardware is unavailable."""


@dataclass
class MappedModel:
    model: Any
    device: Any
    clock_mode: str
    map_mode: str
    hw_only: bool = True


def _load_akida() -> tuple[Any, Any]:
    try:
        import akida
    except ImportError as exc:
        raise RuntimeUnavailableError(
            "Akida SDK not found. Install the selected runtime inside the virtual environment."
        ) from exc
    try:
        return akida, akida.MapMode
    except AttributeError as exc:
        raise RuntimeUnavailableError(
            "The installed Akida SDK does not expose the documented akida.MapMode API."
        ) from exc


def list_devices() -> list[Any]:
    akida, _ = _load_akida()
    return list(akida.devices())


def map_model(
    fbz_path: str | Path,
    *,
    clock_mode: str = "Performance",
    map_mode: str = "AllNps",
    device_index: int = 0,
    hw_only: bool = True,
) -> MappedModel:
    """Load an FBZ, select a physical AKD1000 and map it with an explicit policy."""

    akida, MapMode = _load_akida()
    fbz = Path(fbz_path)
    if not fbz.is_file() or fbz.stat().st_size == 0:
        raise FileNotFoundError(f"FBZ not found or empty: {fbz}")
    available = list(akida.devices())
    if not available:
        raise RuntimeUnavailableError(
            "akida.devices() returned no hardware. Check power, PCIe and the SDK before checking the model."
        )
    if device_index < 0 or device_index >= len(available):
        raise IndexError(f"Device index {device_index} is invalid for {len(available)} device(s).")
    device = available[device_index]
    if device.soc is None:
        raise RuntimeUnavailableError("Selected device exposes no SoC control interface.")
    try:
        clock_value = getattr(akida.soc.ClockMode, clock_mode)
    except AttributeError as exc:
        raise ValueError("Clock mode must be Performance, Economy or LowPower.") from exc
    try:
        map_value = getattr(MapMode, map_mode)
    except AttributeError as exc:
        raise ValueError("Map mode must be AllNps, HwPr or Minimal.") from exc

    device.soc.clock_mode = clock_value
    model = akida.Model(str(fbz))
    model.map(device, hw_only=hw_only, mode=map_value)
    return MappedModel(
        model=model,
        device=device,
        clock_mode=clock_mode,
        map_mode=map_mode,
        hw_only=hw_only,
    )


def run_raw(mapped: MappedModel, inputs: np.ndarray, method: str = "forward") -> np.ndarray:
    """Execute one numeric input tensor and return one numeric output tensor unchanged."""

    values = np.asarray(inputs)
    if values.size == 0 or not np.issubdtype(values.dtype, np.number):
        raise ValueError("Inputs must be a non-empty numeric array.")
    expected_sample_shape = tuple(mapped.model.input_shape)
    if values.ndim < 1 or tuple(values.shape[1:]) != expected_sample_shape:
        raise ValueError(
            "Input shape must be (batch, *model.input_shape): "
            f"received {tuple(values.shape)}, expected (*, {expected_sample_shape})."
        )
    if method not in {"forward", "predict"}:
        raise ValueError("Method must be 'forward' or 'predict'.")
    operation = getattr(mapped.model, method, None)
    if operation is None:
        raise RuntimeUnavailableError(f"The installed Akida SDK exposes no model.{method}().")
    output = operation(values)
    if not isinstance(output, np.ndarray):
        raise RuntimeUnavailableError(
            "The generic runner supports one NumPy output tensor; use the model-specific API "
            "for structured or multiple outputs."
        )
    if output.size == 0 or not np.issubdtype(output.dtype, np.number):
        raise RuntimeUnavailableError("The Akida SDK returned an empty or non-numeric output.")
    return output


def describe_mapping(mapped: MappedModel) -> dict[str, Any]:
    model = mapped.model
    device = mapped.device
    component_count = {
        getattr(key, "name", str(key)): int(value)
        for key, value in getattr(model, "component_count", {}).items()
    }
    return {
        "device_description": str(device.desc),
        "device_version": str(device.version),
        "device_ip_version": str(device.ip_version),
        "model_ip_version": str(model.ip_version),
        "input_shape": list(model.input_shape),
        "output_shape": list(model.output_shape),
        "external_memory_size": int(model.external_memory_size),
        "component_count": component_count,
        "clock_mode": mapped.clock_mode,
        "map_mode": mapped.map_mode,
        "hw_only": mapped.hw_only,
    }
