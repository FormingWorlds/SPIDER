# SPIDER Code Review Criteria

When reviewing SPIDER code (either your own or via code-reviewer agents), apply these domain-specific checks in addition to standard code quality review.

> **Discovery note.** SPIDER keeps its Claude-Code rule files under `.github/.claude/rules/` (not the conventional repo-root `.claude/`) so they can be tracked in git and shared across collaborators. Claude does NOT auto-discover them at this path; the repo-root `CLAUDE.md` (symlinked to `.github/copilot-instructions.md`) names this file and `spider-tests.md` explicitly. **Before opening any review pass, read both this file and `spider-tests.md`.**

## Physics plausibility

- Temperature must be positive everywhere (Kelvin). Flag any code path where T could reach zero or go negative, including through the entropy-to-temperature lookup at extreme entropies.
- Pressure must be positive and monotonically increasing with depth. Flag any mesh or EOS change that could produce a non-monotonic pressure profile without an explicit guard.
- Melt fraction phi must lie in [0, 1] at every node. The two-phase blending in `twophase.c` and the smoothing in `matprop.c` (`matprop_smooth_width`) must clamp, not extrapolate.
- Liquidus must sit above solidus at every pressure in the loaded tables. Flag any table-loading change that skips this check.
- Viscosity, density, heat capacity, thermal expansivity must be positive after every lookup and blend. Out-of-range lookups must fail loudly or clamp with a warning, never extrapolate silently.
- Mantle mass closure: `mass_liquid + mass_solid = mass_mantle`. Flag any change to mass bookkeeping in `monitor.c` output or the underlying integrals that could break the closure.

## Nondimensional scaling boundaries

SPIDER solves the nondimensionalised problem. The scaling constants (`-entropy0`, `-radius0`, `-time0`, `-pressure0` where used) convert between internal and SI values, and every JSON output field carries its `scaling` alongside `values`.

When reviewing code that crosses this boundary (a new output field, a new option, a new source term), verify:

- The nondimensionalisation is applied exactly once on input and inverted exactly once on output. Double-scaling and missed scaling both produce O(scaling)-factor errors that can look plausible in isolation.
- New JSON fields are emitted as `DimensionalisableField`s with correct `scaling` and `units`, never as raw internal values.
- Option defaults documented in `parameters.c` state their unit (SI unless noted, `-dtmacro` in years, `-gravity` negative by convention).

The `-gravity` sign convention (negative, pointing inward) is a recurring trap for new code paths that compute hydrostatic quantities.

## PETSc / SUNDIALS failure modes

- Every PETSc call must have its return code checked (`PetscCall` / `CHKERRQ` style, matching the surrounding code). Flag any bare call.
- Memory: every `PetscMalloc`/`VecCreate`/`DMCreate` needs its matching destroy on all exit paths. Leaks accumulate across the many macro steps of a coupled PROTEUS run.
- CVODE (SUNDIALS2, BDF) controls the inner time integration. A change that alters stiffness (new source term, sharper material-property gradient) can silently degrade CVODE step sizes. Any such change needs a smoke-tier check on step count / final time, not just an exit-code run.
- The binary is serial-only (`main.c` refuses MPI ranks > 1). Flag any new code that assumes or introduces parallel constructs.
- Out-of-range EOS table access: the lookup layer guards against queries beyond the table domain. Flag any new lookup call that bypasses the guarded path.

## JSON output contract (PROTEUS coupling surface)

PROTEUS parses SPIDER's JSON output (`<outputDirectory>/<time_years>.json`) as its only view of the interior state. The fields PROTEUS reads (see `src/proteus/interior_energetics/spider.py` in the PROTEUS repo) include: `mass_liquid`, `mass_solid`, `mass_mantle`, `mass_core`, `temperature_surface`, `phi_global`, `Fatm`, `rheological_front_dynamic/depth`, and the staggered/basic node arrays (`phi_s`, `rho_s`, `radius_b`, `visc_b`, `mass_s`, `temp_s`, `pressure_s`, `S_s`, `cp_s`, `Hradio_s`, `Htidal_s`, `Jconv_b`, `Jcond_b`), plus the full-precision `time_years`.

Review rules:

- Renaming, removing, or changing the units/scaling of any of these fields is a breaking change to PROTEUS; it requires a coordinated PROTEUS-side PR and a pin bump, and must be called out in the release notes.
- New fields are additive and safe; they must carry correct `scaling` and `units`.
- The restart path (`-IC_INTERIOR 2 -ic_interior_filename <json>`) must remain able to read the output the binary itself wrote (round-trip property). Flag any output change without the matching reader change.

## PROTEUS coupling patterns

1. **Retry ladder tolerance interplay.** PROTEUS retries failed SPIDER calls up to 8 times, scaling `-dtmacro` by 0.3x and the CVODE tolerances by 5x per attempt. A source change that makes the solver more fragile shows up as more ladder descent, not as a visible failure. When reviewing solver-adjacent changes, check the smoke tests still pass at the STRICT tolerances (`-ts_sundials_atol/rtol 1e-8`), not just at relaxed ones.
2. **External mesh from Zalmoxis.** With `-MESH_SOURCE 1 -mesh_external_filename`, the mesh (and the pressure profile) comes from Zalmoxis instead of the internal Adams-Williamson model. PROTEUS may also blend consecutive meshes and remap entropy between them. Review rules: the external-mesh reader must validate monotonicity and node count; changes to the mesh file format require the matching PROTEUS-side writer change; the AW pathway must remain the fallback.
3. **Core parameter echo-back.** PROTEUS passes `-coresize`, `-rho_core`, `-cp_core` derived from the structure module (Zalmoxis), overriding any internal defaults. Flag any change that re-derives core properties internally when these options are set; the caller's values are authoritative.
4. **Surface boundary condition dispatch.** PROTEUS switches between `-SURFACE_BC 4` (prescribed flux from the atmosphere module) and `-SURFACE_BC 1` (grey body). A change to either branch needs tests on both, because PROTEUS exercises both across a coupled run.

## Options and parameters discipline

- Every new runtime option is registered in `parameters.c` with a default, a unit comment, and validation of its range where applicable. The options reference page is generated from `parameters.c`; keep the in-source description accurate.
- An option that changes the physics (new flux term, new BC mode) needs: a smoke-tier test with the option enabled, a line in the relevant `docs/Explanations/` page, and a JSON output field if the new quantity should be visible to PROTEUS.
- Never repurpose an existing option's meaning; add a new one and deprecate loudly.

## Vendored code

`cJSON.c` / `cJSON.h` are vendored third-party code: do not restyle, do not extend in place, exclude from coverage. If cJSON needs new capability, wrap it in `util.c`.

## Test marker discipline

Every test file must begin with a module-level `pytestmark = [pytest.mark.<tier>, pytest.mark.timeout(<budget>)]` (unit/30 s, smoke/60 s, integration/300 s, slow/3600 s). Per-function markers are additive but do not replace the module-level marker; PR CI runs `pytest -m "(unit or smoke) and not skip and not slow and not integration"` and any file missing the tier marker ships untested.

## Test quality (cross-reference)

Test-content rules (anti-happy-path, discriminating-value guards, physics-invariant tiering, `physics_invariant` / `reference_pinned` certification markers, the C-test-executable pattern, cached-run fixtures, adversarial-review trigger) live in [`spider-tests.md`](spider-tests.md). When reviewing tests, apply both files: this one for marker discipline and the review-pass gate, the deep-dive for the content contract.

## Sister rules (cross-link)

- [`.github/copilot-instructions.md`](../../copilot-instructions.md) "Testing Standards" -- high-level rules visible to all readers. Repo-root `CLAUDE.md` is a symlink to this file.
- [`spider-tests.md`](spider-tests.md) -- test quality deep-dive; the canonical source for anti-happy-path patterns and the validation certification markers.
