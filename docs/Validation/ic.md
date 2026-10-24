# ic.c: Initial condition

**Source under test**: `ic.c`

## Cases

### Prescribed adiabat entropy sets the initial profile

**Reference-pinned test**: `tests/test_ic.py::test_prescribed_adiabat_entropy_sets_the_initial_profile`

**Reference**: Analytical limit: the initial condition prescribes the adiabat entropy (2600 J/kg/K at the top staggered node) with the configured small gradient ramp.

**Tolerance**: rel 1e-3 at the top node (observed exact); the profile mean lies between the adiabat entropy and that value plus |ic_dsdr| times the mantle depth; the 2400 J/kg/K run shifts the mean by 200 J/kg/K to rel 1e-9.

**Command**: `make`, then `pytest -o addopts= tests/test_ic.py::test_prescribed_adiabat_entropy_sets_the_initial_profile`

**Discrimination guards**: A run with ic_adiabat_entropy = 2400 shifts the profile by exactly 200 J/kg/K (wrong-value discrimination); the entropy is positive and its mean between 1e3 and 1e4 J/kg/K. The sibling test `test_initial_adiabat_is_nearly_flat_until_cooling_imprints_structure` (same file) checks that cooling at later outputs breaks the initial flatness, so the IC is not a fixed point of the output pipeline.

The initial condition writes the prescribed adiabat onto the mesh. The top-node entropy, the integrated gradient ramp, and the response to a different prescribed value are pinned from the t = 0 output.

### Abundance IC realises the requested inventory

**Reference-pinned test**: `tests/test_ic.py::test_abundance_ic_realises_the_requested_inventory`

**Reference**: Mass-balance identity through the initial partial-pressure solve: initial_kg equals the requested ppm of the mantle mass per volatile, and the realised reservoirs carry the requested hydrogen and carbon mole totals (conserved by the water and carbon dioxide reactions).

**Tolerance**: rel 1e-9 on the stored inventories and the H and C totals (observed below 1e-15).

**Command**: `make`, then `pytest -o addopts= tests/test_ic.py::test_abundance_ic_realises_the_requested_inventory`

**Discrimination guards**: The volatile oxygen total drifts by about 2e-3 relative against the request because the reactions exchange O with the melt's fO2 buffer, and the realised H2O reservoirs sit about 3.6e-3 relative off the bare request; the test thresholds sit at 1e-4, at least twenty-fold below the observed signals, while an inert reaction network would match the request to the 1e-9 the H and C totals meet.

### Ocean-moles IC converts moles to mass

**Reference-pinned test**: `tests/test_ic.py::test_ocean_moles_ic_converts_moles_to_mass`

**Reference**: The OCEAN_MOLES constant of constants.c (7.68894973907177e22 mol per Earth ocean): initial_kg equals moles times OCEAN_MOLES times the volatile molar mass.

**Tolerance**: rel 1e-9 (closed-form product of stored constants).

**Command**: `make`, then `pytest -o addopts= tests/test_ic.py::test_ocean_moles_ic_converts_moles_to_mass`

**Discrimination guards**: Reading the CO2 inventory with the CO molar mass shifts the expected mass by 36 percent; positivity and scale bounds on the CO2 inventory, the smallest in ocean equivalents (0.0087 oceans; H2 is smaller in mass).
