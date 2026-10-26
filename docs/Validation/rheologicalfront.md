# rheologicalfront.c: Rheological front tracking

## What this page checks

This page checks front tracking in `rheologicalfront.c`, which locates the solidification boundary.
`rheologicalfront.c` detects the critical melt fraction threshold where mantle rheology shifts from liquid-like to solid-like behavior.
Validation means that we check reported front indices and depths against independent crossings of the melt fraction profile.
If front tracking fails, the dynamic boundary between convective magma ocean and solid mantle is misplaced.
The section below details the validation check, its tolerance, and its test command.

## Front location is consistent with melt fraction profile

**Why this check exists.** The front depth must follow from the front radius, and the front must lie inside the mantle. A wrong depth formula, an inverted coordinate sign or a front outside the mantle gives a wrong front without an error message.

**What it tests.** The test evaluates analytical self-consistency: reported front index matches the phi_critical = 0.4 crossing of the melt-fraction profile, and depth equals surface radius minus front radius. It checks that the front depth is positive and bounded by mantle depth, with front pressure located inside the mantle range. Sibling tests pin the un-formed-front limit at t = 0, where the front reports the core-mantle boundary by convention (`test_unformed_front_reports_the_cmb_at_the_fully_molten_start`), and upward migration during bottom-up solidification (`test_front_rises_from_the_cmb_as_the_mantle_solidifies`).

**How we know the right answer.** The test recomputes the front location in Python, with the same rule, from the melt-fraction profile and the geometry arrays. The depth identity matches to rel 1e-6, and the index matches to one node of the recomputed crossing.

**Why it matters.** The front block marks where the mantle turns from mostly molten to mostly solid. PROTEUS reads neither its index nor its depth: it takes `Phi_global` from the same output block and `RF_depth` from the dynamic front.

**Known limit.** The test recomputes the crossing with the same rule as `get_crossover_index` and allows one node of difference, so a one-node misplacement passes; the code takes the first node below `phi_critical` without interpolation. PROTEUS takes `RF_depth` from the dynamic front (`rheological_front_dynamic`, the crossing of the convection regime flag at 1.5, between inviscid (2) and viscous (1) convection), which this test does not cover.

![Radii of the 2 nodes on each side of the critical melt fraction and of the reported front at 1200 yr](../assets/validation/rheologicalfront_location.svg#only-light){ width="80%" }
![Radii of the 2 nodes on each side of the critical melt fraction and of the reported front at 1200 yr](../assets/validation/rheologicalfront_location_dark.svg#only-dark){ width="80%" }

**How to read the plot.** The y-axis is the radius, shown to 3 significant digits. The squares are the 2 staggered nodes (cell centres of the mesh) that the test finds itself at 1200 yr. They are the last node at or above the critical melt fraction $\phi_c = 0.4$ (0.403), and the first node below it (0.3995). The circle is the asserted front radius, the planet radius minus the reported depth. The melt fractions are not drawn: the first node is only 4.5e-4 below $\phi_c$, so a rounded value is not stable between builds. A pass means that the circle lies at most 1 node from the squares; in this run it lies between them.

??? info "Test details"
    - Reference: Analytical self-consistency: the reported front index matches the phi_critical = 0.4 crossing of the melt-fraction profile, and the depth equals the surface radius minus the front radius.
    - Tolerance: Front index within one node of the recomputed crossing; rel 1e-6 on the depth identity.
    - Test id: `tests/test_rheologicalfront.py::test_front_location_is_consistent_with_melt_fraction_profile`
    - Command: `make`, then `pytest -o addopts= tests/test_rheologicalfront.py::test_front_location_is_consistent_with_melt_fraction_profile` (add `--validation-plots` to write the plot pair)
    - Companion test: `tests/test_rheologicalfront.py::test_front_rises_from_the_cmb_as_the_mantle_solidifies` verifies upward front migration as the mantle solidifies.

## Related code

- `rheologicalfront.c`: `get_crossover_index`.
- `tests/test_rheologicalfront.py`: `test_front_location_is_consistent_with_melt_fraction_profile`, `test_front_rises_from_the_cmb_as_the_mantle_solidifies`, `test_unformed_front_reports_the_cmb_at_the_fully_molten_start`.
