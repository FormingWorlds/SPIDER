# rheologicalfront.c: Rheological front tracking

## What this page checks

This page checks front tracking in `rheologicalfront.c`, which locates the solidification boundary.
`rheologicalfront.c` detects the critical melt fraction threshold where mantle rheology shifts from liquid-like to solid-like behavior.
Validation means that we check reported front indices and depths against independent crossings of the melt fraction profile.
If front tracking fails, the dynamic boundary between convective magma ocean and solid mantle is misplaced.
The section below details the validation check, its tolerance, and its test command.

## Front location is consistent with melt fraction profile

**Why this check exists.** Front finding routines can misplace grid crossings, apply incorrect search directions, or invert coordinate signs. A bug in front tracking misidentifies the boundary between solid and fluid mantle.

**What it tests.** The test evaluates analytical self-consistency: reported front index matches the phi_critical = 0.4 crossing of the melt-fraction profile, and depth equals surface radius minus front radius. It checks that the front depth is positive and bounded by mantle depth, with front pressure located inside the mantle range. Sibling tests pin the un-formed-front limit at t = 0, where the front reports the core-mantle boundary by convention (`test_unformed_front_reports_the_cmb_at_the_fully_molten_start`), and upward migration during bottom-up solidification (`test_front_rises_from_the_cmb_as_the_mantle_solidifies`).

**How we know the right answer.** The front location is recomputed independently from the discrete melt-fraction profile and geometry arrays. The depth identity matches to rel 1e-6, and the index matches to one node of the recomputed crossing.

**Why it matters.** The rheological front marks the viscosity transition that PROTEUS reads as dynamic front depth (`RF_depth` in `ReadSPIDER` of `spider.py`).

**Known limit.** Due to discrete spatial grid intervals, the front index is resolved to one node of the interpolated profile crossing.

??? info "Test details"
    - Reference: Analytical self-consistency: the reported front index matches the phi_critical = 0.4 crossing of the melt-fraction profile, and the depth equals the surface radius minus the front radius.
    - Tolerance: Front index within one node of the recomputed crossing; rel 1e-6 on the depth identity.
    - Test id: `tests/test_rheologicalfront.py::test_front_location_is_consistent_with_melt_fraction_profile`
    - Command: `make`, then `pytest -o addopts= tests/test_rheologicalfront.py::test_front_location_is_consistent_with_melt_fraction_profile`
    - Companion test: `tests/test_rheologicalfront.py::test_front_rises_from_the_cmb_as_the_mantle_solidifies` verifies upward front migration as the mantle solidifies.

## Related code

- `rheologicalfront.c`: `get_crossover_index`.
- `tests/test_rheologicalfront.py`: `test_front_location_is_consistent_with_melt_fraction_profile`, `test_front_rises_from_the_cmb_as_the_mantle_solidifies`, `test_unformed_front_reports_the_cmb_at_the_fully_molten_start`.
