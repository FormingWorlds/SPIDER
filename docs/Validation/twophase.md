# twophase.c: Global melt and solid mass bookkeeping

## What this page checks

This page checks two-phase mass bookkeeping in `twophase.c`, which tracks global magma ocean freezing.
`twophase.c` integrates local melt fractions over shell masses to compute total liquid and solid mantle masses.
Validation means that we check global melt fractions against analytical mass-weighted sums and mass closure.
If two-phase bookkeeping is wrong, global melt fractions and mantle phase inventories are incorrect.
The text below details the check, its tolerance, and its test command.

## Global melt fraction is the mass-weighted profile mean

**Why this check exists.** Mass sum routines can omit geometric shell weighting, confuse node centers with edges, or violate mass balance. A bug in mass bookkeeping produces inaccurate global melt inventories during cooling.

**What it tests.** The test evaluates the analytical identity: the global melt fraction equals the liquid mass Mliq over the mantle mass Mmantle, and the mass-weighted mean of the melt fraction at the staggered nodes (cell centres). It checks a part-solidified 1200-year state. An unweighted profile mean differs by more than 1e-3, confirming that the test guards spatial weighting. Global melt fraction must lie between 0 and 1 and, at 1200 yr, between 0.2 and 0.9. Sibling tests verify mantle mass closure Mliq + Msol = Mmantle at every output to rel 1e-12 (`test_mantle_mass_closure_at_every_output_time`), and monotone solidification under cooling (`test_solidification_proceeds_monotonically_under_cooling`).

**How we know the right answer.** By mass balance, total melt mass divided by mantle mass must identically equal the mass-weighted mean of the radial melt fraction profile. Both identities match to rel 1e-10.

**Why it matters.** Global melt fraction and mantle phase masses are primary outputs read by PROTEUS (`M_mantle_liquid`, `M_mantle_solid`, and `Phi_global` in `ReadSPIDER` of `spider.py`).

**Known limit.** The identity compares 2 code paths that share the code's own `mass_s` and `phi_s`, so a wrong shell mass or melt fraction passes.

![Reported global melt fraction at 1200 yr against its 3 definitions](../assets/validation/twophase_global_melt_fraction.svg#only-light){ width="80%" }
![Reported global melt fraction at 1200 yr against its 3 definitions](../assets/validation/twophase_global_melt_fraction_dark.svg#only-dark){ width="80%" }

**How to read the plot.** The circles are the global melt fraction at 1200 yr in 4 forms. The first 3 are the reported `phi_global`, the liquid over mantle mass Mliq / Mmantle, and the mass-weighted mean of the staggered-node melt fraction. The test requires these 3 to agree (relative 1e-10), and the unweighted mean to be more than 1e-3 away. The grey band is the reported value $\pm$ 1e-3. Values are shown to 2 significant digits, because the run output moves by about 2.5e-6 between builds of the PETSc library. A pass means that the first 3 circles lie in the band and the last outside it; the test checks the unrounded values.

??? info "Test details"
    - Reference: Analytical identity: the global melt fraction equals Mliq/Mmantle and the mass-weighted mean of the staggered melt-fraction profile.
    - Tolerance: rel 1e-10 on both identities at the part-solidified 1200-year state.
    - Test id: `tests/test_twophase.py::test_global_melt_fraction_is_the_mass_weighted_profile_mean`
    - Command: `make`, then `pytest -o addopts= tests/test_twophase.py::test_global_melt_fraction_is_the_mass_weighted_profile_mean` (add `--validation-plots` to write the plot pair)
    - Companion test: `tests/test_twophase.py::test_mantle_mass_closure_at_every_output_time` asserts mass conservation closure Mliq + Msol = Mmantle across outputs.

## Related code

- `twophase.c`: `set_Mliq`, `set_Msol`, `set_dMliqdt`, `set_rheological_front`.
- `tests/test_twophase.py`: `test_global_melt_fraction_is_the_mass_weighted_profile_mean`, `test_mantle_mass_closure_at_every_output_time`, `test_solidification_proceeds_monotonically_under_cooling`.
