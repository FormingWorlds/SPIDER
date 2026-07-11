# atmosphere.c: Surface energy balance

**Source under test**: `atmosphere.c`

**Reference-pinned test**: `tests/test_atmosphere.py::test_grey_body_flux_matches_stefan_boltzmann_limit`

**Anchor**: Analytical limit: the grey-body flux F = emissivity sigma (T_surf^4 - T_eqm^4) with emissivity 1 and T_eqm = 273 K (Stefan-Boltzmann).

**Tolerance**: rel 1e-6 against the reported surface temperature, using the code constant sigma = 5.670367e-8 W m-2 K-4.

**Discrimination guards**: A T^3 exponent slip changes the flux by orders of magnitude at magma-ocean temperatures; the flux is positive (outward) and bounded to the 1e2 to 1e9 W/m2 regime; monotone decline of flux and surface temperature over the first outputs.

The atmosphere module computes the surface energy balance that drives the cooling. The grey-body branch is pinned against the Stefan-Boltzmann law evaluated from the same output state, and the secular cooling trend is asserted across output times.
