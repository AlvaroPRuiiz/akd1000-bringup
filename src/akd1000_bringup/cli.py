"""Command-line interface for diagnostics, execution and measurement."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from .artifacts import load_manifest, verify_artifact
from .benchmark import collect_provenance, run_benchmark, write_results
from .doctor import collect_diagnostics, diagnostics_exit_code, format_diagnostics, to_json
from .io import load_array
from .runtime import describe_mapping, map_model, run_raw


def _mapping_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", type=Path, required=True, help="Path to an Akida v1 FBZ.")
    parser.add_argument(
        "--clock", choices=("Performance", "Economy", "LowPower"), default="Performance"
    )
    parser.add_argument(
        "--map",
        dest="map_mode",
        choices=("AllNps", "HwPr", "Minimal"),
        default="AllNps",
    )
    parser.add_argument("--device-index", type=int, default=0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="akd1000-bringup")
    commands = parser.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser("doctor", help="Run read-only host and hardware diagnostics.")
    doctor.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    doctor.add_argument(
        "--expected-akida",
        help="Return 1 if the detected SDK differs; omit for a version-neutral check.",
    )

    verify = commands.add_parser("verify", help="Verify an FBZ against a manifest entry.")
    verify.add_argument("--model", type=Path, required=True)
    verify.add_argument("--manifest", type=Path, default=Path("models/manifest.json"))
    verify.add_argument("--id", required=True, help="Model identifier in the manifest.")

    run = commands.add_parser(
        "run", help="Run a single-input/single-output model and preserve its numeric output."
    )
    _mapping_arguments(run)
    run.add_argument("--input", type=Path, required=True, help="Input .npy or .npz file.")
    run.add_argument("--input-key", help="Array key when --input is an NPZ archive.")
    run.add_argument("--method", choices=("forward", "predict"), default="forward")
    run.add_argument("--output", type=Path, help="Optional destination .npy for the raw output.")

    benchmark = commands.add_parser(
        "benchmark", help="Measure serial, host-observed inference latency."
    )
    _mapping_arguments(benchmark)
    benchmark.add_argument("--input", type=Path, required=True)
    benchmark.add_argument("--input-key")
    benchmark.add_argument("--method", choices=("forward", "predict"), default="forward")
    benchmark.add_argument("--warmup", type=int, default=8)
    benchmark.add_argument("--repetitions", type=int, default=1)
    benchmark.add_argument("--output", type=Path, default=Path("outputs/latest"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "doctor":
            report = collect_diagnostics()
            report["requested_akida_version"] = args.expected_akida
            print(to_json(report) if args.json else format_diagnostics(report, args.expected_akida))
            return diagnostics_exit_code(report, args.expected_akida)
        if args.command == "verify":
            manifest = load_manifest(args.manifest)
            result = verify_artifact(args.model, manifest["models"][args.id])
            print(json.dumps(result, indent=2))
            return 0
        if args.command == "run":
            inputs = load_array(args.input, args.input_key)
            mapped = map_model(
                args.model,
                clock_mode=args.clock,
                map_mode=args.map_mode,
                device_index=args.device_index,
            )
            output = run_raw(mapped, inputs, args.method)
            destination = args.output
            if destination is not None:
                if not str(destination).endswith(".npy"):
                    destination = Path(str(destination) + ".npy")
                destination.parent.mkdir(parents=True, exist_ok=True)
                np.save(destination, output, allow_pickle=False)
            payload = {
                "mapping": describe_mapping(mapped),
                "method": args.method,
                "input": {"shape": list(inputs.shape), "dtype": str(inputs.dtype)},
                "output": {"shape": list(output.shape), "dtype": str(output.dtype)},
                "saved_to": str(destination) if destination is not None else None,
            }
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 0
        if args.command == "benchmark":
            inputs = load_array(args.input, args.input_key)
            provenance = collect_provenance(args.model, args.input, args.input_key)
            diagnostics = collect_diagnostics()
            mapped = map_model(
                args.model,
                clock_mode=args.clock,
                map_mode=args.map_mode,
                device_index=args.device_index,
            )
            summary, rows = run_benchmark(
                mapped,
                inputs,
                method=args.method,
                warmup=args.warmup,
                repetitions=args.repetitions,
            )
            summary["provenance"] = provenance
            summary["host_diagnostics_file"] = "host.json"
            write_results(args.output, summary, rows, diagnostics=diagnostics)
            print(json.dumps(summary, indent=2, ensure_ascii=False))
            return 0
    except (OSError, IndexError, KeyError, RuntimeError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
