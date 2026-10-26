# mesh.c: Static mesh and pressure structure

## What this page checks

This page checks static radial mesh and pressure profile construction in `mesh.c`.
The mesh module sets up basic and staggered radial nodes, shell areas, shell volumes, and gravitational pressures.
Validation means that we test the native pressure profile against the closed-form Adams-Williamson solution.
If mesh construction fails, shell geometry and pressure fields in the mantle are distorted.
The section below details the validation check, its tolerance, and its test command.

## Pressure profile matches Adams-Williamson closed form

**Why this check exists.** Radial grid generation can suffer from sign errors in the hydrostatic integral or wrong radial bounds; the test evaluates the expected pressure at the code's own radii, so a spacing error is not caught. An error in mesh setup makes the pressure and volume arrays of every physics module wrong.

**What it tests.** The test evaluates the native Adams-Williamson pressure profile P(r) = -(rhos g / beta)(exp(beta (R - r)) - 1) in closed form. It checks the basic-node pressures through the mantle. A sign-flipped beta and the linear small-beta approximation both fall far outside tolerance, confirming proper discrimination. Sibling test `test_mesh_orderings_interleave_and_shell_masses_close` checks geometric node interleaving and shell mass conservation. Sibling test `test_external_linear_density_mesh_replaces_the_aw_profile` confirms that external meshes replace native profiles cleanly.

**How we know the right answer.** Under the Adams-Williamson assumptions, the hydrostatic equation integrates to an exact analytical expression. Computed pressures agree with the closed form to rel 1e-12 (observed 6e-15, limited by precision in JSON serialization).

**Why it matters.** The mesh module builds the static spatial and pressure framework that every interior routine in SPIDER evaluates. PROTEUS reads radius arrays `radius_b` and pressure arrays `pressure_s` (in `ReadSPIDER` of `spider.py`).

**Known limit.** The native profile assumes an idealized Adams-Williamson compressibility model rather than self-consistent mineralogical structures.

??? info "Test details"
    - Reference: Analytical limit: the Adams-Williamson pressure profile P(r) = -(rhos g / beta)(exp(beta (R - r)) - 1) in closed form.
    - Tolerance: rel 1e-12 on the basic-node pressures (observed 6e-15; mesh.c evaluates the same closed form, so the agreement is limited by the round trip through the JSON output).
    - Test id: `tests/test_mesh.py::test_pressure_profile_matches_adams_williamson_closed_form`
    - Command: `make`, then `pytest -o addopts= tests/test_mesh.py::test_pressure_profile_matches_adams_williamson_closed_form`
    - Companion test: `tests/test_mesh.py::test_mesh_orderings_interleave_and_shell_masses_close` verifies node interleaving and shell mass conservation.

## Related code

- `mesh.c`: `set_mesh`.
- `tests/test_mesh.py`: `test_pressure_profile_matches_adams_williamson_closed_form`, `test_mesh_orderings_interleave_and_shell_masses_close`.
