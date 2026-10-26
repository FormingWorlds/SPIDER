# eos_adamswilliamson.c: Adams-Williamson analytic density

## What this page checks

This page checks the Adams-Williamson model in `eos_adamswilliamson.c`, which builds planetary structure.
The Adams-Williamson model describes how mantle density increases with depth.
Validation means that we check computed profiles against the exact analytical formula.
If the density profile is incorrect, mantle mass, pressure gradients, and shell volumes are wrong.
The text below details the check, its tolerance, and its test command.

## Density matches the closed-form profile

**Why this check exists.** Analytical codes can suffer from sign errors in compressibility, or from wrong fit inputs. A bug in density calculations distorts the pressure field and mesh geometry without an error.

**What it tests.** The test evaluates the formula rho(P) = rhos - P beta / g, using parameters fitted to the PREM lower mantle for blackbody50. It checks density values at the surface (P = 0), at 10 GPa, and at the core-mantle boundary pressure. A sign-flipped compressibility shifts the 10 GPa density by more than 200 kg/m3, which the test guards against. Sibling test `test_si_density_invariant_under_nondimensionalisation_choice` confirms that physical SI density outputs stay unchanged under the nondimensionalisation choice.

**How we know the right answer.** The Adams-Williamson formula provides an exact closed-form density profile. Numerical values in C agree with the analytical profile to rel 1e-12, reducing at the surface to the exact configured surface density.

**Why it matters.** The Adams-Williamson EOS supplies the static structural profile used by SPIDER native mesh code (`parameters.c` and `mesh.c`).

**Known limit.** The Adams-Williamson model assumes an idealized profile, rather than a multi-phase EOS.

![Adams-Williamson density against pressure from the closed form and from the code](../assets/validation/eos_adamswilliamson_density.svg#only-light){ width="80%" }
![Adams-Williamson density against pressure from the closed form and from the code](../assets/validation/eos_adamswilliamson_density_dark.svg#only-dark){ width="80%" }

**How to read the plot.** The x-axis is the pressure and the y-axis the density. The line is the closed form $\rho_s - P\beta/g$, with surface density $\rho_s$, compressibility parameter $\beta$ and gravity $g$. The dashed line is the form with a sign-flipped $\beta$, which the test rejects (context). The circles are the asserted densities of eos_adamswilliamson.c at the surface, at 10 GPa and at 135 GPa. A pass means that the circles lie on the line (relative 1e-12).

??? info "Test details"
    - Reference: Analytical limit: rho(P) = rhos - P beta / g in closed form, with the blackbody50 PREM lower-mantle fit parameters.
    - Tolerance: rel 1e-12 at the surface (P = 0), 10 GPa, and the approximate core-mantle boundary pressure.
    - Test id: `tests/test_eos_adamswilliamson.py::test_density_matches_the_closed_form_profile`
    - Command: `make tests_c`, then `pytest -o addopts= tests/test_eos_adamswilliamson.py::test_density_matches_the_closed_form_profile` (add `--validation-plots` to write the plot pair)
    - Companion test: `tests/test_eos_adamswilliamson.py::test_si_density_invariant_under_nondimensionalisation_choice` asserts SI invariance under the nondimensionalisation choice.

## Related code

- `eos_adamswilliamson.c`: `EOSCreate_AdamsWilliamson`, `EOSEval_AdamsWilliamson`.
- `tests/test_eos_adamswilliamson.py`: `test_density_matches_the_closed_form_profile`, `test_si_density_invariant_under_nondimensionalisation_choice`.
