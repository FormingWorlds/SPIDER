# eos.c: EOS interface: setup, viscosity, phase boundaries

**Source under test**: `eos.c`

**Reference-pinned test**: `tests/test_eos.py::test_phase_boundary_matches_independent_table_read`

**Anchor**: Cross-implementation cross-check of the loaded melt phase boundary against an independent read of liquidus_A11_H13.dat (Andrault et al. 2011 liquidus with the Hirschmann 2013 solidus companion).

**Tolerance**: rel 1e-12 at the P = 0 table edge, a mid-mantle node, and an off-node deep point.

**Discrimination guards**: The solidus value at 10 GPa (about 1524 J/kg/K) sits far from the pinned liquidus value (about 2128 J/kg/K), so a swapped-boundary regression fails; sign and scale guards bound the entropies; a companion test pins the per-phase viscosity and conductivity dispatch with a 19-decade melt/solid contrast.

eos.c owns the option parsing shared by all EOS implementations and loads the phase boundaries. The boundary interpolation is compared against numpy.interp on the same file, and the per-phase transport constants configured in the options file are recovered exactly from the evaluation.
