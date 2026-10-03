# AKD1000 Bring-up and Benchmarking Toolkit

Utilities and documentation for bringing up a BrainChip AKD1000 PCIe board,
checking the host/driver/software stack, running a known smoke-test model and
benchmarking Akida FBZ models. The manual covers Linux PCIe hosts and Raspberry
Pi 5 with a compatible FFC-to-PCIe adapter; software checks also run on Windows.

The project grew out of the hardware deployment work for
a Telecommunications Engineering final degree project at Universidad Politécnica de Madrid.
The AoA model-conversion pipeline and experimental results are documented separately
in [akida-model-deployment-pipeline](https://github.com/AlvaroPRuiiz/akida-model-deployment-pipeline).

## Documentation

- [Manual en español](manual/AKD1000_Bringup_Guide_ES.pdf)
- [English manual](manual/AKD1000_Bringup_Guide_EN.pdf)

## Quick start

Download the repository ZIP from GitHub, extract it and open a terminal in the
directory containing `pyproject.toml`. On Linux, with Python 3.11:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements/reproducible.txt
python -m pip install -e . --no-deps
python -m pip check
akd1000-bringup verify --id smoke --model models/akida_v1_smoke_test.fbz
python examples/00_simulator_smoke.py
```

On Windows, create the environment with `py -3.11 -m venv .venv` and activate
it with `.\.venv\Scripts\Activate.ps1`, then follow the same installation steps.
The simulator must produce `[5, 5]`; virtual mapping does not execute physical hardware.
The manual also documents the separate MetaTF installation route.

## Hardware and benchmarking

Follow the manual's assembly and Linux driver instructions before running:

```text
akd1000-bringup doctor
akida devices
python examples/01_hardware_smoke.py
akd1000-bringup run --help
akd1000-bringup benchmark --help
```

`run` preserves the numeric model output. `benchmark` records serial,
host-observed latency and writes timing and provenance files under `outputs/`.
Provide your own FBZ and input data with the model's required shape and preprocessing.

## Repository

- `src/akd1000_bringup/`: diagnostics, artifact verification, execution and benchmarking.
- `examples/`: software and physical-device smoke tests.
- `models/`: reference FBZ and integrity manifest.
- `requirements/`: reference Akida environment.
- `tests/`: automated tests (`python -m unittest discover -s tests -v`).
- `manual/`: Spanish and English LaTeX sources, shared styles, builder and PDFs; `docs/assets/`: manual figures.

Build the manual with `python manual/build.py` (XeLaTeX and BibTeX required).

## Limitations

The revised physical procedure and a complete session with a new user remain pending.
SDK power statistics
do not measure total system consumption; benchmark timings include host overhead.
Driver compatibility must be checked against the actual Linux kernel and SDK.
No CPU, GPU or FPGA speedup claim is made by this toolkit.

Original content retains its MIT license. BrainChip's SDK and PCIe driver are not
redistributed; see [third-party notices](THIRD_PARTY_NOTICES.md).
Contributor checks are in [CONTRIBUTING.md](CONTRIBUTING.md);
figure provenance is in [docs/assets/README.md](docs/assets/README.md).
