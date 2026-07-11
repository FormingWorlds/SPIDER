# rhs.c: Entropy time-derivative assembly

**Source under test**: `rhs.c`

**Reference-pinned test**: `tests/test_rhs.py::test_reported_dsdt_matches_finite_difference_of_outputs`

**Anchor**: Analytical self-consistency: the reported dS/dt matches the finite-difference slope of consecutive outputs over 10-year macro steps.

**Tolerance**: rel 2e-2 at every staggered node (observed agreement 0.7 percent, midpoint rule over 10 years).

**Discrimination guards**: Cooling sign at every node; zero radiogenic and tidal source arrays in this configuration; near-uniform decline in the upper molten layer (adiabatic mixing).

rhs.c assembles the entropy tendency from the flux divergence and sources; it is validated as the actual derivative of the trajectory the timestepper follows, by comparing the reported tendency against the slope between closely spaced outputs.
