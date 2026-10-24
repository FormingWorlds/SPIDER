# eos_adamswilliamson.c: Adams-Williamson analytic density

**Source under test**: `eos_adamswilliamson.c`

## Cases

### Density matches the closed-form profile

**Reference-pinned test**: `tests/test_eos_adamswilliamson.py::test_density_matches_the_closed_form_profile`

**Reference**: Analytical limit: rho(P) = rhos - P beta / g in closed form, with the blackbody50 PREM lower-mantle fit parameters.

**Tolerance**: rel 1e-12 at the surface (P = 0), 10 GPa, and the approximate core-mantle boundary pressure.

**Command**: `make tests_c`, then `pytest -o addopts= tests/test_eos_adamswilliamson.py::test_density_matches_the_closed_form_profile`

**Discrimination guards**: A sign-flipped compressibility shifts the 10 GPa density by more than 200 kg/m3; monotonicity under compression and the silicate density range bound the profile; SI invariance under the nondimensionalisation choice is asserted separately.

The Adams-Williamson EOS provides the static structural profile used by the native mesh. Its density is a closed-form expression, so the evaluation is pinned to rounding accuracy, with the surface limit reducing exactly to the configured surface density.
