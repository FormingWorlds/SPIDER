# eos_composite.c: Two-phase composite blending

**Source under test**: `eos_composite.c`

## Cases

### Fusion equals liquidus minus solidus and phi is linear in entropy

**Reference-pinned test**: `tests/test_eos_composite.py::test_fusion_equals_liquidus_minus_solidus_and_phi_is_linear_in_entropy`

**Reference**: Analytical limit: by construction of the two-phase region, fusion = S_liq - S_sol and phi = (S - S_sol)/fusion between the phase boundaries.

**Tolerance**: rel 1e-10 on the fusion identity; rel 1e-6 on the melt fraction at one quarter of the melting interval at 10 GPa.

**Command**: `make tests_c`, then `pytest -o addopts= tests/test_eos_composite.py::test_fusion_equals_liquidus_minus_solidus_and_phi_is_linear_in_entropy`

**Discrimination guards**: A wrong-denominator regression (liquidus entropy instead of fusion) shifts phi from 0.25 to about 0.07, far beyond tolerance; the fusion entropy lies between 100 and 1500 J/kg/K (603.6 J/kg/K at 10 GPa for the dK09 tables); companion tests pin the [0, 1] clamp and the pure-phase limits against the single-phase lookups.

The composite EOS blends the melt and solid lookups across the melting interval. The melt fraction definition, the fusion entropy, and the recovery of the pure end-members away from the interval are each pinned; the truncation contract is made visible through the untruncated diagnostic value.
