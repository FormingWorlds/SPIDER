# bc.c: Boundary conditions

**Source under test**: `bc.c`

**Reference-pinned test**: `tests/test_bc.py::test_prescribed_flux_bc_echoes_value_and_inverts_emissivity`

**Anchor**: Analytical identity: with SURFACE_BC 4 the surface flux equals the prescribed value, and the reported emissivity is its grey-body inversion.

**Tolerance**: rel 1e-9 on the flux echo; rel 1e-6 on the emissivity inversion.

**Discrimination guards**: The grey-body flux at the same surface temperature differs from the prescribed value by far more than tolerance (dispatch guard); temperature ordering across the mantle (CMB hotter than surface) and the near-zero surface pressure are asserted on the default configuration.

The boundary-condition dispatch is pinned through the prescribed-flux pathway PROTEUS uses in coupled runs: the value handed in through the option must reappear identically in the output, with the emissivity consistently inverted from it.
