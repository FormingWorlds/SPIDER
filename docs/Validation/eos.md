# eos.c: EOS interface: setup, viscosity, phase boundaries

## What this page checks

This page checks the equation of state interface in `eos.c`, which coordinates material property evaluations.
`eos.c` manages common option parsing for equations of state, loads phase boundaries, and computes composition-dependent viscosity.
Validation means that we compare boundary interpolations and viscosity shifts against independent implementations and published formulas.
If phase boundaries or viscosity calculations are wrong, the melt fraction and convection velocity in the mantle are incorrect.
The sections below detail two validation cases, their tolerances, and their test commands.

## Phase boundary matches independent table read

**Why this check exists.** Table reading routines can swap solidus and liquidus arrays, misplace table indices, or apply incorrect unit conversions. A wrong phase boundary misidentifies the melting state of the mantle without an error message.

**What it tests.** The test evaluates the loaded melt phase boundary against an independent read of `liquidus_A11_H13.dat` (Andrault et al. 2011 liquidus with the Hirschmann 2013 solidus companion). It checks interpolation at the P = 0 table edge, a mid-mantle node, and an off-node deep point. The solidus value at 10 GPa (about 1524 J/kg/K) sits far from the pinned liquidus value (about 2128 J/kg/K), guarding against swapped boundaries. Sibling test `test_viscosity_and_conductivity_dispatch_per_phase` pins per-phase transport dispatch with a 19-decade melt to solid contrast.

**How we know the right answer.** The independent reader evaluates the raw table file using Python numpy interpolation. The C interpolation reproduces these reference values to rel 1e-12.

**Why it matters.** The phase boundary determines where melting occurs throughout the mantle. SPIDER evaluates this boundary to compute the local and global melt fraction.

**Known limit.** The independent verification reads the same source table file, checking interpolation rather than physical accuracy of the underlying experimental dataset.

??? info "Test details"
    - Reference: Cross-implementation cross-check of the loaded melt phase boundary against an independent read of liquidus_A11_H13.dat (Andrault et al. 2011 liquidus with the Hirschmann 2013 solidus companion).
    - Tolerance: rel 1e-12 at the P = 0 table edge, a mid-mantle node, and an off-node deep point.
    - Test id: `tests/test_eos.py::test_phase_boundary_matches_independent_table_read`
    - Command: `make tests_c`, then `pytest -o addopts= tests/test_eos.py::test_phase_boundary_matches_independent_table_read`
    - Companion test: `tests/test_eos.py::test_viscosity_and_conductivity_dispatch_per_phase` verifies that melt and solid phases receive distinct transport properties.

## Compositional viscosity matches Spaargaren et al. (2020)

**Why this check exists.** Piecewise empirical formulas can suffer from transcription typos in branch coefficients, incorrect branch selection, or missing signs. An incorrect viscosity prefactor alters convective vigour by orders of magnitude.

**What it tests.** The test evaluates the piecewise Mg/Si log10 viscosity prefactor of Spaargaren et al. (2020). It re-encodes the published coefficients independently, and pins two branch-pair shifts as hand-derived literals (0.2074 and -1.35803). The test exercises two configurations that shift in opposite directions across more than 1.5 decades, covering all four piecewise branches. Sibling test `test_activation_terms_shape_the_viscosity_profile` pins the zero-pressure limit and pressure-scale damping direction.

**How we know the right answer.** Spaargaren et al. (2020) define the formula analytically. The shifts match option arithmetic to abs 1e-9, and the hand-derived literal transcription pins match to abs 1e-4.

**Why it matters.** Compositional controls on mantle viscosity determine how mantle convective vigor responds to planetary bulk composition.

**Known limit.** The test re-encodes the coefficients as in `eos.c`, so a coefficient that is wrong in both copies is not caught; the 2 hand-derived literals catch a transcription error in either copy.

??? info "Test details"
    - Reference: The piecewise Mg/Si log10 viscosity prefactor of Spaargaren et al. (2020). The test re-encodes the published coefficients independently of eos.c and additionally pins the two branch-pair shifts as hand-derived literals (0.2074 and -1.35803), so a transcription error in either copy of the formula surfaces.
    - Tolerance: abs 1e-9 on the evaluated shifts (closed-form option arithmetic); abs 1e-4 on the literal transcription pins.
    - Test id: `tests/test_eos.py::test_compositional_viscosity_matches_spaargaren`
    - Command: `make tests_c`, then `pytest -o addopts= tests/test_eos.py::test_compositional_viscosity_matches_spaargaren`
    - Companion test: `tests/test_eos.py::test_activation_terms_shape_the_viscosity_profile` checks activation volume and energy scalings in the viscosity model.

## Related code

- `eos.c`: `EOSSetUpFromOptions`, `EOSGetPhaseBoundary`, `EOSEvalSetViscosity`.
- `tests/test_eos.py`: `test_phase_boundary_matches_independent_table_read`, `test_compositional_viscosity_matches_spaargaren`.
