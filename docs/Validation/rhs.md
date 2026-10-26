# rhs.c: Entropy time-derivative assembly

## What this page checks

This page checks the right-hand side time-derivative assembly in `rhs.c`, which governs thermal evolution.
`rhs.c` compiles flux divergences and internal heating source terms into the rate of change dS/dt of the specific entropy S (J/kg/K) at each node. This right-hand side is the function that the time stepper integrates.
Validation means that we check reported time derivatives against finite-difference slopes between consecutive output snapshots.
If right-hand side evaluation is incorrect, the numerical timestepper integrates along an erroneous trajectory.
The section below details the validation check, its tolerance, and its test command.

## Reported dS/dt matches finite difference of outputs

**Why this check exists.** The time derivative that SPIDER reports must be the one the time stepper integrates. A unit or scaling slip in the reported value, or a gross sign flip, makes the reported rate disagree with the trajectory without an error message.

**What it tests.** A macro step is the interval between 2 outputs; here it is 10 years. The test evaluates the reported dS/dt of the blackbody50 run (the standard 50-node test run, `tests/opts/blackbody50.opts`) against the finite-difference slope of the outputs at 10 and 20 yr. At each node, it asserts cooling (dS/dt < 0). It also bounds the largest |dS/dt| between 1e-12 and 1e-4 J/kg/K/s. The run gives about 2e-8 J/kg/K/s; the same rate, per year instead of per second, is about 0.7 and fails the upper bound. Sibling test `test_cooling_sign_structure_and_finiteness` checks that radiogenic and tidal source arrays remain zero and that entropy declines smoothly in the upper molten layer.

**How we know the right answer.** In the limit of small timesteps, the discrete difference between output snapshots approaches the instantaneous time derivative. The test asserts that the reported derivative matches the finite-difference rate to rel 2e-2 at the staggered nodes (cell centres). The observed difference is 0.43 to 0.65 percent, the truncation error of the 10-year slope.

**Why it matters.** The right-hand side assembly provides the core time derivative that PETSc integrates to advance mantle thermal evolution in SPIDER.

**Known limit.** The trajectory comes from the same right-hand side that reports dS/dt, so a wrong right-hand side gives a consistent wrong trajectory and passes; dS/dt is not compared with an independent physical value. The run has no heating, so a dropped heating term cannot show. Finite differencing over 10-year intervals adds a truncation error of up to 0.65 percent.

![Largest reported dS/dt magnitude of the run against the asserted window](../assets/validation/rhs_dsdt_finite_difference.svg#only-light){ width="80%" }
![Largest reported dS/dt magnitude of the run against the asserted window](../assets/validation/rhs_dsdt_finite_difference_dark.svg#only-dark){ width="80%" }

**How to read the plot.** The y-axis is the largest cooling rate |dS/dt| of the run in J/kg/K/s, on a log scale. The circle is this asserted value, the mean of the 10 and 20 yr outputs, shown to 1 significant digit. The grey band is the asserted window from 1e-12 to 1e-4 J/kg/K/s. The node profiles are not drawn, because they move by about 7e-4 (relative) between the macOS and Linux builds. The main comparison, with the slope of the specific entropy S between the outputs to relative 2e-2 at every node, is not drawn either. A pass means that the circle lies in the grey band.

??? info "Test details"
    - Reference: Analytical self-consistency: the reported dS/dt matches the finite-difference slope of consecutive outputs over 10-year macro steps.
    - Tolerance: rel 2e-2 at every staggered node (observed at most 0.65 percent, midpoint rule over 10 years).
    - Test id: `tests/test_rhs.py::test_reported_dsdt_matches_finite_difference_of_outputs`
    - Command: `make`, then `pytest -o addopts= tests/test_rhs.py::test_reported_dsdt_matches_finite_difference_of_outputs` (add `--validation-plots` to write the plot pair)
    - Companion test: `tests/test_rhs.py::test_cooling_sign_structure_and_finiteness` asserts cooling signs and finiteness of time derivatives.

## Related code

- `rhs.c`: `RHSFunction`.
- `tests/test_rhs.py`: `test_reported_dsdt_matches_finite_difference_of_outputs`, `test_cooling_sign_structure_and_finiteness`.
