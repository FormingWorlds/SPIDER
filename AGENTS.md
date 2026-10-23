# SPIDER agent instructions

SPIDER solves the interior thermal evolution of rocky planets in the entropy formulation (Bower et al. 2018). It is C code on PETSc with SUNDIALS (CVODE), run serially (`main.c` refuses more than one MPI rank), with a Python test harness; PROTEUS runs the binary as a subprocess (`src/proteus/interior_energetics/spider.py`), and it also runs standalone. Before a first edit:

- Physics sources (repo root): `atmosphere.c`, `bc.c`, `energy.c`, `eos.c`, `eos_adamswilliamson.c`, `eos_composite.c`, `eos_lookup.c`, `ic.c`, `interp.c`, `matprop.c`, `mesh.c`, `reaction.c`, `rheologicalfront.c`, `rhs.c`, `twophase.c`. Utility sources: `cJSON.c` (vendored), `constants.c`, `ctx.c`, `dimensionalisablefield.c`, `eos_output.c`, `main.c`, `monitor.c`, `other.c` (not compiled), `parameters.c`, `poststep.c`, `rollback.c`, `util.c`. The test linter treats a root C source that is not on its utility list as a physics source.
- Tests for `<file>.c` go in `tests/test_<file>.py`; the test rules are in `tests/AGENTS.md`.
- These commands decide whether a change is ready (CI runs them, with a `--coverage` build):

```bash
export PETSC_DIR=/path/to/petsc PETSC_ARCH=arch-linux-c-opt   # or arch-darwin-c-opt
make -j && make -j tests_c
pytest -m "(unit or smoke) and not skip"
ruff check --fix <changed .py files> && ruff format <changed .py files>
bash tools/validate_test_structure.sh
python tools/check_test_quality.py --check
python tools/generate_options_reference.py --check
python tools/agents/check_agents_md.py
```

C line coverage as CI measures it, and debugging:

```bash
make clean && make -j CFLAGS_EXTRA="--coverage" && make -j tests_c CFLAGS_EXTRA="--coverage"
pytest -m "(unit or smoke) and not skip" && gcovr --txt --exclude cJSON.c
pytest -x -v --showlocals tests/test_<file>.py::test_function
make clean; make -j CFLAGS_EXTRA="-O0 -fsanitize=address"   # debug or sanitizer build
```

<!-- fwl-core:begin sha256=1adfa510a4f117ec -->
## PROTEUS ecosystem rules

PROTEUS couples separate module repositories into one model of the evolution of rocky planets and their atmospheres. Its config selects one module per process; the config values are the lowercase names:

- `interior_energetics.module`: `aragog`, `spider` (or the built-in `boundary`); `interior_struct.module`: `zalmoxis`, `spider`
- `atmos_clim.module`: `agni`, `janus`, both with SOCRATES spectral radiative transfer
- `outgas.module`: `calliope`, `atmodeller`; `atmos_chem.module`: `vulcan`
- `star.module`: `mors`; `escape.module`: `zephyrus`, `boreas`; `orbit.module` (tides): `obliqua`, `lovepy`
- fwl-io downloads the reference data the modules use

A module change to anything PROTEUS calls or reads (a function signature, a config key, an output column, a unit) can break the coupled model while the module's own tests pass. Search `src/proteus/` in PROTEUS for the name before you change it, and name the affected PROTEUS call sites in the pull request.

### Physics and numerics

- Units differ between and within modules: MORS and VULCAN use cgs; CALLIOPE and atmodeller work with pressures in bar; AGNI takes surface pressure in bar at setup and holds Pa inside; PROTEUS states the unit of every `hf_row` key in `GetHelpfileKeys` (`src/proteus/utils/coupler.py`: atmospheric pressures in bar, interior pressures in Pa, model time in years, orbital periods in s), and its config reference pages state each key's unit (for example stellar mass in M_sun, initial partial surface pressures in bar, stellar age in Gyr). State the unit of every physical quantity in its docstring and convert explicitly at the boundary: a unit mismatch between two modules passes the tests of both and shows only in the coupled run.
- A physics test must fail for the most plausible wrong formula: check a conservation law, a bound, a monotonicity, or a published or analytical value, and assert that the wrong result falls outside the tolerance.
- Take each physical constant from one source per repository (in Python `scipy.constants` or the module's constants file). Two retyped values of one constant differ at round-off and hide real differences between code paths.
- Do not loosen a solver tolerance, a conservation check or a clamp to make a run or a test pass. Find the cause; a loosened check also hides the next defect.

### Validation

A new or changed physics routine gets the validation cases named in its confirmed plan: an analytical law, a published figure or table, or a cross-code check. Each case is a `reference_pinned` test that runs the real code on real data, with no mocks, asserts the tolerance, and writes its light and dark plot through the `validation_plot` fixture of proteus-mpl. `pytest -m reference_pinned --validation-plots` makes all plots again. Line plots are SVG, maps are AVIF; each file is at most 60 kB, under `docs/assets/validation/`. Each case has a subsection on its page in the Validation tab, with the reference, the tolerance, the test id and the command. Data read from a published figure comes from 2 independent figlab reads that agree within the stated error, as a CSV with its provenance under `tests/validation/data/`.

### Code

- Keep an inline comment block to 2 lines or fewer, and never more than 4, because a long block drifts from the code it describes. An explanation that needs more goes in the docstring, the commit message or the pull-request description.

### Branches and pull requests

- Work on a feature branch `<initials>/<short-description>`; `main` changes only through a reviewed pull request.
- Fill every section of the repository's pull-request template, where it has one.
- Before you push, run the checks listed at the top of this `AGENTS.md` and in `tests/AGENTS.md`.

### Where knowledge goes

Rules for every contributor go in the `AGENTS.md` files, the reason for a change in its commit message and pull-request description, and the scientific validation of a module in its `docs/Validation/` pages, where the repository has them. Do not add memory, notes or decision-log files to the repository: nobody maintains them, and they go stale.
<!-- fwl-core:end -->

<!-- fwl-voice:begin sha256=b4fe24baeef8b734 -->
### Commit messages and public text

Commit messages, pull-request text, code comments, docstrings, test names, test skip reasons, parametrize ids, log strings that ship with the code, and CI job and step names describe the change and the current state of the code. They name no tool used to write the change, carry no tool-attribution trailer, use no internal plan, phase or work-group labels, and use no em or en dashes (a page range in a citation is the exception).
<!-- fwl-voice:end -->

## Environment

A C compiler and GNU make; PETSc with SUNDIALS2, from `./tools/get_petsc.sh` (PETSc 3.19.0 from Zenodo, with the DataverseNL mirror as the fallback, SHA-256 checked) or from source (`--with-fc=0 --with-cxx=0 --download-sundials2 --download-mpich --download-f2cblaslapack`); Python with `pip install -r py/requirements.txt pytest pytest-timeout 'proteus-mpl>=1.4.0'`. `pyproject.toml` only configures the test harness and the tools; SPIDER is not a Python package. `pre-commit install -f` runs the whitespace hooks, ruff and the agent-file check. CI runs `ruff check` on `tests/`, `tools/` and `py/`; `ruff format` applies to the files a change touches, because older files are not formatted yet (`ruff format --check tests/ tools/ py/` exits 1 on the tree). Serve the docs with `zensical serve`. Installation, testing and release steps: `docs/How-to/installation.md`, `docs/How-to/test.md`, `docs/How-to/build_tests.md`, `docs/How-to/releasing.md`.

Style: C code follows the surrounding PETSc conventions (`PetscErrorCode` returns, `PetscFunctionBeginUser`/`PetscFunctionReturn`, `CHKERRQ`); no reformatting sweeps. Python: lines of at most 96 characters (ruff), snake_case, NumPy docstrings.

Entry point: `./spider -options_file <file.opts> [-flag value ...]` (no arguments: the default options file); key options `-n`, `-nstepsmacro`, `-dtmacro`, `-outputDirectory`, `-IC_INTERIOR` (1 fresh, 2 restart). Output: one JSON file per macro step, `<outputDirectory>/<time_years>.json`, each field with `values`, `scaling` and `units`. All runtime options are read in `parameters.c`; `docs/Reference/options.md` is generated from it.

## CI

- `ci.yml` (every pull request): PETSc built from the pinned source (cached), `make` and `make tests_c` with `--coverage`; `ruff check tests/ tools/ py/`; `validate_test_structure.sh`; `check_test_quality.py --check` (blocking); `generate_options_reference.py --check`; a guard that rejects lowering `[tool.spider.coverage_fast]` or `[tool.spider.coverage_full]` `fail_under` below `min(base, 90)`; `pytest -m "(unit or smoke) and not skip and not slow and not integration"` with the fast gate on gcovr line coverage; the agent-file check; and an installer job that runs `./tools/get_spider.sh` and the smoke tier on the installed build.
- `nightly.yml`: the same PETSc build, `pytest -m "not skip"` on a `--coverage` build, the full gate, upload to Codecov.
- `docs.yaml` builds and deploys the docs; `publish-test-badges.yml` refreshes the test-count badges; `release-guard.yml` checks the tag against `version.h`.

## Physics and coupling contract

- SPIDER solves the nondimensional problem; the scalings (`-entropy0`, `-radius0`, `-time0`, `-pressure0` where used) convert to SI. Apply the scaling once on input and invert it once on output: a double or a missed scaling gives an error of the size of the scaling that can look plausible. A new JSON field is a `DimensionalisableField` with correct `scaling` and `units`, never a raw internal value. Option defaults in `parameters.c` state their unit (SI unless noted; `-dtmacro` in years; `-gravity` negative, pointing inward, a recurring trap for hydrostatic code).
- Temperature, pressure, entropy, viscosity, density, heat capacity and thermal expansivity stay positive after every lookup and blend; pressure increases with depth; the melt fraction stays in [0, 1] (the two-phase blending and the `matprop_smooth_width` smoothing in `eos_composite.c` and `energy.c` clamp and never extrapolate); the loaded tables must have the liquidus above the solidus at every pressure (the code does not check it and `eos_composite.c` divides by their difference; `tests/test_eos_composite.py` checks it at one pressure); `mass_liquid + mass_solid = mass_mantle`. An out-of-range table lookup fails loudly or clamps with a warning; a new lookup goes through the guarded path.
- PETSc and SUNDIALS: every PETSc call has its return code checked as in the surrounding code; every create has its destroy on every exit path (a coupled run makes many macro steps). A change that alters stiffness (a new source term, a sharper property gradient) can degrade the CVODE steps silently: it needs a smoke test on the step count or the final time. No parallel constructs.
- PROTEUS reads the JSON output only: `mass_liquid`, `mass_solid`, `mass_mantle`, `mass_core`, `temperature_surface`, `phi_global`, `Fatm`, `rheological_front_dynamic` (`depth`) and `rheological_front_phi`, the node arrays `phi_s`, `rho_s`, `radius_b`, `visc_b`, `mass_s`, `temp_s`, `pressure_s`, `S_s`, `cp_s`, `Hradio_s`, `Htidal_s`, `Jconv_b`, `Jcond_b`, and `time_years`. Renaming or removing one of them, or changing its units or scaling, breaks PROTEUS: it needs the PROTEUS change, a pin update and a release note. New fields are additive. The restart path (`-IC_INTERIOR 2 -ic_interior_filename <json>`) reads what the binary writes; an output change comes with the reader change.
- PROTEUS retries a failed call up to 8 times, scaling `-dtmacro` by 0.3 and the CVODE tolerances by 5 per attempt, so a more fragile solver shows as more retries, not as a failure: check solver-adjacent changes at the strict tolerances (`-ts_sundials_atol/rtol 1e-8`).
- With `-MESH_SOURCE 1 -mesh_external_filename` the mesh and pressure profile come from Zalmoxis; the reader checks the node counts and only warns when the radius or the core size differ by more than 1 percent (it does not check monotonicity), a change of the file format needs the PROTEUS writer change, and the Adams-Williamson mesh stays the fallback. PROTEUS passes `-coresize`, `-rho_core` and `-cp_core`; these values are authoritative, do not re-derive them when they are set. PROTEUS uses `-SURFACE_BC 4` (prescribed flux) and `-SURFACE_BC 1` (grey body); a change to either needs tests on both.
- A new runtime option is registered in `parameters.c` with a default, a unit comment and a range check where it applies; an option that changes the physics needs a smoke test with it set, a line in the matching `docs/Explanations/` page, and a JSON field if PROTEUS should see the quantity. Do not change the meaning of an existing option; add a new one.
- `cJSON.c` and `cJSON.h` are vendored: do not restyle or extend them; wrap new needs in `util.c`; they are excluded from coverage.

## Adding a physics source

1. Create `<file>.c` and `<file>.h` and add them to `SRC_C` in the `Makefile`; create `tests/test_<file>.py` with the module-level `pytestmark`.
2. Add at least one `physics_invariant` and one `reference_pinned` test; a pure evaluator gets a C test executable under `tests/c/`, added to `TEST_C_SRC` in the `Makefile` (only listed files are built).
3. Add `docs/Validation/<file>.md` with a subsection per case (reference, tolerance, test id, command), list the case in `docs/Validation/index.md` and add the page to the Validation nav of `mkdocs.yml`.

## Review

Check each change against these points and the physics and coupling contract above. `.github/copilot-instructions.md` holds a subset of this checklist for tools that read only that file; change them together.

- Positivity, pressure monotonic with depth, melt fraction in [0, 1], liquidus above solidus, mantle mass closure.
- Scaling applied once each way; new fields as `DimensionalisableField` with scaling and units; the `-gravity` sign.
- PETSc return codes checked, every create destroyed, serial only; stiffness changes covered by a smoke test.
- The JSON fields PROTEUS reads, the restart round trip, the external-mesh reader, the core options and both surface boundary conditions.
- Tests follow `tests/AGENTS.md`.
