# twophase.c: Global melt and solid mass bookkeeping

**Source under test**: `twophase.c`

**Reference-pinned test**: `tests/test_twophase.py::test_global_melt_fraction_is_the_mass_weighted_profile_mean`

**Anchor**: Analytical identity: the global melt fraction equals Mliq/Mmantle and the mass-weighted mean of the staggered melt-fraction profile.

**Tolerance**: rel 1e-10 on both identities at the part-solidified 1200-year state.

**Discrimination guards**: An unweighted profile mean differs beyond tolerance (weighting guard); mantle mass closure Mliq + Msol = Mmantle holds at every output to rel 1e-12; solidification is monotone under cooling with the mantle mass constant.

The two-phase bookkeeping integrates the melt distribution into the global masses PROTEUS consumes. Closure, monotone solidification, and the equivalence of the three melt-fraction definitions are pinned across the full frozen-reference run.
