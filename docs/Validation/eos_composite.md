# eos_composite.c: Two-phase composite blending

## What this page checks

This page checks the two-phase composite equation of state in `eos_composite.c`, which blends melt and solid properties.
The composite EOS bridges pure melt and solid lookups across the melting interval.
Validation means that we test the fusion entropy and melt fraction interpolation against exact analytical definitions.
If the composite blending is wrong, mantle phase fractions, density jumps, and latent heat release are corrupted.
Coupled planetary simulations in PROTEUS then miscalculate magma ocean solidification times.
The section below details the validation check, its tolerance, and its test command.

## Fusion equals liquidus minus solidus and phi is linear in entropy

**Why this check exists.** Composite blending routines can use wrong denominators, miscalculate melting intervals, or flip boundary bounds. A bug in melt fraction interpolation produces wrong phase mixtures throughout the mantle.

**What it tests.** The test evaluates the analytical limit in the two-phase region: fusion = S_liq - S_sol, and phi = (S - S_sol)/fusion between phase boundaries. It tests the melt fraction at one quarter of the melting interval at 10 GPa. A wrong-denominator regression (using liquidus entropy instead of fusion) shifts phi from 0.25 to about 0.07, which is far beyond tolerance. The fusion entropy lies between 100 and 1500 J/kg/K (603.6 J/kg/K at 10 GPa for the dK09 tables). Sibling tests pin the [0, 1] clamp and pure-phase limits against single-phase lookups.

**How we know the right answer.** By mathematical construction of the linear entropy interpolation, the melt fraction and fusion entropy satisfy exact definitions. The fusion identity matches to rel 1e-10, and the fractional melt position matches to rel 1e-6.

**Why it matters.** The composite EOS determines the local melt fraction and effective thermodynamic properties of partially molten mantle shells.

**Known limit.** This test pins the linear entropy lever rule, but does not benchmark non-linear eutectic melting curves.

??? info "Test details"
    - Reference: Analytical limit: by construction of the two-phase region, fusion = S_liq - S_sol and phi = (S - S_sol)/fusion between the phase boundaries.
    - Tolerance: rel 1e-10 on the fusion identity; rel 1e-6 on the melt fraction at one quarter of the melting interval at 10 GPa.
    - Test id: `tests/test_eos_composite.py::test_fusion_equals_liquidus_minus_solidus_and_phi_is_linear_in_entropy`
    - Command: `make tests_c`, then `pytest -o addopts= tests/test_eos_composite.py::test_fusion_equals_liquidus_minus_solidus_and_phi_is_linear_in_entropy`
    - Companion test: `tests/test_eos_composite.py::test_phase_fraction_bounded_and_truncation_contract_visible` asserts melt fraction clamping to [0, 1] and visibility of untruncated values.

## Related code

- `eos_composite.c`: `EOSCreate_Composite`, `EOSEval_Composite`.
- `tests/test_eos_composite.py`: `test_fusion_equals_liquidus_minus_solidus_and_phi_is_linear_in_entropy`, `test_phase_fraction_bounded_and_truncation_contract_visible`, `test_pure_phase_limits_recover_the_single_phase_lookups`.
