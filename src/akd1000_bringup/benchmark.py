"""Transparent host-observed latency benchmark for AKD1000."""

from __future__ import annotations

import csv
import json
import time
import platform
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

import numpy as np

from . import __version__
from .artifacts import sha256_file
from .runtime import MappedModel, describe_mapping, run_raw


def run_benchmark(
    mapped: MappedModel,
    inputs: np.ndarray,
    *,
    method: str = "forward",
    warmup: int = 8,
    repetitions: int = 1,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    checked = np.asarray(inputs)
    if checked.size == 0 or not np.issubdtype(checked.dtype, np.number):
        raise ValueError("Inputs must be a non-empty numeric array.")
    if checked.ndim == 0:
        raise ValueError("Benchmark input must have a leading sample dimension.")
    expected_sample_shape = tuple(mapped.model.input_shape)
    if tuple(checked.shape[1:]) != expected_sample_shape:
        raise ValueError(
            f"Sample shape {tuple(checked.shape[1:])} does not match "
            f"model.input_shape {expected_sample_shape}."
        )
    if warmup < 0 or repetitions < 1:
        raise ValueError("warmup must be >= 0 and repetitions must be >= 1.")
    for sample in checked[: min(warmup, len(checked))]:
        run_raw(mapped, np.expand_dims(sample, axis=0), method)

    rows: list[dict[str, Any]] = []
    for repetition in range(repetitions):
        for sample_index, sample in enumerate(checked):
            batch = np.expand_dims(sample, axis=0)
            start = time.perf_counter()
            run_raw(mapped, batch, method)
            latency_ms = (time.perf_counter() - start) * 1000.0
            rows.append(
                {
                    "repetition": repetition,
                    "sample_index": sample_index,
                    "latency_ms": latency_ms,
                }
            )

    latencies = np.asarray([row["latency_ms"] for row in rows], dtype=np.float64)
    summary: dict[str, Any] = {
        "measurement_boundary": "host_observed_around_run_raw",
        "includes": ["input_validation", "sdk_call", "output_validation"],
        "excludes": ["file_loading", "mapping", "warmup", "result_writing"],
        "method": method,
        "samples": int(checked.shape[0]),
        "repetitions": repetitions,
        "warmup_samples": min(warmup, len(checked)),
        "latency_mean_ms": float(np.mean(latencies)),
        "latency_std_ms": float(np.std(latencies)),
        "latency_median_ms": float(np.median(latencies)),
        "latency_p95_ms": float(np.percentile(latencies, 95)),
        "serial_throughput_estimate_inf_s": float(1000.0 / np.mean(latencies)),
        "input": {"shape": list(checked.shape), "dtype": str(checked.dtype)},
        "mapping": describe_mapping(mapped),
    }
    return summary, rows


def write_results(
    output_dir: str | Path,
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    diagnostics: dict[str, Any] | None = None,
) -> None:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if diagnostics is not None:
        (destination / "host.json").write_text(
            json.dumps(diagnostics, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    if rows:
        with (destination / "latencies.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def collect_provenance(
    model_path: str | Path, input_path: str | Path, input_key: str | None = None
) -> dict[str, Any]:
    """Record file identity and software before mapping and timed inference."""

    files = {}
    for label, source in (("model", model_path), ("input", input_path)):
        path = Path(source)
        files[label] = {
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    try:
        akida_version = metadata.version("akida")
    except metadata.PackageNotFoundError:
        akida_version = None
    return {
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "recorded_before": "hardware_mapping_and_warmup",
        "files": files,
        "input_key_requested": input_key,
        "software": {
            "akd1000_bringup": __version__,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "akida": akida_version,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
    }
