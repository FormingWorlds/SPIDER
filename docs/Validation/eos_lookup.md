# eos_lookup.c: Tabulated P-S equation of state

## What this page checks

This page checks the tabulated thermodynamic lookup in `eos_lookup.c`, which reads mineral tables.
`eos_lookup.c` bilinearly reads thermodynamic properties from pressure-entropy grids.
Validation means that we check C table reads against an independent Python code.
If table reads fail, the density and the other tabulated properties of the mantle are wrong; the test compares the density only.
The section below details the check, its tolerance, and its test command.

## Melt density matches independent bilinear evaluation

**Why this check exists.** Table grid reads can suffer from indexing offsets, wrong corner weights, or swapped column scales. A bug in table reading shifts density values without triggering a runtime error.

**What it tests.** The test evaluates the shipped melt density table (1TPa-dK09-elec-free set: de Koker and Stixrude 2009 properties as assembled for Bower et al. 2018). It compares C outputs with an independent Python bilinear check at three off-node (P, S) probe points spanning 7.3 to 89 GPa. The test guards against reading the wrong table: solid-table density at the same probes differs by more than 1 percent. Positive values and the 2000 to 8000 kg/m3 silicate range bound the density scale. Sibling test `test_si_outputs_invariant_under_nondimensionalisation_choice` confirms consistent SI outputs under scaling choices.

**How we know the right answer.** The table is independently parsed with Python numpy routines, sharing no code with the C side. Matching values pin file parsing, column scaling, index search, and bilinear weighting to rel 1e-9.

**Why it matters.** Lookup tables supply thermodynamic properties to mantle transport and structure routines.

**Known limit.** The test compares table reads against an independent Python read of the same table file, but does not benchmark the underlying ab initio mineral physics.

??? info "Test details"
    - Reference: Cross-implementation cross-check: an independent numpy bilinear evaluation of the shipped melt density table (1TPa-dK09-elec-free set: de Koker and Stixrude 2009 properties as assembled for Bower et al. 2018).
    - Tolerance: rel 1e-9 at three off-node (P, S) probe points spanning 7.3 to 89 GPa.
    - Test id: `tests/test_eos_lookup.py::test_melt_density_matches_independent_bilinear_evaluation`
    - Command: `make tests_c`, then `pytest -o addopts= tests/test_eos_lookup.py::test_melt_density_matches_independent_bilinear_evaluation`
    - Companion test: `tests/test_eos_lookup.py::test_thermodynamic_quantities_positive_and_rho_monotonic_in_pressure` asserts positive thermodynamic quantities and monotonic density with pressure.

## Related code

- `eos_lookup.c`: `EOSCreate_Lookup`, `EOSEval_Lookup`, `SetInterp2dValue`.
- `tests/test_eos_lookup.py`: `test_melt_density_matches_independent_bilinear_evaluation`, `test_thermodynamic_quantities_positive_and_rho_monotonic_in_pressure`.
