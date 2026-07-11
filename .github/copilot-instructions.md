# SPIDER AI Agent Guidelines

**Trust these instructions.** Only search if information is incomplete or found to be in error.

**Identity & Mission**: You are an expert Scientific Software Engineer working on the SPIDER module of the PROTEUS ecosystem.

## High-Level Instructions

> ### Rule files you MUST read on every session
>
> SPIDER keeps its Claude-Code rule files under `.github/.claude/rules/` (NOT the conventional repo-root `.claude/`, which is gitignored and so cannot be shared with collaborators). Claude Code does NOT auto-discover the rules at this unusual path. Read them explicitly at the start of every session and any time you open a related file:
>
> - [`.github/.claude/rules/spider-tests.md`](.claude/rules/spider-tests.md) -- test quality deep-dive: anti-happy-path patterns, discriminating-value guards, physics-invariant tiering, validation certification markers, the C-test-executable pattern, cached-run fixtures, adversarial-review trigger. **Required reading before editing any file under `tests/**` or any `.c`/`.h` source.**
> - [`.github/.claude/rules/spider-code-review.md`](.claude/rules/spider-code-review.md) -- review-pass gate, domain-aware physics review (nondimensional scaling boundaries, PETSc/SUNDIALS failure modes, JSON output contract, PROTEUS-coupling patterns). **Required reading before any code review pass.**
>
> These two files plus this one are the canonical sources of truth for testing rigor and review criteria. Together they enforce SPIDER's extreme-rigor stance on physics validity, anti-happy-path testing, and validation certification.

1. **Always** read the two rule files above plus the Testing Standards section below before any code change.
2. **Always** inform the user that you are reading in this file by printing a message at the start of your response: "(Read in copilot-instructions.md...)"
3. When creating a PR, **always** follow the PR template (`.github/pull_request_template.md`, if present) and ensure all sections are filled out with relevant information.
4. **Claude-specific**: `CLAUDE.md` is a symlink to this file. Session learnings, plans, and memories live in `~/.claude/projects/<repo>/memory/`; they do NOT live in this repository.

## Ecosystem Context

SPIDER solves the interior thermal evolution of rocky planets in the entropy formulation (Bower et al. 2018). It is one of the interior modules of the PROTEUS ecosystem, called by the main [PROTEUS](https://github.com/FormingWorlds/PROTEUS) coupled atmosphere-interior framework as a subprocess. SPIDER is also usable standalone for magma-ocean evolution studies.

Sister modules in the ecosystem: ARAGOG (interior, T-P formalism; the cross-check sibling), AGNI (atmospheric radiative transfer), SOCRATES (spectral radiative transfer), CALLIOPE (outgassing), JANUS (1D convective atmosphere), MORS (stellar evolution), VULCAN (atmospheric chemistry), ZEPHYRUS / BOREAS (atmospheric escape), Zalmoxis (interior structure; supplies external meshes to SPIDER), Obliqua (tidal evolution).

**Project Type**: Scientific simulation code (C, PETSc-based) with a Python test harness.

**Languages**: C (source), Python 3.12+ (tests, tooling, plotting).

**Size**: 27 C source files at repo root, ~20k LOC.

**Target Runtime**: Linux / macOS, serial (refuses MPI ranks > 1). PETSc >= 3.17 with SUNDIALS2.

## Build & Validation

### Environment Setup

**Prerequisites**:

1. A C compiler (gcc or clang) and GNU make.
2. PETSc with SUNDIALS2 (`--download-sundials2`). Two supported paths:
   - Installer: `./tools/get_petsc.sh` (downloads the PETSc 3.19.0 source archive from OSF and builds it; sets `arch-linux-c-opt` / `arch-darwin-c-opt`).
   - From source: clone `https://gitlab.com/petsc/petsc.git`, configure with `--with-fc=0 --with-cxx=0 --download-sundials2 --download-mpich --download-f2cblaslapack`.
3. Python 3.12+ with `pip install -r py/requirements.txt` plus `pytest pytest-timeout` for the test suite.

**Build**:

```bash
export PETSC_DIR=/path/to/petsc
export PETSC_ARCH=arch-linux-c-opt   # or arch-darwin-c-opt, arch-test, ...
make -j                              # builds the spider executable
make -j tests_c                      # builds the C test executables under tests/c/
```

Debug / sanitizer builds: `make clean; make -j CFLAGS_EXTRA="-O0 -fsanitize=address"`.

### Test Commands

**Run all PR-tier tests** (requires `spider` and the `tests/c/` executables to be built):

```bash
pytest -m "(unit or smoke) and not skip"
```

**Run by category** (matches CI):

```bash
pytest -m unit           # C test executables + Python-side checks (fast)
pytest -m smoke          # Short real spider runs, JSON invariant checks
pytest -m integration    # Full regression cases vs expected output (nightly)
pytest -m slow           # Long validation runs, cross-implementation checks (nightly)
```

**With C line coverage** (matches CI; requires a `--coverage` build):

```bash
make clean && make -j CFLAGS_EXTRA="--coverage" && make -j tests_c CFLAGS_EXTRA="--coverage"
pytest -m "(unit or smoke) and not skip"
gcovr --txt --exclude cJSON.c
```

**Coverage thresholds** (in `pyproject.toml`; raised manually with `tools/update_coverage_threshold.py`, which caps them at 90; the CI guard rejects any decrease):

- Fast gate (`[tool.spider.coverage_fast]`, unit + smoke, every PR): moves only upward toward **90%** (the PROTEUS-ecosystem ceiling).
- Full gate (`[tool.spider.coverage_full]`, unit + smoke + integration + slow, nightly): moves only upward toward **90%**.

**Validate test structure**:

```bash
bash tools/validate_test_structure.sh
```

**Test quality lint** (blocking on PRs):

```bash
python tools/check_test_quality.py --check
```

### Lint Commands

**Always run before committing** (Python files only; C sources keep their existing style):

```bash
ruff check tests/ tools/ py/
ruff check --fix tests/ tools/ py/
ruff format tests/ tools/ py/
```

**Pre-commit hook** (runs automatically on commit):

```bash
pre-commit install -f
```

### Validation Pipeline

**CI runs on PRs** (`.github/workflows/ci.yml`):

1. **Build**: PETSc from source at the pinned commit (cached across runs), then `make` and `make tests_c` with `--coverage`.
2. **Unit + smoke tests**: `pytest -m "(unit or smoke) and not skip and not slow and not integration"`.
3. **Fast coverage gate**: gcovr line coverage checked against `[tool.spider.coverage_fast].fail_under`.
4. **Test structure**: `bash tools/validate_test_structure.sh`.
5. **Test quality**: `python tools/check_test_quality.py --check` (blocking).
6. **Coverage ratchet guard**: rejects any PR that lowers either `fail_under` below `min(base_ref, 90.0)`.
7. **Lint**: `ruff check tests/ tools/ py/` and `ruff format --check tests/ tools/ py/`.
8. **Installer smoke**: `./tools/get_spider.sh` end-to-end.

**All must pass** before merge. Coverage thresholds move only upward (never decrease).

**Nightly CI** (`.github/workflows/nightly.yml`):

- The same cached PETSc build as the PR workflow.
- Full suite: `pytest -m "not skip"` on a `--coverage` build.
- gcovr line coverage checked against `[tool.spider.coverage_full].fail_under` and uploaded to Codecov.

## Project Layout

### Key Directories

- Repo root - C sources (flat layout, 27 files). Physics sources vs utility sources:
  - Physics: `atmosphere.c`, `bc.c`, `energy.c`, `eos.c`, `eos_adamswilliamson.c`, `eos_composite.c`, `eos_lookup.c`, `ic.c`, `interp.c`, `matprop.c`, `mesh.c`, `reaction.c`, `rheologicalfront.c`, `rhs.c`, `twophase.c`.
  - Utility: `cJSON.c` (vendored), `constants.c`, `ctx.c`, `dimensionalisablefield.c`, `eos_output.c`, `main.c`, `monitor.c`, `other.c` (uncompiled prototypes), `parameters.c`, `poststep.c`, `rollback.c`, `util.c`. The linter classifies fail-closed: a repo-root C source not on its utility denylist is physics-required.
- `tests/` - pytest suite. Each physics source has a 1:1 test file at `tests/test_<file>.py`. Cross-cutting tests (`tests/test_regression.py`, `tests/test_aragog_crosscheck.py`) are the exception.
  - `tests/c/` - C test executables (thin evaluators; assertions live in the pytest wrappers).
  - `tests/opts/` - options files for test runs.
  - `tests/expected_output/` - frozen regression references.
- `py/` - Python utilities (`plot_spider_lite.py`, `citations.py`).
- `tools/` - build / CI scripts (`get_petsc.sh`, `get_spider.sh`, `check_test_quality.py`, `update_coverage_threshold.py`, `validate_test_structure.sh`, `check_file_sizes.sh`, `generate_test_badges.py`, `generate_options_reference.py`).
- `lookup_data/` - EOS and melting-curve tables (1TPa-dK09-elec-free, RTmelt).
- `docs/` - Documentation (Zensical; Diátaxis structure), deployed to proteus-framework.org/SPIDER.
  - `Validation/<file>.md` - per-source-file inventory of `@pytest.mark.reference_pinned` tests.

### Configuration Files

- `pyproject.toml` - pytest config, coverage thresholds (fast + full gates), ruff rules. SPIDER is NOT a Python package; this file only configures the test harness and tooling.
- `Makefile` - build (includes PETSc conf); targets `all`, `tests_c`, `test`, `clean`.
- `mkdocs.yml` - documentation configuration (used by Zensical).
- `.github/workflows/` - CI / CD pipelines
  - `ci.yml` - PR validation (build + unit/smoke + lint + test-quality + ratchet guard + installer smoke)
  - `nightly.yml` - full suite with source-built PETSc and coverage upload
  - `docs.yaml` - documentation build and deploy
  - `publish-test-badges.yml` - test-count badges
  - `release-guard.yml` - tag vs `version.h` consistency check on release

### Entry Points

- **Binary**: `./spider -options_file <file.opts> [-flag value ...]`. With no arguments it runs the default options file. Key options: `-n` (nodes), `-nstepsmacro`, `-dtmacro`, `-outputDirectory`, `-IC_INTERIOR` (1 fresh, 2 restart).
- **Output**: one JSON file per macro step in `<outputDirectory>/<time_years>.json`, dimensionalisable fields carrying `values`, `scaling`, `units`.
- **All runtime options**: consumed in `parameters.c`; the generated reference lives at docs Reference/options.
- **PROTEUS coupling**: PROTEUS invokes the binary as a subprocess (`src/proteus/interior_energetics/spider.py` in the PROTEUS repo).

## Testing Standards

SPIDER is scientific simulation code, so the test suite is held to physics-grade rigor. The rules below are the contract; the deep-dive (anti-happy-path patterns, discriminating-value guards, certification markers, C-test-executable pattern, adversarial-review trigger) lives in [`.github/.claude/rules/spider-tests.md`](.claude/rules/spider-tests.md). Read that file before editing any test file or any C source. The two files must be kept in sync; if you change one, mirror the change in the other.

### Structure

- Tests mirror source 1:1: `<file>.c` -> `tests/test_<file>.py` for every physics source. Utility sources are exempt. Cross-cutting tests (`test_regression.py`, `test_aragog_crosscheck.py`) are the exception, not the rule.
- Framework: `pytest` exclusively in the `tests/` directory. C test executables under `tests/c/` are thin evaluators driven by their pytest wrappers; numeric pins, tolerances, and discrimination guards live in the Python wrapper where the linter sees them.

### Markers and the module-level marker rule

Tier markers, with their CI surface and per-test wall-time budgets:

| Marker | What it tests | Speed budget | When CI runs it |
|---|---|---|---|
| `@pytest.mark.unit` | C test executables, Python-side logic, data-table checks | < 1 s per test | Every PR |
| `@pytest.mark.smoke` | Short real `spider` runs (few macro steps, n=50), JSON invariants | < 30 s per test | Every PR |
| `@pytest.mark.integration` | Full regression cases vs frozen expected output | Minutes per test | Nightly only |
| `@pytest.mark.slow` | Long validation runs, cross-implementation checks | Up to hours per test | Nightly only |
| `@pytest.mark.skip` | Placeholder, deliberately disabled | n/a | Never |

**Mandatory module-level marker** (no exceptions): every test file begins with

```python
pytestmark = [pytest.mark.<tier>, pytest.mark.timeout(<budget>)]
```

with timeouts: 30 s for unit, 60 s for smoke, 300 s for integration, 3600 s for slow. Per-function markers are additive but do not replace the module-level marker. CI runs `pytest -m "(unit or smoke) and not skip and not slow and not integration"`; tests without a tier marker are invisible to CI. The `pytest-timeout` ceiling is a defensive net against future regressions that introduce a hang.

The `unit` budget is < 1 s rather than the ecosystem's usual < 100 ms because a C test executable pays `PetscInitialize` startup on every invocation; the cost is fixed overhead, not physics.

### Physics validity

Every test on a **physics source** must assert at least one of:

- **Conservation**: mantle mass closure (`mass_liquid + mass_solid = mass_mantle`), energy flux consistency at interfaces, per-shell mass consistency between mesh and density.
- **Positivity / boundedness**: T > 0 K, P > 0 Pa everywhere; melt fraction phi in [0, 1]; viscosity positive; entropy positive.
- **Monotonicity or symmetry**: pressure increasing with depth; entropy non-increasing during secular cooling with no heat sources; liquidus above solidus at every pressure.
- **Pinned numeric value with a discrimination guard**: a closed-form value (Adams-Williamson profile, grey-body flux) or table entry pinned via `pytest.approx`, accompanied by explicit assertions that wrong-formula results would differ by more than the tolerance.

Utility sources are **exempt** from the physics-invariant requirement but still subject to the anti-happy-path rules.

Tag every test that asserts a physical invariant with `@pytest.mark.physics_invariant`. Per-source-file granularity: each physics source needs at least one such test in `tests/test_<file>.py`.

### Reference-pinned validation

Tag tests that pin against a published benchmark, an analytical limit, or a cross-implementation cross-check with `@pytest.mark.reference_pinned`. Each physics source must have at least one such test. The anchor is recorded in `docs/Validation/<file>.md` (created when the first reference_pinned test for that source lands). `python tools/check_test_quality.py --reference-pinned-status` reports the punch list.

### Anti-happy-path rules (every new test)

Every new test function MUST include:

1. **At least one edge case** (boundary value, empty input, extreme physical parameter).
2. **At least one path that exercises the error contract** (documented exception, guard return, graceful clamp; for closed-form C evaluations, exercise a limit input and assert the mathematical invariant).
3. **Assertion values that are NOT trivially derivable from the implementation**: discriminating numeric pins or property-based assertions.

**Forbidden patterns** (flagged by `tools/check_test_quality.py`):

- Single-assert test functions.
- Standalone weak assertions (`assert result is not None`, `assert result > 0`, `assert len(result) > 0`, `assert isinstance(result, dict)`) as the only meaningful check.
- Tests with no function-level docstring.
- Tests using `==` adjacent to float literals.
- Tests asserting on a fixture's implicit default.

### Float and numerical comparison

NEVER use `==` for floats. Use `pytest.approx(val, rel=1e-5)` or `np.testing.assert_allclose(...)`. For pinned numeric values, include a **discrimination guard**: a follow-up `assert` showing the wrong-formula value would differ by more than the tolerance. See `spider-tests.md` Section 2 for the canonical pattern.

### Real runs instead of mocks

There is no Python source to mock: unit tests call C test executables, smoke and slower tiers run the real binary. The discipline transfers as follows:

- Share expensive runs through the session-scoped cached-run fixtures in `tests/conftest.py`; never launch a fresh multi-step run for an assertion a cached run already supports.
- Keep per-test option overrides minimal and explicit so the exercised code path is obvious.
- Never assert only on the exit code when JSON output is available; exit-code-only tests hide physics regressions.

### Optional-dependency imports

Any test that imports an optional dependency (`matplotlib`, `aragog`, `bibtexparser`) MUST call `pytest.importorskip('<dep>')` at module top. CI installs a minimal Python environment; tests that import optional deps unconditionally will fail to collect.

### Voice rule for test artifacts

The repo-wide voice rule (zero AI-process disclosure in any public artifact) applies to test code with the same strictness as to source. Scope: test-skip reasons, test-file / function docstrings, test-function / class names, parametrize ids, log-capture assertions, **commit messages on test-touching commits, pull-request titles and bodies on test-touching PRs**, GitHub Actions job / step names, inline C source comments, and shipped log strings. Out of scope: the rule documents themselves (this file, `spider-tests.md`, `spider-code-review.md`) may legitimately name the procedures they define.

Banned phrases inside in-scope artifacts: "audit", "review pass", "adversarial review", AI-roadmap labels (`Phase X`, `Stage X.Y`, `Iteration N`, `T1.x`, `Group A/B/C/D` when AI-organized), `claude-config/...` paths, "Generated with Claude", AI-tool names, em-dashes, en-dashes (except bibliographic page ranges).

Write the OUTCOME, never the PROCESS.

### Speed and determinism

- Unit tests: < 1 s wall-time each (PetscInitialize overhead included).
- Smoke tests: < 30 s; use the smallest `-nstepsmacro` and `-n` that still exercise the contract.
- SPIDER runs are deterministic (serial CVODE with fixed tolerances); regression comparisons use rtol 1e-5 against frozen references, 2e-3 for the external-mesh pathway (midpoint-rule quadrature vs analytical integrals).
- Use `tmp_path` (pytest fixture) for run output directories; never write into the repo tree.

### Documentation per test

- File-level docstring: name the C source under test, list the invariants and contract clauses the file exercises.
- Function-level docstring: state the physical scenario or contract clause being verified. Required (lint-enforced).
- Inline comments: explain **why** a specific input or tolerance was chosen.

### Independent review trigger

A pull request that adds or substantially modifies > 50 lines of test code across all its commits triggers an independent review pass before merge. The denominator is PR-level (`git diff origin/main...HEAD -- 'tests/**'`); splitting into many sub-50-line commits does not dodge the trigger.

### Tooling

- Validate test structure: `bash tools/validate_test_structure.sh`
- Test-quality lint: `python tools/check_test_quality.py --check`
- Baseline regeneration (after a deliberate sweep): `python tools/check_test_quality.py --baseline`
- Reference-pinned audit: `python tools/check_test_quality.py --reference-pinned-status`
- Coverage ratchet (one-way, capped at 90): `python tools/update_coverage_threshold.py --target fast|full`
- Format / lint (Python only): `ruff format tests/ tools/ py/`, `ruff check tests/ tools/ py/`

### Coverage architecture

SPIDER measures C line coverage with gcov/gcovr (`--coverage` builds; `cJSON.c` excluded as vendored code):

| Gate | Tests included | Target | Enforced |
|---|---|---|---|
| Fast gate (`tool.spider.coverage_fast.fail_under`) | unit + smoke | Moves only upward toward **90%** | Every PR |
| Full gate (`tool.spider.coverage_full.fail_under`) | unit + smoke + integration + slow | Moves only upward toward **90%** | Nightly |

Both gates are raised manually with `tools/update_coverage_threshold.py`, which caps them at 90 (`ECOSYSTEM_CEILING = 90.0`); neither may be decreased. The CI guard in `ci.yml` rejects any PR that lowers either `fail_under` below `min(base_ref, 90.0)`.

## Safety & Determinism

- SPIDER is deterministic; do not introduce randomness into tests.
- Do not generate large output files in tests; short runs with `tmp_path` output directories only.

## Code Quality

**C style**: match the surrounding code (PETSc conventions, `PetscErrorCode` returns, `PetscFunctionBeginUser`/`PetscFunctionReturn`, CHKERRQ error propagation). No reformatting sweeps.

**Python style** (enforced by ruff): line length < 96, snake_case, NumPy docstrings.

**Pre-commit**: runs whitespace hooks, ruff on Python files, and the file-size cap. Fix issues before committing.

## Common Workflows

### Making a Code Change

1. **Create branch**: `git checkout -b <initials>/<short-description>`.
2. **Make changes** in the C sources.
3. **Build**: `make -j && make -j tests_c`.
4. **Write / update tests** in `tests/test_<file>.py` (mirror structure).
5. **Run tests locally**: `pytest -m "(unit or smoke) and not skip"`.
6. **Lint**: `ruff check --fix tests/ tools/ py/ && ruff format tests/ tools/ py/`.
7. **Validate structure**: `bash tools/validate_test_structure.sh`.
8. **Test quality**: `python tools/check_test_quality.py --check`.
9. **Commit**: plain-language subject, first-person voice, no AI-process disclosure.
10. **Push**: CI runs automatically on PR.

### Adding a New Physics Source

1. Create `<file>.c` + `<file>.h`, add to `SRC_C` in the Makefile.
2. Create `tests/test_<file>.py` with module-level `pytestmark`.
3. Add at least one `@pytest.mark.physics_invariant` test asserting one of the four invariant families.
4. Plan a `@pytest.mark.reference_pinned` test (anchor: paper, analytical limit, or cross-check); create `docs/Validation/<file>.md` when it lands.
5. If the source has pure evaluator functions, add a C test executable under `tests/c/` (see `spider-tests.md` Section 4).
6. Run the full PR checks locally.

### Debugging Test Failures

```bash
pytest -v --showlocals                          # Verbose with local variables
pytest -x                                       # Stop at first failure
pytest tests/test_<file>.py::test_function      # Run specific test
make clean; make -j CFLAGS_EXTRA="-O0"          # Debug build for lldb/gdb
```

## Documentation References

- **Testing rules**: `.github/.claude/rules/spider-tests.md`, `.github/.claude/rules/spider-code-review.md`
- **Test how-to**: `docs/How-to/build_tests.md`
- **Installation**: `docs/How-to/installation.md`, `docs/How-to/quadruple_installation.md`
- **Concepts**: `docs/Explanations/` (thermodynamics, transport, material properties, boundary conditions, ...)
- **Releasing**: `docs/How-to/releasing.md`

## Project memory and session learnings

Session-specific knowledge (debugging logs, design rationale, sprint focus) lives outside this repository, in the Claude memory tree under `~/.claude/projects/<repo>/memory/`. The memory tree is per-user, sync-ready across machines, and not exposed in public commit history.

What still lives in this repository:

- Architectural decisions that affect every contributor: this file (`.github/copilot-instructions.md`).
- Test and review rules: `.github/.claude/rules/spider-tests.md` and `.github/.claude/rules/spider-code-review.md`.
- Per-PR rationale: PR descriptions.
- Per-commit rationale: commit messages.
- Module-level scientific validation: `docs/Validation/<file>.md`.

Do not introduce a new in-repo "memory" or "decisions log" file. The four channels above are the contract.

---

## Quick Reference

```bash
# Build
export PETSC_DIR=/path/to/petsc PETSC_ARCH=arch-linux-c-opt
make -j && make -j tests_c

# Test
pytest -m "(unit or smoke) and not skip"

# Lint (Python only)
ruff check --fix tests/ tools/ py/
ruff format tests/ tools/ py/

# Validate
bash tools/validate_test_structure.sh
python tools/check_test_quality.py --check

# Coverage
make clean && make -j CFLAGS_EXTRA="--coverage" && make -j tests_c CFLAGS_EXTRA="--coverage"
pytest -m "(unit or smoke) and not skip" && gcovr --txt --exclude cJSON.c

# Serve docs locally
zensical serve
```

**Remember**: Trust these instructions. Only search if information is incomplete or found to be in error.

---

> **⚠️ FILE SIZE LIMIT: This file must stay below 500 lines.** Enforced by pre-commit hook (`tools/check_file_sizes.sh`). File located at `.github/copilot-instructions.md`.
