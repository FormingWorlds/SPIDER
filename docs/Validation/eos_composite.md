# eos_composite.c: Two-phase composite blending

**Source under test**: `eos_composite.c`

**Reference-pinned test**: `tests/test_eos_composite.py::test_fusion_equals_liquidus_minus_solidus_and_phi_is_linear_in_entropy`

**Anchor**: Analytical limit: by construction of the two-phase region, fusion = S_liq - S_sol and phi = (S - S_sol)/fusion between the phase boundaries.

**Tolerance**: rel 1e-10 on the fusion identity; rel 1e-6 on the melt fraction at one quarter of the melting interval at 10 GPa.

**Discrimination guards**: A wrong-denominator regression (liquidus entropy instead of fusion) shifts phi from 0.25 to about 0.07, far beyond tolerance; the fusion scale is bounded to the few-hundred J/kg/K range of the dK09 tables; companion tests pin the [0, 1] clamp and the pure-phase limits against the single-phase lookups.

The composite EOS blends the melt and solid lookups across the melting interval. The melt fraction definition, the fusion entropy, and the recovery of the pure end-members away from the interval are each pinned; the truncation contract is made visible through the untruncated diagnostic value.
