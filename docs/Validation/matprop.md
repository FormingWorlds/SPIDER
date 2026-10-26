# matprop.c: Blended material properties

## What this page checks

This page checks material property blending in `matprop.c`, which computes transport coefficients throughout the mantle.
`matprop.c` blends melt and solid properties over the melting interval to determine local viscosity and conductivities.
Validation means that we check blended viscosity against configured end-member values in pure phases.
If material property blending is wrong, mantle convective heat transport and viscosity structures are wrong.
The text below details the check, its tolerance, and its test command.

## Viscosity recovers configured end members

**Why this check exists.** Rheological blending functions can swap the melt and solid limits. A bug in property blending causes the convection solver to use wrong viscosities.

**What it tests.** The test evaluates the analytical limit where blended viscosity recovers configured end-members away from the rheological transition (melt_log10visc = 2, solid_log10visc = 21). It checks two extreme states: the hot initial state of the blackbody50 run (t = 0, where all 50 nodes are molten), and a cold 0-step run started from a 1600 J/kg/K adiabat (where at least 5 nodes are solid). The recovered end-members must differ by more than 10 decades, guarding against swapped phases. Sibling test `test_material_properties_positive_and_conductivity_constant` asserts positive values for density, heat capacity and thermal expansion, and a constant conductivity, alongside configured 4.0 W/m/K conductivity.

**How we know the right answer.** Away from the partial-melting interval, blended material properties must approach pure-phase limits asymptotically. Viscosity matches configured values to abs 0.01 on log10(viscosity) at molten nodes and abs 0.05 at solid nodes.

**Why it matters.** Mantle viscosity governs convective heat transport. PROTEUS reads the viscosity array `visc_b` from SPIDER.

**Known limit.** The main test samples only nearly pure nodes, so a wrong weighting inside the melting interval is not caught there. The companion test `test_viscosity_rises_monotonically_across_rheological_transition` checks that the viscosity rises steadily across the transition, by more than 3 decades, but not its shape.

![log10 viscosity against radius for the hot molten and the cold initial condition](../assets/validation/matprop_viscosity_end_members.svg#only-light){ width="80%" }
![log10 viscosity against radius for the hot molten and the cold initial condition](../assets/validation/matprop_viscosity_end_members_dark.svg#only-dark){ width="80%" }

**How to read the plot.** The x-axis is the radius and the y-axis the log10 viscosity at the basic nodes. The solid line is the hot initial condition, all 50 nodes molten, asserted at the melt end member 2 (dashed, within 0.01). The dash-dotted line is the cold initial condition at 1600 J kg$^{-1}$ K$^{-1}$, and the circles its asserted nodes with a melt fraction below $10^{-3}$, at the solid end member 21 (dotted, within 0.05). A pass means that the solid line lies on the dashed line and the circles on the dotted line.

??? info "Test details"
    - Reference: Analytical limit: away from the rheological transition the blended viscosity recovers the configured end-members (melt_log10visc = 2, solid_log10visc = 21).
    - Tolerance: abs 0.01 on log10(viscosity) at the strongly molten nodes and abs 0.05 at the strongly solid nodes.
    - Test id: `tests/test_matprop.py::test_viscosity_recovers_configured_end_members`
    - Command: `make`, then `pytest -o addopts= tests/test_matprop.py::test_viscosity_recovers_configured_end_members` (add `--validation-plots` to write the plot pair)
    - Companion test: `tests/test_matprop.py::test_material_properties_positive_and_conductivity_constant` asserts positive values for density, heat capacity and thermal expansion, and a constant conductivity; the main test asserts a positive viscosity.

## Related code

- `matprop.c`: `set_capacitance_staggered`, `set_matprop_basic`.
- `tests/test_matprop.py`: `test_viscosity_recovers_configured_end_members`, `test_material_properties_positive_and_conductivity_constant`.
