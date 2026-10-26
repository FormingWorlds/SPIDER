# atmosphere.c: Surface energy balance

## What this page checks

This page checks the surface radiative energy balance in `atmosphere.c`, which models heat exchange.
The atmosphere module calculates the thermal flux, which is exchanged between the planetary surface and space.
Validation means that we test the grey-body radiation routine against the analytical Stefan-Boltzmann law, which provides an exact reference.
If the surface radiation is wrong, the cooling rate of the magma ocean is incorrect.
The section below details the validation check, its tolerance, and its test command.

## Grey-body flux matches Stefan-Boltzmann limit

**Why this check exists.** Numerical implementations of radiative flux can suffer from incorrect temperature exponents, or from inverted signs. A bug in the surface flux calculation leads to unphysical planetary cooling rates, without raising a runtime error.

**What it tests.** The test evaluates the grey-body surface flux F = emissivity sigma (T_surf^4 - T_eqm^4), with emissivity 1, and equilibrium temperature T_eqm = 273 K. It compares the reported surface flux against the Stefan-Boltzmann law, evaluated at the reported surface temperature. The test guards against exponent errors, where a T^3 exponent slip changes the flux by orders of magnitude at magma-ocean temperatures. The flux must remain positive (outward), and bounded to the 1e2 to 1e9 W/m2 regime.

**How we know the right answer.** The grey-body Stefan-Boltzmann law provides an exact analytical reference for thermal radiation, which governs ideal emitters. An exponent slip to third power changes the flux by orders of magnitude, which easily violates the tolerance of rel 1e-6.

**Why it matters.** The atmosphere module computes the surface energy balance, which drives planetary mantle cooling. PROTEUS reads the surface flux `Fatm` as `F_int`, and surface temperature `temperature_surface` as `T_magma`, to couple the interior to the atmosphere.

**Known limit.** The test uses its own copy of the source value, sigma = 5.670367e-8 W m-2 K-4. A change of the constant in the code fails the test, but a value that is wrong in both places does not. PROTEUS uses this grey-body branch only with `surface_bc_mode = 'grey_body'`; its default is a prescribed flux (`SURFACE_BC 4`).

??? info "Test details"
    - Reference: Analytical limit: the grey-body flux F = emissivity sigma (T_surf^4 - T_eqm^4) with emissivity 1 and T_eqm = 273 K (Stefan-Boltzmann).
    - Tolerance: rel 1e-6 against the reported surface temperature, using the code constant sigma = 5.670367e-8 W m-2 K-4.
    - Test id: `tests/test_atmosphere.py::test_grey_body_flux_matches_stefan_boltzmann_limit`
    - Command: `make`, then `pytest -o addopts= tests/test_atmosphere.py::test_grey_body_flux_matches_stefan_boltzmann_limit`
    - Companion test: `tests/test_atmosphere.py::test_surface_cools_and_flux_decays_across_macro_steps` confirms monotone decline of flux and surface temperature over outputs.

## Related code

- `atmosphere.c`: `set_atmosphere_emissivity_and_flux`.
- `tests/test_atmosphere.py`: `test_grey_body_flux_matches_stefan_boltzmann_limit`, `test_surface_cools_and_flux_decays_across_macro_steps`.
