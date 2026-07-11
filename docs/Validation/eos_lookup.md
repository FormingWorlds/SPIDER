# eos_lookup.c: Tabulated P-S equation of state

**Source under test**: `eos_lookup.c`

**Reference-pinned test**: `tests/test_eos_lookup.py::test_melt_density_matches_independent_bilinear_evaluation`

**Anchor**: Cross-implementation cross-check: an independent numpy bilinear evaluation of the shipped melt density table (1TPa-dK09-elec-free set: de Koker and Stixrude 2009 properties as assembled for Bower et al. 2018).

**Tolerance**: rel 1e-9 at three off-node (P, S) probe points spanning 7.3 to 89 GPa.

**Discrimination guards**: The solid-table density at the same probes differs by more than 1 percent (wrong-table guard); positivity and the 2000 to 8000 kg/m3 silicate range bound the scale; a separate test asserts SI outputs are invariant under the choice of nondimensionalisation.

The lookup EOS is validated against a re-implementation of the same mathematical operation that shares no code with the C side: the table file is parsed and bilinearly interpolated with numpy primitives. Agreement pins file parsing, per-column scaling, index search, and weighting in one comparison.
