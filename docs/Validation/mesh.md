# mesh.c: Static mesh and pressure structure

**Source under test**: `mesh.c`

**Reference-pinned test**: `tests/test_mesh.py::test_pressure_profile_matches_adams_williamson_closed_form`

**Anchor**: Analytical limit: the Adams-Williamson pressure profile P(r) = -(rhos g / beta)(exp(beta (R - r)) - 1) in closed form.

**Tolerance**: See the rationale comments in the test for the calibrated tolerance against the internal profile.

**Discrimination guards**: Sign and monotonicity of the pressure with depth; the core-mantle boundary pressure is bounded to its physical order of magnitude; a sign-flipped beta and the linear small-beta approximation both fall far outside tolerance; the external-mesh pathway is verified to actually differ from the native profile when supplied.

The mesh module builds the static pressure and geometry arrays every physics term runs on. The native profile is pinned against the AW closed form and the geometric consistency between basic and staggered nodes (interleaving, shell masses, monotonicity) is asserted, including for an externally supplied non-AW mesh.
