"""Read-only diagnostics for Linux hosts connected to an AKD1000 card."""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

REFERENCE_PACKAGES = ("metatf", "akida", "cnn2snn", "quantizeml", "tensorflow")

DRIVER_SOURCE = "https://github.com/Brainchip-Inc/akida_dw_edma"
DRIVER_SOURCE_CHECKED_ON = "2026-09-29"
CURRENT_METATF_REFERENCE = "2.19.3"
CURRENT_PYTHON_RANGE = ">=3.10,<3.13"


def _command(args: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(args, check=False, capture_output=True, text=True, timeout=10)
        return {
            "available": True,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "error": str(exc)}


def _package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _cpu_governors() -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(Path("/sys/devices/system/cpu").glob("cpu[0-9]*/cpufreq/scaling_governor")):
        try:
            result[path.parent.parent.name] = path.read_text(encoding="utf-8").strip()
        except OSError:
            result[path.parent.parent.name] = "unreadable"
    return result


def _read_text(path: Path) -> dict[str, Any]:
    try:
        return {"available": True, "path": str(path), "text": path.read_text(encoding="utf-8")}
    except OSError as exc:
        return {"available": False, "path": str(path), "error": str(exc)}


def _pcie_configuration() -> dict[str, Any]:
    candidates = (Path("/boot/firmware/config.txt"), Path("/boot/config.txt"))
    config = next((path for path in candidates if path.exists()), None)
    if config is None:
        return {
            "available": False,
            "path": None,
            "note": "No config.txt was found; this check applies only to Raspberry Pi.",
            "pciex1_enabled": None,
            "pciex1_gen3_requested": None,
        }
    report = _read_text(config)
    text = report.pop("text", "")
    section = "[all]"
    entries = []
    includes = []
    for line_number, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if line.startswith("[") and line.endswith("]"):
            section = line
        elif re.match(r"include\s+", line, re.IGNORECASE):
            includes.append({"line": line_number, "section": section, "text": line})
        elif re.match(r"dtparam\s*=.*\bpciex1(?:_gen)?\b", line, re.IGNORECASE):
            entries.append({"line": line_number, "section": section, "text": line})
    report.update({
        "pciex1_enabled": None,
        "pciex1_gen3_requested": None,
        "pcie_entries": entries,
        "include_entries": includes,
        "interpretation": "file_entries_only",
        "note": (
            "Lines are reported with their section and order. Filters, included files, "
            "firmware defaults and HAT detection are not evaluated; confirm with lspci."
        ),
    })
    return report


def _akida_device_nodes() -> list[str]:
    return [str(path) for path in sorted(Path("/dev").glob("akida*"))]


def _driver_kernel_note(release: str) -> dict[str, str]:
    match = re.match(r"^(\d+)\.(\d+)", release)
    if not match:
        return {
            "status": "unknown",
            "note": "The kernel version could not be parsed.",
            "source": DRIVER_SOURCE,
            "source_checked_on": DRIVER_SOURCE_CHECKED_ON,
        }
    major, minor = (int(value) for value in match.groups())
    if (major, minor) < (5, 4):
        return {
            "status": "review_required",
            "note": (
                "The kernel predates the 5.4-6.8 range documented by akida_dw_edma. "
                "Check the official repository before installing."
            ),
            "source": DRIVER_SOURCE,
            "source_checked_on": DRIVER_SOURCE_CHECKED_ON,
        }
    if (major, minor) >= (6, 9):
        return {
            "status": "review_required",
            "note": (
                "The akida_dw_edma README checked for this release documents support through "
                "Linux 6.8. Check the official repository before installing."
            ),
            "source": DRIVER_SOURCE,
            "source_checked_on": DRIVER_SOURCE_CHECKED_ON,
        }
    return {
        "status": "within_documented_range",
        "note": "The kernel is within the 5.4-6.8 range documented by akida_dw_edma.",
        "source": DRIVER_SOURCE,
        "source_checked_on": DRIVER_SOURCE_CHECKED_ON,
    }


def collect_diagnostics() -> dict[str, Any]:
    kernel_release = platform.release()
    packages = {name: _package_version(name) for name in REFERENCE_PACKAGES}
    checks: dict[str, Any] = {
        "python": {
            "executable": sys.executable,
            "version": platform.python_version(),
            "current_documented_range": CURRENT_PYTHON_RANGE,
        },
        "platform": {
            "system": platform.system(),
            "release": kernel_release,
            "machine": platform.machine(),
            "platform": platform.platform(),
        },
        "packages": packages,
        "current_metatf_reference": CURRENT_METATF_REFERENCE,
        "cpu_governors": _cpu_governors(),
        "lspci": _command(["lspci", "-nn"]),
        "loaded_modules": _command(["lsmod"]),
        "pcie_configuration": _pcie_configuration(),
        "akida_device_nodes": _akida_device_nodes(),
        "driver_kernel_note": _driver_kernel_note(kernel_release),
        "throttling": _command(["vcgencmd", "get_throttled"]),
        "running_as_root": os.geteuid() == 0 if hasattr(os, "geteuid") else None,
    }
    try:
        import akida

        hardware = list(akida.devices())
        checks["akida"] = {
            "import_ok": True,
            "version": str(akida.__version__),
            "devices": [
                {
                    "description": str(device.desc),
                    "version": str(device.version),
                    "ip_version": str(device.ip_version),
                    "has_soc": device.soc is not None,
                }
                for device in hardware
            ],
        }
    except Exception as exc:  # noqa: BLE001 - diagnostics must serialize native SDK failures.
        checks["akida"] = {"import_ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return checks


def diagnostics_exit_code(report: dict[str, Any], expected_akida: str | None = None) -> int:
    akida = report.get("akida", {})
    if not akida.get("import_ok") or not akida.get("devices"):
        return 2
    if expected_akida is not None and akida.get("version") != expected_akida:
        return 1
    return 0


def format_diagnostics(report: dict[str, Any], expected_akida: str | None = None) -> str:
    detected_akida = report.get("akida", {}).get("version")
    installed_akida = detected_akida or report["packages"]["akida"] or "not installed"
    lines = [
        f"Python: {report['python']['version']}",
        f"Platform: {report['platform']['platform']}",
        f"Akida SDK: {installed_akida}",
    ]
    if expected_akida is not None:
        status = "match" if installed_akida == expected_akida else "mismatch"
        lines.append(f"Requested Akida version: {expected_akida} ({status})")
    devices = report.get("akida", {}).get("devices", [])
    lines.append(f"AKD1000 devices: {len(devices)}")
    for index, device in enumerate(devices):
        lines.append(f"  [{index}] {device['description']} | version {device['version']}")
    governors = sorted(set(report.get("cpu_governors", {}).values()))
    lines.append(f"CPU governor(s): {', '.join(governors) if governors else 'not readable'}")
    throttling = report["throttling"].get("stdout") or report["throttling"].get("error", "n/a")
    lines.append(f"Throttling: {throttling}")
    pcie = report.get("pcie_configuration", {})
    if pcie.get("available"):
        entries = pcie.get("pcie_entries", [])
        lines.append(
            f"Raspberry Pi PCIe config: {len(entries)} line(s); effective state not inferred"
        )
        for entry in entries:
            lines.append(f"  line {entry['line']} {entry['section']}: {entry['text']}")
    else:
        lines.append("Raspberry Pi PCIe config: not applicable or not readable")
    nodes = report.get("akida_device_nodes", [])
    lines.append(f"Akida device nodes: {', '.join(nodes) if nodes else 'none'}")
    kernel_note = report.get("driver_kernel_note", {})
    lines.append(
        f"Driver/kernel: {kernel_note.get('status', 'unknown')} — {kernel_note.get('note', '')}"
    )
    return "\n".join(lines)


def to_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False)
