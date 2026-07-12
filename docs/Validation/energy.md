# energy.c: Energy fluxes

**Source under test**: `energy.c`

**Reference-pinned test**: `tests/test_energy.py::test_disabled_transport_mechanisms_carry_zero_flux`

**Anchor**: Analytical limit: a disabled transport mechanism carries zero flux, and with only conduction enabled the total flux equals the conductive flux identically.

**Tolerance**: Exact (tight allclose) on the zero and identity relations; see the test comments.

**Discrimination guards**: The complementary mechanism stays nonzero when its sibling is disabled (wrong-path guard); the total flux is asserted to be the sum of the four components at every node in the full-physics configuration; scale bounds on the magma-ocean flux magnitudes.

The flux assembly is validated through its superposition structure: each transport term can be switched off through its runtime option, and the total must respond exactly. This pins the dispatch wiring between the options, the individual flux routines, and the total used by the time integration.

**Reference-pinned test**: `tests/test_energy.py::test_radiogenic_heating_pins_two_isotope_decay`

**Anchor**: Analytical limit: radiogenic heating is the sum over isotopes of concentration times abundance times heat production, decaying as 2^(-(t - t0)/half_life). A two-isotope configuration with 100-year and 200-year half-lives pins the sum at t = 0 and the weighted decay factor 0.2506 after 200 years.

**Tolerance**: rel 1e-6 on the initial sum, rel 1e-4 on the decay factor.

**Discrimination guards**: A dropped isotope shifts the sum by 2.4e-3 relative; the two-isotope decay factor is resolved from the single-isotope values 0.25 and 0.5 and from the no-decay value 1.0.

**Reference-pinned test**: `tests/test_energy.py::test_steady_state_ic_balances_interior_and_surface`

**Anchor**: Analytical limit: the steady-state initial condition equalises the energy flow through every basic node and closes the surface radiation balance sigma (T_surf^4 - teqm^4) with the Stefan-Boltzmann constant of constants.c.

**Tolerance**: Relative energy-flow spread below 1e-8 (observed 2e-11); grey-body pin at rel 1e-5.

**Discrimination guards**: A T^3 exponent slip misses the flux by a factor of about 300; sign and scale bounds on the flux.
