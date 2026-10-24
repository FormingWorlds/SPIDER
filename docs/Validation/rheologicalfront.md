# rheologicalfront.c: Rheological front tracking

**Source under test**: `rheologicalfront.c`

## Cases

### Front location is consistent with melt fraction profile

**Reference-pinned test**: `tests/test_rheologicalfront.py::test_front_location_is_consistent_with_melt_fraction_profile`

**Reference**: Analytical self-consistency: the reported front index matches the phi_critical = 0.4 crossing of the melt-fraction profile, and the depth equals the surface radius minus the front radius.

**Tolerance**: Front index within one node of the recomputed crossing; rel 1e-6 on the depth identity.

**Command**: `make`, then `pytest -o addopts= tests/test_rheologicalfront.py::test_front_location_is_consistent_with_melt_fraction_profile`

**Discrimination guards**: Depth positivity and the mantle-depth bound; front pressure within the mantle range. Sibling tests in the same file pin the un-formed-front limit at t = 0, where the front reports the core-mantle boundary by convention (`test_unformed_front_reports_the_cmb_at_the_fully_molten_start`), and the upward migration of the front as the mantle solidifies bottom-up (`test_front_rises_from_the_cmb_as_the_mantle_solidifies`).

The rheological front marks the transition between the low- and high-viscosity regimes that PROTEUS reads as the dynamic front depth. Its location is recomputed independently from the melt-fraction profile and the geometry arrays of the same output.
