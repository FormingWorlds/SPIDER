# ic.c: Initial condition

## What this page checks

This page checks initial condition setup in `ic.c`, which builds starting mantle and volatile states.
`ic.c` establishes the initial adiabat profile, sets volatile inventories from mass fractions, and converts ocean-mole specifications.
Validation means that we compare initial profiles and chemical inventories against analytical limits and mass-balance identities.
If initial conditions are set incorrectly, simulations start from wrong thermal profiles, or from incorrect volatile inventories.
The sections below detail three validation cases, their tolerances, and their test commands.

## Prescribed adiabat entropy sets the initial profile

**Why this check exists.** Initial condition (IC) routines can misinterpret input entropy parameters or fail to write values to the staggered mesh nodes; a gradient ramp error shows only if the profile mean leaves 2600 to 2628.7 J/kg/K. A bug in initial condition setup shifts the starting temperature structure, and the later cooling is wrong too.

**What it tests.** The test evaluates the prescribed adiabat entropy (2600 J/kg/K at the top staggered node) with the configured gradient ramp. The profile mean lies between the adiabat entropy and that value plus |ic_dsdr| times mantle depth. A run with ic_adiabat_entropy = 2400 shifts the mean by 200 J/kg/K to rel 1e-9, guarding against ignored option inputs. Entropy is positive, with its mean between 1e3 and 1e4 J/kg/K. Top-node entropy matches at t = 0 to rel 1e-3 (observed exact). Sibling test `test_initial_adiabat_is_nearly_flat_until_cooling_imprints_structure` checks that subsequent cooling imprints thermal structure.

**How we know the right answer.** Prescribing an adiabat provides an analytical limit, which defines an idealized reference. The top-node value, and the mean profile shift, match exact option arithmetic.

**Why it matters.** The initial adiabat sets the starting thermal state of the magma ocean. SPIDER integrates cooling forward from this baseline.

**Known limit.** The check tests initialization on the staggered grid, but does not benchmark external non-adiabatic initial profiles.

??? info "Test details"
    - Reference: Analytical limit: the initial condition prescribes the adiabat entropy (2600 J/kg/K at the top staggered node) with the configured small gradient ramp.
    - Tolerance: rel 1e-3 at the top node (observed exact); the profile mean lies between the adiabat entropy and that value plus |ic_dsdr| times the mantle depth; the 2400 J/kg/K run shifts the mean by 200 J/kg/K to rel 1e-9.
    - Test id: `tests/test_ic.py::test_prescribed_adiabat_entropy_sets_the_initial_profile`
    - Command: `make`, then `pytest -o addopts= tests/test_ic.py::test_prescribed_adiabat_entropy_sets_the_initial_profile`
    - Companion test: `tests/test_ic.py::test_initial_adiabat_is_nearly_flat_until_cooling_imprints_structure` verifies that cooling breaks initial profile uniformity.

## Abundance IC realises the requested inventory

**Why this check exists.** Volatile partition routines can lose element mass during initial solver iterations, or misapply ppm conversions. A bug in volatile setup gives wrong initial volatile budgets in the atmosphere and the interior.

**What it tests.** The test evaluates mass-balance closure through the initial partial-pressure solve. The quantity initial_kg equals requested ppm of mantle mass per volatile. Realised reservoirs hold requested hydrogen and carbon mole totals. Volatile oxygen drifts by about 2e-3 relative because reactions exchange O with the melt fO2 buffer, and realised H2O reservoirs sit about 3.6e-3 relative off bare requests. Discrimination thresholds sit at 1e-4, far below observed signals, while inert networks match to 1e-9.

**How we know the right answer.** Closed-system mass conservation requires total moles of conserved elements to match requested inputs. Stored inventories and H and C totals match to rel 1e-9 (observed below 1e-15).

**Why it matters.** SPIDER's own volatile partitioning starts from this allocation. PROTEUS leaves the volatile part of SPIDER unused and computes outgassing with its own modules.

**Known limit.** Volatile oxygen mass is not strictly conserved by volatile species alone because the melt iron buffer exchanges oxygen with dissolved gases.

??? info "Test details"
    - Reference: Mass-balance identity through the initial partial-pressure solve: initial_kg equals the requested ppm of the mantle mass per volatile, and the realised reservoirs carry the requested hydrogen and carbon mole totals (conserved by the water and carbon dioxide reactions).
    - Tolerance: rel 1e-9 on the stored inventories and the H and C totals (observed below 1e-15).
    - Test id: `tests/test_ic.py::test_abundance_ic_realises_the_requested_inventory`
    - Command: `make`, then `pytest -o addopts= tests/test_ic.py::test_abundance_ic_realises_the_requested_inventory`
    - Companion test: `tests/test_ic.py::test_abundance_and_ocean_mole_solves_agree` verifies consistency between abundance and ocean-mole initialization paths.

## Ocean-moles IC converts moles to mass

**Why this check exists.** Unit conversions from ocean equivalents can apply wrong molar masses, or miscalculate moles-to-mass constants. A conversion error scales volatile mass by large factors, leading to invalid atmospheric pressures.

**What it tests.** The test evaluates the OCEAN_MOLES constant of constants.c (7.68894973907177e22 mol per Earth ocean). It verifies that initial_kg equals moles times OCEAN_MOLES times volatile molar mass. Reading CO2 inventory with CO molar mass shifts expected mass by 36 percent, which guards against swapped species indices. The test checks positivity and scale bounds on CO2 inventory, the smallest in ocean equivalents (0.0087 oceans; H2 is smaller in mass).

**How we know the right answer.** Moles to mass conversion is a closed-form product of defined constants. The evaluated mass matches to rel 1e-9.

**Why it matters.** Setting volatile budgets in Earth ocean equivalents allows direct comparison with terrestrial water and carbon inventories in planetary models.

**Known limit.** The test uses its own copy of the OCEAN_MOLES constant of the source, so it checks the conversion, not the definition of the terrestrial ocean mass; a value that is wrong in both places passes.

??? info "Test details"
    - Reference: The OCEAN_MOLES constant of constants.c (7.68894973907177e22 mol per Earth ocean): initial_kg equals moles times OCEAN_MOLES times the volatile molar mass.
    - Tolerance: rel 1e-9 (closed-form product of stored constants).
    - Test id: `tests/test_ic.py::test_ocean_moles_ic_converts_moles_to_mass`
    - Command: `make`, then `pytest -o addopts= tests/test_ic.py::test_ocean_moles_ic_converts_moles_to_mass`
    - Companion test: `tests/test_ic.py::test_abundance_and_ocean_mole_solves_agree` confirms that the ocean-mole and ppm abundance formulations give the same partial pressures to rel 5e-3.

## Related code

- `ic.c`: `set_ic_interior`, `set_ic_atmosphere`, `set_ic_interior_entropy`, `set_ic_atmosphere_from_initial_total_abundance`, `set_ic_atmosphere_from_ocean_moles`.
- `tests/test_ic.py`: `test_prescribed_adiabat_entropy_sets_the_initial_profile`, `test_abundance_ic_realises_the_requested_inventory`, `test_ocean_moles_ic_converts_moles_to_mass`.
