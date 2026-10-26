# eos.c: EOS interface: setup, viscosity, phase boundaries

## What this page checks

This page checks the equation of state interface in `eos.c`, which coordinates material property evaluations.
`eos.c` manages common option parsing for equations of state, loads phase boundaries, and computes composition-dependent viscosity.
Validation means that we compare boundary interpolations and viscosity shifts against independent implementations and closed-form formulas.
If phase boundaries or viscosity calculations are wrong, the melt fraction and convection velocity in the mantle are incorrect.
The sections below detail two validation cases, their tolerances, and their test commands.

## Phase boundary matches independent table read

**Why this check exists.** Table reading routines can swap solidus and liquidus arrays, misplace table indices, or apply incorrect unit conversions. A wrong phase boundary misidentifies the melting state of the mantle without an error message.

**What it tests.** The phase boundaries are the liquidus, the entropy above which the mantle is fully molten, and the solidus, below which it is fully solid. The test evaluates the loaded liquidus against an independent read of `liquidus_A11_H13.dat` (Andrault et al. 2011 liquidus with the Hirschmann 2013 solidus companion). It checks interpolation at the P = 0 table edge, a mid-mantle node, and an off-node deep point. The solidus entropy at 10 GPa (about 1524 J/kg/K) sits far from the pinned liquidus entropy (about 2128 J/kg/K), guarding against swapped boundaries. Sibling test `test_viscosity_and_conductivity_dispatch_per_phase` pins per-phase transport dispatch with a 19-decade melt to solid contrast.

**How we know the right answer.** The independent reader evaluates the raw table file using Python numpy interpolation. The C interpolation reproduces these reference values to rel 1e-12.

**Why it matters.** The phase boundary determines where melting occurs throughout the mantle. SPIDER evaluates this boundary to compute the local and global melt fraction.

**Known limit.** The independent verification reads the same source table file, checking interpolation rather than physical accuracy of the underlying experimental dataset.

![Liquidus entropy against pressure from the table and from eos.c at 3 probes](../assets/validation/eos_phase_boundary.svg#only-light){ width="80%" }
![Liquidus entropy against pressure from the table and from eos.c at 3 probes](../assets/validation/eos_phase_boundary_dark.svg#only-dark){ width="80%" }

**How to read the plot.** The x-axis is the pressure in GPa and the y-axis the entropy of the liquidus in J/kg/K. The line is the liquidus table `liquidus_A11_H13.dat` read with numpy (every 10th node, context). The circles are the asserted values of eos.c at 3 probes. These are the table edge at 0 GPa, a table node at 10 GPa, and an off-node point at 65.5 GPa. The cross is the solidus at 10 GPa, 1524.43 J kg$^{-1}$ K$^{-1}$, which must differ from the code value by more than 100. A pass means that the circles lie on the line (relative 1e-12).

??? info "Test details"
    - Reference: Cross-implementation cross-check of the loaded melt phase boundary against an independent read of liquidus_A11_H13.dat (Andrault et al. 2011 liquidus with the Hirschmann 2013 solidus companion).
    - Tolerance: rel 1e-12 at the P = 0 table edge, a mid-mantle node, and an off-node deep point.
    - Test id: `tests/test_eos.py::test_phase_boundary_matches_independent_table_read`
    - Command: `make tests_c`, then `pytest -o addopts= tests/test_eos.py::test_phase_boundary_matches_independent_table_read` (add `--validation-plots` to write the plot pair)
    - Companion test: `tests/test_eos.py::test_viscosity_and_conductivity_dispatch_per_phase` verifies that melt and solid phases receive distinct transport properties.

## Compositional viscosity matches Spaargaren et al. (2020)

**Why this check exists.** Piecewise empirical formulas can suffer from transcription typos in branch coefficients, incorrect branch selection, or missing signs. An incorrect viscosity prefactor alters convective vigour by orders of magnitude.

**What it tests.** The test evaluates the piecewise Mg/Si log10 viscosity prefactor of Spaargaren et al. (2020). It re-encodes the coefficients independently of `eos.c`, and pins two branch-pair shifts as hand-derived literals (0.2074 and -1.35803). The comment in `eos.c` says the expressions were worked out in an MSc thesis (2018) and are explained in Spaargaren et al. (2020). The test exercises two configurations that shift in opposite directions across more than 1.5 decades, covering all four piecewise branches. Sibling test `test_activation_terms_shape_the_viscosity_profile` checks the pressure and temperature dependence: no shift at P = 0, a positive shift at depth, its damping by the pressure scale, and the sign of the temperature term.

**How we know the right answer.** The prefactor is a piecewise closed form in Mg/Si. The shifts match option arithmetic to abs 1e-9, and the hand-derived literal transcription pins match to abs 1e-4.

**Why it matters.** Compositional controls on mantle viscosity determine how mantle convective vigor responds to planetary bulk composition.

**Known limit.** The test re-encodes the coefficients as in `eos.c`. The 2 hand-derived literals catch an error that is in both copies at the 4 compositions they probe; a coefficient that affects neither literal is not caught.

![Spaargaren viscosity prefactor against Mg/Si with the eos.c shifts](../assets/validation/eos_spaargaren_viscosity.svg#only-light){ width="80%" }
![Spaargaren viscosity prefactor against Mg/Si with the eos.c shifts](../assets/validation/eos_spaargaren_viscosity_dark.svg#only-dark){ width="80%" }

**How to read the plot.** The x-axis is the Mg/Si ratio and the y-axis the log10 viscosity prefactor. The line is the piecewise prefactor of Spaargaren et al. (2020), as the test re-encodes it (context). The hollow squares are its values at the 2 reference compositions, 1.6 and 0.9. The circles are each reference value plus the asserted shift of eos.c (melt log10 viscosity minus the configured 2.0), at 1.4 and 1.2. A pass means that the circles lie on the line (absolute 1e-9), the one at 1.4 above its square and the one at 1.2 below.

??? info "Test details"
    - Reference: The piecewise Mg/Si log10 viscosity prefactor of Spaargaren et al. (2020). The test re-encodes the coefficients independently of eos.c and additionally pins the two branch-pair shifts as hand-derived literals (0.2074 and -1.35803), so a transcription error in either copy of the formula surfaces.
    - Tolerance: abs 1e-9 on the evaluated shifts (closed-form option arithmetic); abs 1e-4 on the literal transcription pins.
    - Test id: `tests/test_eos.py::test_compositional_viscosity_matches_spaargaren`
    - Command: `make tests_c`, then `pytest -o addopts= tests/test_eos.py::test_compositional_viscosity_matches_spaargaren` (add `--validation-plots` to write the plot pair)
    - Companion test: `tests/test_eos.py::test_activation_terms_shape_the_viscosity_profile` checks the pressure and temperature dependence of the viscosity (no shift at P = 0, a positive shift at depth, damping by the pressure scale, and the sign of the temperature term).

## Related code

- `eos.c`: `EOSSetUpFromOptions`, `EOSGetPhaseBoundary`, `EOSEvalSetViscosity`.
- `tests/test_eos.py`: `test_phase_boundary_matches_independent_table_read`, `test_compositional_viscosity_matches_spaargaren`.
