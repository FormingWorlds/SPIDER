# matprop.c: Blended material properties

**Source under test**: `matprop.c`

## Cases

### Viscosity recovers configured end members

**Reference-pinned test**: `tests/test_matprop.py::test_viscosity_recovers_configured_end_members`

**Reference**: Analytical limit: away from the rheological transition the blended viscosity recovers the configured end-members (melt_log10visc = 2, solid_log10visc = 21).

**Tolerance**: abs 0.01 on log10(viscosity) at the strongly molten nodes and abs 0.05 at the strongly solid nodes.

**Command**: `make`, then `pytest -o addopts= tests/test_matprop.py::test_viscosity_recovers_configured_end_members`

**Discrimination guards**: The recovered end-members differ by more than 10 decades (swapped-phase guard); positivity of density, heat capacity, conductivity, and expansivity at every node; the configured 4.0 W/m/K conductivity is recovered exactly.

Material properties are blended across the melting interval from the per-phase EOS evaluations. The viscosity end-members, the constant conductivity, and positivity of all blended quantities are pinned on the part-solidified state of the frozen-reference run.
