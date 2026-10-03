# Third-party components

This repository does not vendor the BrainChip Akida SDK, CNN2SNN, QuantizeML, TensorFlow
or their binaries. They are installed separately under their respective terms.

The runtime was validated in the TFG with Akida 2.19.1. The package metadata identifies the
Akida execution engine as proprietary. Review BrainChip's current developer terms before
redistributing SDK material or using the tooling outside the licensed environment.

The optional Linux PCIe driver is not included. BrainChip publishes `akida_dw_edma` separately
under GPL-3.0: <https://github.com/Brainchip-Inc/akida_dw_edma>. Its license does not change the
MIT license of this repository because no driver source or binary is redistributed here.
