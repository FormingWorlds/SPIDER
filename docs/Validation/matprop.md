# matprop.c: Blended material properties

**Source under test**: `matprop.c`

## Cases

### Viscosity recovers configured end members

**Reference-pinned test**: `tests/test_matprop.py::test_viscosity_recovers_configured_end_members`

**Reference**: Analytical limit: away from the rheological transition the blended viscosity recovers the configured end-members (melt_log10visc = 2, solid_log10visc = 21).

**Tolerance**: abs 0.01 on log10(viscosity) at the strongly molten nodes and abs 0.05 at the strongly solid nodes.

**Command**: `make`, then `pytest -o addopts= tests/test_matprop.py::test_viscosity_recovers_configured_end_members`

**Discrimination guards**: The recovered end-members differ by more than 10 decades (swapped-phase guard); all 50 nodes are molten in the hot state and at least 5 solid in the cold one; the viscosity is positive. The sibling test `test_material_properties_positive_and_conductivity_constant` (same file) asserts the positivity of density, heat capacity, conductivity and expansivity at every node and the configured 4.0 W/m/K conductivity.

Material properties are blended across the melting interval from the per-phase EOS evaluations. The viscosity end-members and the viscosity positivity are pinned on two states: the hot initial state of the short blackbody50 run (t = 0, every node molten) and a cold 0-step run started from a 1600 J/kg/K adiabat (solid nodes); the sibling test `test_material_properties_positive_and_conductivity_constant` checks positivity and the constant conductivity on the full run.
