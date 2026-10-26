# rhs.c: Entropy time-derivative assembly

## What this page checks

This page checks the right-hand side time-derivative assembly in `rhs.c`, which governs thermal evolution.
`rhs.c` compiles flux divergences and internal heating source terms into local entropy tendencies dS/dt.
Validation means that we check reported time derivatives against finite-difference slopes between consecutive output snapshots.
If right-hand side evaluation is incorrect, the numerical timestepper integrates along an erroneous trajectory.
The section below details the validation check, its tolerance, and its test command.

## Reported dS/dt matches finite difference of outputs

**Why this check exists.** Time derivative assembly can misplace spatial differencing weights, drop heating source terms, or reverse flux divergence signs. An error in derivative evaluation causes unphysical energy drift during timestepping.

**What it tests.** The test evaluates the reported dS/dt against the finite-difference slope of consecutive outputs over 10-year macro steps. It asserts cooling signs at each node, and bounds the largest |dS/dt| between 1e-12 and 1e-4 J/kg/K/s. This bound rejects unscaled annual rates, while finite differencing catches nondimensional values (around 3e-5 here). Sibling test `test_cooling_sign_structure_and_finiteness` checks that radiogenic and tidal source arrays remain zero and that entropy declines smoothly in the upper molten layer.

**How we know the right answer.** In the limit of small timesteps, the discrete difference between output snapshots approaches the instantaneous time derivative. The reported derivative matches the finite-difference rate to rel 2e-2 at staggered nodes (observed at most 0.65 percent).

**Why it matters.** The right-hand side assembly provides the core time derivative that PETSc integrates to advance mantle thermal evolution in SPIDER.

![Reported dS/dt and the slope of S between the 10 and 20 yr outputs against radius, and their relative difference with the tolerance](../assets/validation/rhs_dsdt_finite_difference.svg#only-light){ width="80%" }
![Reported dS/dt and the slope of S between the 10 and 20 yr outputs against radius, and their relative difference with the tolerance](../assets/validation/rhs_dsdt_finite_difference_dark.svg#only-dark){ width="80%" }

**How to read the plot.** Top: the cooling rate -dS/dt that rhs.c reports, as the mean of the 10 and 20 yr outputs (line), and the slope of the entropy between these outputs (dashed), at every staggered node of the blackbody50 run. Bottom: their relative difference per node (dots) and the tolerance of the assertion (dashed); the largest difference is 0.65 percent.

**Known limit.** Discrete finite differencing over 10-year intervals introduces numerical truncation error of up to 0.65 percent relative to instantaneous continuous derivatives.

??? info "Test details"
    - Reference: Analytical self-consistency: the reported dS/dt matches the finite-difference slope of consecutive outputs over 10-year macro steps.
    - Tolerance: rel 2e-2 at every staggered node (observed at most 0.65 percent, midpoint rule over 10 years).
    - Test id: `tests/test_rhs.py::test_reported_dsdt_matches_finite_difference_of_outputs`
    - Command: `make`, then `pytest -o addopts= tests/test_rhs.py::test_reported_dsdt_matches_finite_difference_of_outputs` (add `--validation-plots` to write the plot pair)
    - Companion test: `tests/test_rhs.py::test_cooling_sign_structure_and_finiteness` asserts cooling signs and finiteness of time derivatives.

## Related code

- `rhs.c`: `RHSFunction`.
- `tests/test_rhs.py`: `test_reported_dsdt_matches_finite_difference_of_outputs`, `test_cooling_sign_structure_and_finiteness`.
