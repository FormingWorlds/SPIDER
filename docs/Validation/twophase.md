# twophase.c: Global melt and solid mass bookkeeping

**Source under test**: `twophase.c`

## Cases

### Global melt fraction is the mass-weighted profile mean

**Reference-pinned test**: `tests/test_twophase.py::test_global_melt_fraction_is_the_mass_weighted_profile_mean`

**Reference**: Analytical identity: the global melt fraction equals Mliq/Mmantle and the mass-weighted mean of the staggered melt-fraction profile.

**Tolerance**: rel 1e-10 on both identities at the part-solidified 1200-year state.

**Command**: `make`, then `pytest -o addopts= tests/test_twophase.py::test_global_melt_fraction_is_the_mass_weighted_profile_mean`

**Discrimination guards**: An unweighted profile mean differs by more than 1e-3 (weighting guard); the global melt fraction lies between 0 and 1 and, at 1200 yr, between 0.2 and 0.9. Sibling tests in the same file check the mantle mass closure Mliq + Msol = Mmantle at every output to rel 1e-12 (`test_mantle_mass_closure_at_every_output_time`) and the monotone solidification under cooling with the mantle mass constant (`test_solidification_proceeds_monotonically_under_cooling`).

The two-phase bookkeeping integrates the melt distribution into the global masses PROTEUS consumes. Closure, monotone solidification, and the equivalence of the three melt-fraction definitions are pinned across the full frozen-reference run.
