# Changelog

## 1.2.2 - 2026-09-29

- Revised Spanish prose using the final thesis as a vocabulary reference.
- Fixed the shared CLI installation step, working directories and software scope.
- Added clickable bibliography links and clarified independent heatmap colour scales.
- Required a full SHA-256 for verification and fixed reported NumPy output paths.
- Reported PCIe configuration entries without inferring effective filtered settings.
- Recorded benchmark file identity, software versions, UTC time and host diagnostics.
- Matched the documented timing boundary to the actual run_raw call.
- Added regression tests, pinned Ruff and aligned CI checks with local validation.
- Updated SPDX packaging metadata and added a cross-platform PDF builder.
- Reconciled the novice-validation criteria and photo provenance.


## 1.2.1 - 2026-09-04

- Switched to the documented public `akida.MapMode` API and made `hw_only` reporting exact.
- Added strict input-shape and single-output checks to the generic runner and benchmark.
- Removed the undocumented low-level power-event path; the manual retains the documented
  `model.statistics` workflow and its measurement limits.
- Prevented the simulator smoke test from overwriting the versioned reference FBZ.
- Reconciled the novice-validation task identifiers and refreshed the release audit.

## 1.2.0 - 2026-09-04

- Renamed the package and command to `akd1000-bringup`.
- Reduced the public CLI to four application-neutral commands.
- Removed AoA decoding, historical result tables, conversion helpers and publication drafts.
- Kept the AoA work only as a cited academic appendix in the manual.
- Removed unused photo variants while retaining isolated versions for reading. Original photographs remain in the author's thesis archive outside this public repository.
- Updated the public release to the MIT license.

## 1.1.0 - 2026-09-03

- Rebuilt the authoritative user manual as a versioned LaTeX scientific manual.
- Separated the current vendor-supported route from the historical SDK reference route.
- Generalized setup, mapping, input-contract and troubleshooting instructions beyond AoA.
- Added a contract-neutral `run` command while retaining the documented AoA example.
- Made `doctor` version-neutral by default and added explicit version enforcement.
- Replaced distracting photo backgrounds while preserving the originals in the author's separate thesis archive.
- Documented the exact component descriptions recoverable from the TFG and their limits.

## 1.0.0 - 2026-09-02

- Expanded the Spanish manual into a zero-to-operation curriculum.
- Added recovered photographs of the exact Raspberry Pi 5, Waveshare carrier and AKD1000 setup.
- Added official PCIe, driver, SDK, mapping, telemetry, edge-learning and C++ guidance.
- Added deterministic Akida v1 software and physical-hardware smoke tests.
- Added a redistributable 974-byte FBZ with full SHA-256 provenance.
- Extended diagnostics with PCIe config, device nodes and kernel/driver guidance.
- Added a novice usability-validation checklist and research provenance log.

## 0.1.0 - 2026-09-02

- Recovered the final TFG environment and deployment contract.
- Added a hardware-only Akida v1 inference CLI.
- Added device, host and version diagnostics.
- Added strict AoA input/output validation and circular metrics.
- Added a minimal host-observed latency and API-power diagnostic runner.
- Added bilingual manuals, reference results and publication guidance.
- Added unit tests and static-analysis configuration.
