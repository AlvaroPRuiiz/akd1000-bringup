# Included model

`akida_v1_smoke_test.fbz` is a deterministic Akida v1 deployment test created by
`examples/00_simulator_smoke.py`. It has four 4-bit inputs and two outputs; for the input
`[3, 2, 1, 4]`, both outputs equal `5`.

The model checks software execution, FBZ serialization, virtual hardware-only mapping and
physical AKD1000 execution. It does not represent an application or establish performance.

```bash
akd1000-bringup verify \
  --id smoke \
  --model models/akida_v1_smoke_test.fbz
```

Expected SHA-256:
`ae5bc251ac1fa6a9665bf5df746f616a4d5c31b58a2201031fc4570d5a5501a4`.
