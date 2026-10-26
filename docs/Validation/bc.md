# bc.c: Boundary conditions

## What this page checks

This page checks the boundary condition implementations in `bc.c`, which control surface and bottom boundaries.
The boundary condition routines specify how energy and entropy enter, or leave, the planetary mantle.
Validation means that we test boundary condition options against analytical identities, and against prescribed inputs.
If boundary condition dispatch fails, energy conservation is violated at the surface, or at the core-mantle boundary.
The sections below detail two validation cases, their tolerances, and their test commands.

## Prescribed-flux BC echoes value and inverts emissivity

**Why this check exists.** Surface boundary routines can misinterpret options, swap boundary condition flags, or miscalculate equivalent emissivities. A bug in prescribed boundary dispatch causes the interior to use an incorrect surface heat flux, without failing explicitly.

**What it tests.** The test evaluates boundary condition SURFACE_BC 4, where the surface flux equals the prescribed value. The reported emissivity must equal the grey-body inversion value. The test guards against wrong dispatch, confirming that the grey-body flux at the surface temperature differs from the prescribed value by more than 10 percent, and the emissivity differs from 1 by more than 0.5. The flux must be positive, and lie between 1e2 and 1e9 W/m^2. Sibling test `test_mantle_cools_from_the_top_between_surface_and_cmb` asserts temperature ordering across the mantle, and near-zero surface pressure.

**How we know the right answer.** Under SURFACE_BC 4, reproducing the prescribed flux is an analytical identity. The test checks the flux echo to rel 1e-9, and the inverted emissivity to rel 1e-6.

**Why it matters.** PROTEUS passes the atmospheric radiative flux into SPIDER using option `-SURFACE_BC 4` and `-surface_bc_value`, so SPIDER must echo this flux exactly.

**Known limit.** This test validates prescribed flux injection, but does not test coupled atmospheric radiative transfer within SPIDER itself.

??? info "Test details"
    - Reference: Analytical identity: with SURFACE_BC 4 the surface flux equals the prescribed value, and the reported emissivity is its grey-body inversion.
    - Tolerance: rel 1e-9 on the flux echo; rel 1e-6 on the emissivity inversion.
    - Test id: `tests/test_bc.py::test_prescribed_flux_bc_echoes_value_and_inverts_emissivity`
    - Command: `make`, then `pytest -o addopts= tests/test_bc.py::test_prescribed_flux_bc_echoes_value_and_inverts_emissivity`
    - Companion test: `tests/test_bc.py::test_mantle_cools_from_the_top_between_surface_and_cmb` verifies that the core-mantle boundary remains hotter than the surface.

## Constant-entropy BC pins the initial surface

**Why this check exists.** Fixed boundary values can be overwritten by initial rebalancing steps, or by stencil operations. If the surface boundary assignment fails, the mantle profile starts from an uncalibrated thermodynamic state.

**What it tests.** The test evaluates the constant-entropy boundary option, which writes `ic_surface_entropy` (2550 J/kg/K) onto the surface basic node. This value is preserved through the steady-state energy solve into the initial output. The test discriminates this setting against the default configuration surface value (2599.7 J/kg/K from the 2600 adiabat), which sits about 50 J/kg/K away. Sibling test `test_prescribed_core_flux_slows_cmb_cooling` checks CORE_BC dispatch, CMB entropy difference, and doubled CMB heat flux.

**How we know the right answer.** Preserving a specified boundary value is an exact identity. Because the value is assigned directly, it matches to rel 1e-10.

**Why it matters.** Setting fixed surface or core entropies allows controlled numerical experiments and comparisons with simplified interior profiles.

**Known limit.** For constant-entropy boundary conditions, the surface value is assigned directly rather than determined by a physical flux balance.

??? info "Test details"
    - Reference: Analytical identity: the constant-entropy boundary writes ic_surface_entropy (2550 J/kg/K) onto the surface basic node, preserved through the steady-state energy solve into the initial output.
    - Tolerance: rel 1e-10 (assigned, not solved).
    - Test id: `tests/test_bc.py::test_constant_entropy_bc_pins_the_initial_surface`
    - Command: `make`, then `pytest -o addopts= tests/test_bc.py::test_constant_entropy_bc_pins_the_initial_surface`
    - Companion test: `tests/test_bc.py::test_prescribed_core_flux_slows_cmb_cooling` verifies that core heat flux slows cooling at the core-mantle boundary.

## Related code

- `bc.c`: `set_surface_flux_from_atmosphere`, `set_surface_entropy_constant`, `set_cmb_entropy_constant`.
- `tests/test_bc.py`: `test_prescribed_flux_bc_echoes_value_and_inverts_emissivity`, `test_constant_entropy_bc_pins_the_initial_surface`.
