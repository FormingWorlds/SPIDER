# energy.c: Energy fluxes

## What this page checks

This page checks energy flux assembly and internal heating routines in `energy.c`, which control mantle energy transport.
The energy module calculates convective, conductive, and diffusive fluxes, alongside radiogenic and tidal heating.
Validation means that we test flux assembly against analytical superposition limits, decay laws, and steady balances.
If flux calculation or source terms are wrong, mantle cooling rates and core heat extraction are corrupted.
Coupled planetary simulations in PROTEUS then evolve along incorrect thermal paths.
The sections below detail three validation cases, their tolerances, and their test commands.

## Disabled transport mechanisms carry zero flux

**Why this check exists.** Runtime configuration flags can fail to disconnect disabled flux routines, or leak residual values into total energy balances. A failure in flux superposition produces incorrect thermal gradients without raising an error.

**What it tests.** The test evaluates the flux superposition architecture when specific transport terms are switched off. A disabled transport mechanism must hold zero flux, within abs 1e-20 W/m^2, which is at least 17 decades below active fluxes. With conduction off, convection yields 9e8 to 2e9 W/m^2. In a conduction-only run, conduction yields 1.9e-3 to 1.3e-2 W/m^2. Total flux equals conductive flux to rel 1e-12 at every interior node. The surface node differs by more than 1e3 W/m^2.

**How we know the right answer.** Superposition of linear or disjoint flux mechanisms is an analytical identity. Inactive transport terms must vanish to rounding precision, while active terms reproduce isolated components.

**Why it matters.** SPIDER models mantle cooling by summing convective and conductive transport. PROTEUS relies on accurate interior fluxes to determine planetary thermal evolution.

**Known limit.** For the conduction-only test, the identity holds at interior nodes only, because the surface node transmits the grey-body boundary flux.

??? info "Test details"
    - Reference: Analytical limit: a disabled transport mechanism carries zero flux, and with only conduction enabled the total flux equals the conductive flux at every node except the surface node, which carries the grey-body boundary flux.
    - Tolerance: abs 1e-20 W/m^2 on the disabled fluxes, at least 17 decades below the active fluxes (convection 9e8 to 2e9 W/m^2 with conduction off; conduction 1.9e-3 to 1.3e-2 W/m^2 in the conduction-only run); rel 1e-12 on the conduction-only identity, and the surface node differs by more than 1e3 W/m^2.
    - Test id: `tests/test_energy.py::test_disabled_transport_mechanisms_carry_zero_flux`
    - Command: `make`, then `pytest -o addopts= tests/test_energy.py::test_disabled_transport_mechanisms_carry_zero_flux`
    - Companion test: `tests/test_energy.py::test_total_flux_assembles_from_transport_components` verifies that total flux equals the sum of transport components at interior basic nodes.

## Radiogenic heating pins two isotope decay

**Why this check exists.** Radioactive decay models can apply incorrect decay constants, confuse isotope abundances, or miscalculate exponential time evolution. A bug in heating terms leads to wrong internal heat production over geological timescales.

**What it tests.** The test evaluates radiogenic heating as the sum of concentration times abundance times heat production over isotopes, decaying as 2^(-(t - t0)/half_life). A two-isotope test configuration with 100-year and 200-year half-lives pins the sum at t = 0, and checks the weighted decay factor 0.2506 after 200 years. A dropped isotope shifts the initial sum by 2.4e-3 relative. The two-isotope factor is discriminated from single-isotope values 0.25 and 0.5, and from the no-decay value 1.0.

**How we know the right answer.** Radioactive decay follows the analytical exponential decay law. The initial sum is checked to rel 1e-6, and the combined decay factor matches to rel 1e-4.

**Why it matters.** Radiogenic decay supplies essential internal heating that delays mantle freezing. PROTEUS reads integrated radiogenic heating `F_radio` (in `ReadSPIDER` of `spider.py`) into whole-planet energy budgets.

**Known limit.** This test pins decay mechanics for synthetic isotopes, but does not benchmark geological isotope concentrations.

??? info "Test details"
    - Reference: Analytical limit: radiogenic heating is the sum over isotopes of concentration times abundance times heat production, decaying as 2^(-(t - t0)/half_life). A two-isotope configuration with 100-year and 200-year half-lives pins the sum at t = 0 and the weighted decay factor 0.2506 after 200 years.
    - Tolerance: rel 1e-6 on the initial sum, rel 1e-4 on the decay factor.
    - Test id: `tests/test_energy.py::test_radiogenic_heating_pins_two_isotope_decay`
    - Command: `make`, then `pytest -o addopts= tests/test_energy.py::test_radiogenic_heating_pins_two_isotope_decay`
    - Companion test: `tests/test_energy.py::test_prescribed_tidal_heating_is_uniform_and_steady` verifies uniform spatial distribution of tidal heating.

## Steady-state IC balances interior and surface

**Why this check exists.** Steady-state solvers can terminate at false equilibria, or fail to balance heat flow across layers. An uncalibrated initial profile introduces unphysical thermal transients at the start of a simulation.

**What it tests.** The test evaluates the steady-state initial condition, which equalises energy flow through every basic node, and closes the surface radiation balance sigma (T_surf^4 - teqm^4) with the Stefan-Boltzmann constant of constants.c. A T^3 exponent slip misses the surface flux by roughly a factor of the surface temperature (about 2000 here).

**How we know the right answer.** Conservation of energy in steady state requires equal energy flow through every mantle shell, and balanced radiation at the surface. Energy-flow relative spread remains below 1e-8 (observed 2e-11), and the grey-body balance matches to rel 1e-5.

**Why it matters.** Steady initial conditions provide smooth starting states for long-term thermal simulations in PROTEUS, avoiding initial shock oscillations.

**Known limit.** The test uses the Stefan-Boltzmann constant from `constants.c`, so an error in the constant definition is not isolated by this check.

??? info "Test details"
    - Reference: Analytical limit: the steady-state initial condition equalises the energy flow through every basic node and closes the surface radiation balance sigma (T_surf^4 - teqm^4) with the Stefan-Boltzmann constant of constants.c.
    - Tolerance: Relative energy-flow spread below 1e-8 (observed 2e-11); grey-body pin at rel 1e-5.
    - Test id: `tests/test_energy.py::test_steady_state_ic_balances_interior_and_surface`
    - Command: `make`, then `pytest -o addopts= tests/test_energy.py::test_steady_state_ic_balances_interior_and_surface`
    - Companion test: `tests/test_energy.py::test_surface_node_flux_is_the_grey_body_atmospheric_flux` verifies that surface node flux equals the atmospheric grey-body value.

## Related code

- `energy.c`: `set_Etot`, `append_Jcond`, `append_Jconv`, `append_Hradio`, `solve_for_steady_state_energy_interior`.
- `tests/test_energy.py`: `test_disabled_transport_mechanisms_carry_zero_flux`, `test_radiogenic_heating_pins_two_isotope_decay`, `test_steady_state_ic_balances_interior_and_surface`.
