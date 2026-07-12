# bc.c: Boundary conditions

**Source under test**: `bc.c`

**Reference-pinned test**: `tests/test_bc.py::test_prescribed_flux_bc_echoes_value_and_inverts_emissivity`

**Anchor**: Analytical identity: with SURFACE_BC 4 the surface flux equals the prescribed value, and the reported emissivity is its grey-body inversion.

**Tolerance**: rel 1e-9 on the flux echo; rel 1e-6 on the emissivity inversion.

**Discrimination guards**: The grey-body flux at the same surface temperature differs from the prescribed value by far more than tolerance (dispatch guard); temperature ordering across the mantle (CMB hotter than surface) and the near-zero surface pressure are asserted on the default configuration.

The boundary-condition dispatch is pinned through the prescribed-flux pathway PROTEUS uses in coupled runs: the value handed in through the option must reappear identically in the output, with the emissivity consistently inverted from it.

**Reference-pinned test**: `tests/test_bc.py::test_constant_entropy_bc_pins_the_initial_surface`

**Anchor**: Analytical identity: the constant-entropy boundary writes ic_surface_entropy (2550 J/kg/K) onto the surface basic node, preserved through the steady-state energy solve into the initial output.

**Tolerance**: rel 1e-10 (assigned, not solved).

**Discrimination guards**: The default configuration's surface value (2599.7 J/kg/K from the 2600 adiabat) sits about 50 J/kg/K away; positivity and table-range bounds on the core-side value after the steady rebalance. The prescribed-core-flux comparison against the core-cooling baseline (same file) discriminates the CORE_BC dispatch by the sign of the CMB entropy difference and the doubled CMB heat flux.
