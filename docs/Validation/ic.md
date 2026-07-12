# ic.c: Initial condition

**Source under test**: `ic.c`

**Reference-pinned test**: `tests/test_ic.py::test_prescribed_adiabat_entropy_sets_the_initial_profile`

**Anchor**: Analytical limit: the initial condition prescribes the adiabat entropy (2600 J/kg/K at the top staggered node) with the configured small gradient ramp.

**Tolerance**: Exact pin at the top node; the profile mean is bounded by the |ic_dsdr| times mantle depth ramp budget.

**Discrimination guards**: A run with ic_adiabat_entropy = 2400 shifts the profile by exactly 200 J/kg/K (wrong-value discrimination); cooling at later outputs breaks the initial flatness, confirming the IC is not a fixed point of the output pipeline.

The initial condition writes the prescribed adiabat onto the mesh. The top-node entropy, the integrated gradient ramp, and the response to a different prescribed value are pinned from the t = 0 output.

**Reference-pinned test**: `tests/test_ic.py::test_abundance_ic_realises_the_requested_inventory`

**Anchor**: Mass-balance identity through the initial partial-pressure solve: initial_kg equals the requested ppm of the mantle mass per volatile, and the realised reservoirs carry the requested hydrogen and carbon mole totals (conserved by the water and carbon dioxide reactions).

**Tolerance**: rel 1e-9 on the stored inventories and the H and C totals (observed agreement 3e-15).

**Discrimination guards**: The volatile oxygen total drifts by about 2e-3 relative against the request because the reactions exchange O with the melt's fO2 buffer, and the realised H2O reservoirs sit about 4e-3 relative off the bare request; the test thresholds sit at 1e-4, twenty-fold below the observed signals, while an inert reaction network would match the request to the 1e-9 the H and C totals meet.

**Reference-pinned test**: `tests/test_ic.py::test_ocean_moles_ic_converts_moles_to_mass`

**Anchor**: The OCEAN_MOLES constant of constants.c (7.68894973907177e22 mol per Earth ocean): initial_kg equals moles times OCEAN_MOLES times the volatile molar mass.

**Tolerance**: rel 1e-9 (closed-form product of stored constants).

**Discrimination guards**: Reading the CO2 inventory with the CO molar mass shifts the expected mass by 36 percent; positivity and scale bounds on the smallest inventory.
