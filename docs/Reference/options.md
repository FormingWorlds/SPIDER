# Runtime options

SPIDER is configured through PETSc-style options: one `-name value`
pair per line in an options file passed as
`spider -options_file <file.opts>`, with further pairs on the command
line overriding the file. All options are consumed in `parameters.c`;
this page is generated from it by `tools/generate_options_reference.py`.
All values are SI unless the description notes otherwise.

The annotated example configurations under `tests/opts/` show working
combinations: `blackbody50.opts` is the minimal grey-body cooling setup
and `reaction.opts` adds volatiles, reactions, and the coupled
atmosphere.

## Options

| Option | Type | Default | Description |
|---|---|---|---|
| `-entropy0` | positive scalar | `1.0E3` | J/kg/K |
| `-radius0` | positive scalar | `1.0E6` | m |
| `-time0` | positive scalar | `3.154E7` | s |
| `-pressure0` | positive scalar | `1.0E7` | Pa |
| `-volatile0` | positive scalar | `1.0E-10` |  |
| `-nstepsmacro` | integer |  |  |
| `-stepmacro` | integer |  |  |
| `-n` | positive integer | `200` |  |
| `-MASS_COORDINATES` | flag |  |  |
| `-MESH_SOURCE` | integer |  |  |
| `-mesh_external_filename` | string |  |  |
| `-activate_rollback` | flag |  |  |
| `-activate_poststep` | flag |  |  |
| `-outputDirectory` | string |  |  |
| `-radius` | positive scalar | `6371000.0` | m |
| `-coresize` | positive scalar | `0.55` | Earth core radius |
| `-mixing_length` | positive integer | `1` |  |
| `-mixing_length_peak_location` | positive scalar | `0.5` |  |
| `-mixing_length_peak_amplitude` | positive scalar | `0.5` |  |
| `-layer_interface_radius` | positive scalar | `P->coresize` |  |
| `-Mg_Si0` | scalar |  |  |
| `-Mg_Si1` | scalar |  |  |
| `-IC_INTERIOR` | positive integer | `1` |  |
| `-ic_interior_filename` | string |  |  |
| `-ic_melt_pressure` | scalar |  |  |
| `-ic_adiabat_entropy` | scalar |  |  |
| `-ic_dsdr` | scalar |  |  |
| `-ic_steady_state_energy` | flag |  |  |
| `-ic_surface_entropy` | scalar |  |  |
| `-ic_core_entropy` | scalar |  |  |
| `-grain` | scalar |  |  |
| `-HTIDAL` | integer |  |  |
| `-htidal_value` | scalar |  |  |
| `-htidal_filename` | string |  |  |
| `-JGRAV_BOTTOM_UP` | flag |  |  |
| `-CORE_BC` | integer |  |  |
| `-core_bc_value` | scalar |  |  |
| `-gravity` | scalar |  |  |
| `-phi_critical` | scalar |  |  |
| `-phi_width` | scalar |  |  |
| `-rho_core` | scalar |  |  |
| `-cp_core` | scalar |  |  |
| `-log10visc_min` | scalar |  |  |
| `-log10visc_max` | scalar |  |  |
| `-eddy_diffusivity_thermal` | scalar |  |  |
| `-eddy_diffusivity_chemical` | scalar |  |  |
| `-VISCOUS_LID` | integer |  |  |
| `-lid_log10visc` | scalar |  |  |
| `-lid_thickness` | scalar |  |  |
| `-CONDUCTION` | flag |  |  |
| `-CONVECTION` | flag |  |  |
| `-MIXING` | flag |  |  |
| `-SEPARATION` | integer |  |  |
| `-IC_ATMOSPHERE` | integer |  |  |
| `-ic_atmosphere_filename` | string |  |  |
| `-SURFACE_BC_ACC` | flag |  |  |
| `-SURFACE_BC` | integer |  |  |
| `-surface_bc_value` | scalar |  |  |
| `-PSEUDO_VOLATILES` | flag |  |  |
| `-emissivity0` | scalar |  |  |
| `-THERMAL_ESCAPE` | flag |  |  |
| `-CONSTANT_ESCAPE` | flag |  |  |
| `-ZAHNLE_ESCAPE` | flag |  |  |
| `-solar_xuv_factor` | scalar |  |  |
| `-teqm` | scalar |  |  |
| `-tsurf_poststep_change` | scalar |  |  |
| `-PARAM_UTBL` | flag |  |  |
| `-param_utbl_const` | scalar |  |  |
| `-P0` | scalar |  |  |
| `-reaction_ammonia1` | flag |  |  |
| `-reaction_carbondioxide_IVTANTHERMO` | flag |  |  |
| `-reaction_carbondioxide_JANAF` | flag |  |  |
| `-reaction_methane_IVTANTHERMO` | flag |  |  |
| `-reaction_water_IVTANTHERMO` | flag |  |  |
| `-reaction_water_JANAF` | flag |  |  |
| `-OXYGEN_FUGACITY` | integer |  |  |
| `-OXYGEN_FUGACITY_offset` | scalar |  |  |

## Prefixed option families

The options below are registered with runtime-composed names, so they
appear once per phase, radionuclide, or volatile rather than as fixed
strings.

### Per-phase equation of state

`-phase_names <melt,solid>` declares the phases; each phase `<p>` then
reads its own EOS configuration: `-<p>_TYPE` (1 = lookup), the table
files `-<p>_alpha_filename`, `-<p>_cp_filename`, `-<p>_dTdPs_filename`,
`-<p>_rho_filename`, `-<p>_temp_filename` (each also available with an
`_rel_to_src` suffix to resolve relative to the source tree),
`-<p>_phase_boundary_filename`, the transport constants `-<p>_log10visc`
and `-<p>_cond`, the viscosity law parameters `-<p>_activation_energy`,
`-<p>_activation_volume`, `-<p>_visc_ref_temp`, `-<p>_visc_ref_pressure`,
`-<p>_visc_ref_comp`, and the Adams-Williamson parameters `-<p>_rhos`
and `-<p>_beta` (used with the `adamswilliamson` EOS type).

### Per-radionuclide heating

`-radionuclide_names <name,...>` declares the heat sources; each
radionuclide `<r>` reads `-<r>_t0` (years), `-<r>_abundance`
(fractional), `-<r>_concentration` (ppmw), `-<r>_heat_production`
(W/kg), and `-<r>_half_life` (years).

### Per-volatile and per-reaction chemistry

Volatile species and their reactions (used by configurations like
`tests/opts/reaction.opts`) read per-species solubility, molar mass,
initial abundance, and escape parameters under the volatile's name
prefix (for example `-H2O_initial_ppmw`), plus reaction definitions
pairing the species. The reaction test configuration documents the
working set.
