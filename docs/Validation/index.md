# Validation

Each physics source carries at least one test pinned against a published
benchmark, an analytical limit, or a cross-implementation cross-check
(the `reference_pinned` marker in the test suite). The pages below record
the anchor, the tolerance and its rationale, and the discrimination
guards for each source. Full-run regression against the frozen
blackbody50 reference complements these per-source anchors
(`tests/test_regression.py`).

| Source | Anchor | Test |
|---|---|---|
| `interp.c` | Analytical limit | `test_affine_data_reproduced_exactly_including_last_node` |
| `eos_lookup.c` | Cross-implementation cross-check | `test_melt_density_matches_independent_bilinear_evaluation` |
| `eos_composite.c` | Analytical limit | `test_fusion_equals_liquidus_minus_solidus_and_phi_is_linear_in_entropy` |
| `eos.c` | Cross-implementation cross-check of the loaded melt phase boundary against an independent read of liquidus_A11_H13.dat (Andrault et al. 2011 liquidus with the Hirschmann 2013 solidus companion). | `test_phase_boundary_matches_independent_table_read` |
| `eos_adamswilliamson.c` | Analytical limit | `test_density_matches_the_closed_form_profile` |
| `mesh.c` | Analytical limit | `test_pressure_profile_matches_adams_williamson_closed_form` |
| `matprop.c` | Analytical limit | `test_viscosity_recovers_configured_end_members` |
| `energy.c` | Analytical limit | `test_disabled_transport_mechanisms_carry_zero_flux` |
| `ic.c` | Analytical limit | `test_prescribed_adiabat_entropy_sets_the_initial_profile` |
| `bc.c` | Analytical identity | `test_prescribed_flux_bc_echoes_value_and_inverts_emissivity` |
| `atmosphere.c` | Analytical limit | `test_grey_body_flux_matches_stefan_boltzmann_limit` |
| `rheologicalfront.c` | Analytical self-consistency | `test_front_location_is_consistent_with_melt_fraction_profile` |
| `twophase.c` | Analytical identity | `test_global_melt_fraction_is_the_mass_weighted_profile_mean` |
| `reaction.c` | Analytical conservation | `test_elements_conserved_across_each_reaction_pair` |
| `rhs.c` | Analytical self-consistency | `test_reported_dsdt_matches_finite_difference_of_outputs` |
