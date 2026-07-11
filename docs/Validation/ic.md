# ic.c: Initial condition

**Source under test**: `ic.c`

**Reference-pinned test**: `tests/test_ic.py::test_prescribed_adiabat_entropy_sets_the_initial_profile`

**Anchor**: Analytical limit: the initial condition prescribes the adiabat entropy (2600 J/kg/K at the top staggered node) with the configured small gradient ramp.

**Tolerance**: Exact pin at the top node; the profile mean is bounded by the |ic_dsdr| times mantle depth ramp budget.

**Discrimination guards**: A run with ic_adiabat_entropy = 2400 shifts the profile by exactly 200 J/kg/K (wrong-value discrimination); cooling at later outputs breaks the initial flatness, confirming the IC is not a fixed point of the output pipeline.

The initial condition writes the prescribed adiabat onto the mesh. The top-node entropy, the integrated gradient ramp, and the response to a different prescribed value are pinned from the t = 0 output.
