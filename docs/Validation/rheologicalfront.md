# rheologicalfront.c: Rheological front tracking

**Source under test**: `rheologicalfront.c`

**Reference-pinned test**: `tests/test_rheologicalfront.py::test_front_location_is_consistent_with_melt_fraction_profile`

**Anchor**: Analytical self-consistency: the reported front index matches the phi_critical = 0.4 crossing of the melt-fraction profile, and the depth equals the surface radius minus the front radius.

**Tolerance**: Front index within one node of the recomputed crossing; rel 1e-6 on the depth identity.

**Discrimination guards**: Depth positivity and the mantle-depth bound; front pressure within the mantle range; the un-formed-front limit at t = 0 reports the core-mantle boundary by convention (pinned as the limit-input contract); the front migrates upward as the mantle solidifies bottom-up.

The rheological front marks the transition between the low- and high-viscosity regimes that PROTEUS reads as the dynamic front depth. Its location is recomputed independently from the melt-fraction profile and the geometry arrays of the same output.
