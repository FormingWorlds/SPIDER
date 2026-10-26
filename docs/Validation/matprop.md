# matprop.c: Blended material properties

## What this page checks

This page checks material property blending in `matprop.c`, which computes transport coefficients throughout the mantle.
`matprop.c` blends melt and solid properties over the melting interval to determine local viscosity and conductivities.
Validation means that we check blended viscosity against configured end-member values in pure phases.
If material property blending is wrong, mantle convective heat transport and viscosity structures are corrupted.
Coupled planetary runs in PROTEUS then evolve along incorrect cooling rates.
The text below details the check, its tolerance, and its test command.

## Viscosity recovers configured end members

**Why this check exists.** Rheological blending functions can apply incorrect weighting formulas, swap melt and solid limits, or invert transition bounds. A bug in property blending causes convection solvers to experience wrong viscosities.

**What it tests.** The test evaluates the analytical limit where blended viscosity recovers configured end-members away from the rheological transition (melt_log10visc = 2, solid_log10visc = 21). It checks two extreme states: the hot initial state of the blackbody50 run (t = 0, where all 50 nodes are molten), and a cold 0-step run started from a 1600 J/kg/K adiabat (where at least 5 nodes are solid). The recovered end-members must differ by more than 10 decades, guarding against swapped phases. Sibling test `test_material_properties_positive_and_conductivity_constant` asserts positive values for density, heat capacity, conductivity, and expansivity, alongside configured 4.0 W/m/K conductivity.

**How we know the right answer.** Away from the partial-melting interval, blended material properties must approach pure-phase limits asymptotically. Viscosity matches configured values to abs 0.01 on log10(viscosity) at molten nodes and abs 0.05 at solid nodes.

**Why it matters.** Mantle viscosity governs convective heat transport. PROTEUS reads interior viscosity arrays `visc_b` from SPIDER to track mantle dynamics.

**Known limit.** The check evaluates asymptotic recovery at extreme states, but does not benchmark the shape of the rheological front through the transition.

??? info "Test details"
    - Reference: Analytical limit: away from the rheological transition the blended viscosity recovers the configured end-members (melt_log10visc = 2, solid_log10visc = 21).
    - Tolerance: abs 0.01 on log10(viscosity) at the strongly molten nodes and abs 0.05 at the strongly solid nodes.
    - Test id: `tests/test_matprop.py::test_viscosity_recovers_configured_end_members`
    - Command: `make`, then `pytest -o addopts= tests/test_matprop.py::test_viscosity_recovers_configured_end_members`
    - Companion test: `tests/test_matprop.py::test_material_properties_positive_and_conductivity_constant` asserts positive values for properties and constant conductivity.

## Related code

- `matprop.c`: `set_capacitance_staggered`, `set_matprop_basic`.
- `tests/test_matprop.py`: `test_viscosity_recovers_configured_end_members`, `test_material_properties_positive_and_conductivity_constant`.
