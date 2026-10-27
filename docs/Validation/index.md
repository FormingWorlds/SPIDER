# Validation

## What this page checks

This page lists the validation cases of SPIDER: each case checks 1 physics source file against a known answer.
Validation means that we compare model outputs against analytical limits and independent implementations.
Each physics source file has at least one pinned test, with a stated tolerance and reference value.
If these components are wrong, the interior thermal evolution that SPIDER computes, alone or inside [PROTEUS](https://proteus-framework.org/PROTEUS), is wrong. PROTEUS is the coupling framework that runs SPIDER as its interior module.
The table below lists each validation case, organized by physical process.
A full-run regression against the frozen blackbody50 reference complements these cases (`tests/test_regression.py`).

Terms used on every page:

- **blackbody50**: the standard 50-node test run of SPIDER, set by `tests/opts/blackbody50.opts`, with a grey-body surface (`SURFACE_BC 1`) and no internal heating.
- **Basic nodes** and **staggered nodes**: the 2 sets of points of the radial mesh. Basic nodes are the cell boundaries, staggered nodes the cell centres.
- **IC** and **BC**: initial condition and boundary condition.

Tests in the `unit` tier drive the small C test executables in `tests/c` (`make tests_c`); tests in the `smoke` tier run the `spider` binary (`make`) on short configurations. See [Testing SPIDER](../How-to/test.md) for the tiers and the commands.

## Cases by process

| Process | Page | Case | Test id | Reference | Tier |
|---|---|---|---|---|---|
| Equation of state and material properties | [eos.c](eos.md) | Compositional viscosity matches Spaargaren et al. (2020) | `tests/test_eos.py::test_compositional_viscosity_matches_spaargaren` | Spaargaren et al. (2020) | unit |
| Equation of state and material properties | [eos.c](eos.md) | Phase boundary matches independent table read | `tests/test_eos.py::test_phase_boundary_matches_independent_table_read` | Cross-implementation cross-check (independent read of liquidus_A11_H13.dat) | unit |
| Equation of state and material properties | [eos_adamswilliamson.c](eos_adamswilliamson.md) | Density matches the closed-form profile | `tests/test_eos_adamswilliamson.py::test_density_matches_the_closed_form_profile` | Analytical limit | unit |
| Equation of state and material properties | [eos_composite.c](eos_composite.md) | Fusion equals liquidus minus solidus and phi is linear in entropy | `tests/test_eos_composite.py::test_fusion_equals_liquidus_minus_solidus_and_phi_is_linear_in_entropy` | Analytical limit | unit |
| Equation of state and material properties | [eos_lookup.c](eos_lookup.md) | Melt density matches independent bilinear evaluation | `tests/test_eos_lookup.py::test_melt_density_matches_independent_bilinear_evaluation` | Cross-implementation cross-check | unit |
| Equation of state and material properties | [interp.c](interp.md) | Affine data reproduced exactly including last node | `tests/test_interp.py::test_affine_data_reproduced_exactly_including_last_node` | Analytical limit | unit |
| Equation of state and material properties | [matprop.c](matprop.md) | Viscosity recovers configured end members | `tests/test_matprop.py::test_viscosity_recovers_configured_end_members` | Analytical limit | smoke |
| Structure and mesh | [mesh.c](mesh.md) | Pressure profile matches Adams-Williamson closed form | `tests/test_mesh.py::test_pressure_profile_matches_adams_williamson_closed_form` | Analytical limit | smoke |
| Energy transport and time stepping | [bc.c](bc.md) | Constant-entropy BC pins the initial surface | `tests/test_bc.py::test_constant_entropy_bc_pins_the_initial_surface` | Analytical identity | smoke |
| Energy transport and time stepping | [bc.c](bc.md) | Prescribed-flux BC echoes value and inverts emissivity | `tests/test_bc.py::test_prescribed_flux_bc_echoes_value_and_inverts_emissivity` | Analytical identity | smoke |
| Energy transport and time stepping | [energy.c](energy.md) | Disabled transport mechanisms carry zero flux | `tests/test_energy.py::test_disabled_transport_mechanisms_carry_zero_flux` | Analytical limit | smoke |
| Energy transport and time stepping | [energy.c](energy.md) | Radiogenic heating pins two isotope decay | `tests/test_energy.py::test_radiogenic_heating_pins_two_isotope_decay` | Analytical limit | smoke |
| Energy transport and time stepping | [energy.c](energy.md) | Steady-state IC balances interior and surface | `tests/test_energy.py::test_steady_state_ic_balances_interior_and_surface` | Analytical limit | smoke |
| Energy transport and time stepping | [ic.c](ic.md) | Abundance IC realises the requested inventory | `tests/test_ic.py::test_abundance_ic_realises_the_requested_inventory` | Mass-balance identity | smoke |
| Energy transport and time stepping | [ic.c](ic.md) | Ocean-moles IC converts moles to mass | `tests/test_ic.py::test_ocean_moles_ic_converts_moles_to_mass` | OCEAN_MOLES constant of constants.c | smoke |
| Energy transport and time stepping | [ic.c](ic.md) | Prescribed adiabat entropy sets the initial profile | `tests/test_ic.py::test_prescribed_adiabat_entropy_sets_the_initial_profile` | Analytical limit | smoke |
| Energy transport and time stepping | [rhs.c](rhs.md) | Reported dS/dt matches finite difference of outputs | `tests/test_rhs.py::test_reported_dsdt_matches_finite_difference_of_outputs` | Analytical self-consistency | smoke; plot pair |
| Melt and phase separation | [rheologicalfront.c](rheologicalfront.md) | Front location is consistent with melt fraction profile | `tests/test_rheologicalfront.py::test_front_location_is_consistent_with_melt_fraction_profile` | Analytical self-consistency | smoke |
| Melt and phase separation | [twophase.c](twophase.md) | Global melt fraction is the mass-weighted profile mean | `tests/test_twophase.py::test_global_melt_fraction_is_the_mass_weighted_profile_mean` | Analytical identity | smoke |
| Atmosphere | [atmosphere.c](atmosphere.md) | Grey-body flux matches Stefan-Boltzmann limit | `tests/test_atmosphere.py::test_grey_body_flux_matches_stefan_boltzmann_limit` | Analytical limit | smoke |
| Chemistry | [reaction.c](reaction.md) | Elements conserved across each reaction pair | `tests/test_reaction.py::test_elements_conserved_across_each_reaction_pair` | Analytical conservation | smoke |

## Plots written by the tests

A case with a plot pair shows the tested values against their reference in a light and a dark version. The test writes the pair with the same numbers it asserts, through the `validation_plot` fixture of proteus-mpl. This command writes all pairs to `docs/assets/validation/`:

```console
pytest -o addopts= -m reference_pinned tests --validation-plots
```

Without `--validation-plots` the tests assert and write nothing. The command makes every plot again; commit only the pair of the case you changed, because the bytes match only for the same matplotlib and Pillow versions. The tests need the built `spider` binary and the C test executables.
