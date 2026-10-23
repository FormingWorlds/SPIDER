# SPIDER test instructions

<!-- fwl-tests-core:begin sha256=0d210e346c572a96 -->
## Test rules shared by the PROTEUS ecosystem

Each test file starts with a module-level tier marker and a timeout. CI selects tests by marker, so a file without one runs in no CI job; the timeout stops a hang, it is not a target.

```python
pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]
```

| tier | what it tests | timeout |
|---|---|---|
| `unit` | Python logic with the heavy physics mocked; aim for < 100 ms | 30 s |
| `smoke` | the real binaries or solvers, one step, low resolution | 60 s |
| `integration` | several modules coupled | 300 s |
| `slow` | full physics validation | 3600 s |

Each test carries exactly one tier marker, so that the tier filters select it in the one CI job meant for it; a function marker for a second tier breaks that. Split a file whose tests need different tiers. `skip` excludes a test from every CI job.

Every new test covers an edge case (a boundary value, an empty input, an extreme physical parameter), exercises the error contract (a documented exception with the check that no side effect ran, a guard, a clamp, or the limit input of the formula), and asserts values that do not follow trivially from the implementation. A pinned value of 1 that every exponent reproduces checks nothing.

`python tools/check_test_quality.py --check` fails when the count of any rule rises above `tools/test_quality_baseline.json`; the offenders it prints are the first few of that rule in the tree, not necessarily yours. The rules: a file without a tier marker, a test without a docstring, a test with one assertion or none, a weak assertion as the only one (`is None`, `is not None`, `> 0`, `len(...) > 0`, `isinstance`), `==` next to a non-zero float literal, and an optional dependency imported without `pytest.importorskip`. `bash tools/validate_test_structure.sh` runs the repository's own structure check; the repository part of this file says what it checks.

Physics tests carry markers so their coverage is tracked apart from line coverage:
- `@pytest.mark.physics_invariant` on each test function that asserts a conservation law, a bound (T > 0, fractions in [0, 1]), a monotonicity or symmetry, or a pinned value with a discrimination guard. The marker goes on the function, not the module: structural tests in the same file do not carry it.
- `@pytest.mark.reference_pinned` (together with `physics_invariant`) on a test that pins a published benchmark, an analytical limit or a cross-implementation result; cite the paper, table or figure in the docstring.
- A discrimination guard asserts that the most plausible wrong formula (a missing factor, a swapped exponent, the wrong unit) gives a result outside the tolerance of the pinned value.

Floats: compare with `pytest.approx` or `np.testing.assert_allclose` and a tolerance you can justify from the method, not the one that makes the test pass.

Mocks: mock at the narrowest scope (the one external call), and return physically plausible values, so the code under test runs its real branches. Set random seeds and write files only under `tmp_path`.

A module-level constant read from an environment variable at import time does not change with `monkeypatch.setenv`; patch the constant with `monkeypatch.setattr`.
<!-- fwl-tests-core:end -->

## SPIDER specifics

Structure: `<file>.c` is tested in `tests/test_<file>.py` for every physics source; the exceptions are `test_regression.py` (full runs against the frozen references in `tests/expected_output/`) and `test_plot_spider_lite.py` (for `py/plot_spider_lite.py`); a cross-implementation check against Aragog would be `slow`. `bash tools/validate_test_structure.sh` checks that every test carries at most one of `unit`, `smoke`, `integration` and `slow` (module, class or function), and `skip` when it carries none, and that every physics source has its test file; its source lists mirror `tools/check_test_quality.py`, keep them in sync.

Tiers here: `unit` runs the C test executables of `tests/c/` and Python-side checks, under 1 s each because every executable pays `PetscInitialize` (timeout 30 s); `smoke` runs the real `spider` binary for a few macro steps at n = 50, under 30 s on a development machine with a 120 s timeout for slower CI runners; `integration` (300 s) and `slow` (3600 s) run in the nightly. PR CI runs `pytest -m "(unit or smoke) and not skip and not slow and not integration"`. The tests need the built binary and `make tests_c`; without them the fixtures skip with a message, and they need `proteus-mpl` for the `validation_plot` fixture.

### No Python source to mock

- Most SPIDER functions take PETSc types and cannot be called from Python. A pure evaluator is tested through a small C executable `tests/c/test_<area>.c` (built by `make tests_c`): it calls `PetscInitialize`, evaluates at the inputs the wrapper passes (or fixed probe points), prints one JSON object of `name: value` pairs and exits nonzero on an internal failure (missing table, PETSc error). The pytest wrapper (`c_test` fixture, unit tier) makes every assertion in Python, where the linter and the Validation pages see the tolerances.
- Full runs are expensive: share them through the session-scoped cached-run fixtures of `tests/conftest.py`, keyed by options; a new configuration adds a cached key with the smallest `-nstepsmacro` and `-n` that exercise the contract; cached-run tests are `smoke`; a restart test (`-IC_INTERIOR 2`) copies the cached output to `tmp_path` first.
- Options files under `tests/opts/` are the run configurations; per-test overrides are minimal `-flag value` pairs. Never assert only on the exit code when JSON output exists.
- `matplotlib`, `aragog` and `bibtexparser` are the optional dependencies the linter knows (`OPTIONAL_DEPS`); the binary and the C executables are no Python imports, their absence is a fixture skip.

### Physics sources and invariants

Each test of a physics source asserts at least one of: conservation (mantle mass closure `mass_liquid + mass_solid = mass_mantle` at every output; shell masses times density integrating to the mantle mass; the surface flux equal to the interior heat extraction plus sources in quasi-steady cooling); bounds (T, P, entropy, viscosity, density, heat capacity positive; melt fraction and global melt fraction in [0, 1]); monotonicity (pressure increasing with depth, density non-decreasing with depth for a stable profile, liquidus above solidus, total entropy non-increasing without heat sources); or a pinned value with a discrimination guard. Utility sources are exempt from this rule only. Each physics source has at least one `physics_invariant` and one `reference_pinned` test and a page in `docs/Validation/`; the [Validation overview](../docs/Validation/index.md) lists every case, and `python tools/check_test_quality.py --reference-pinned-status` lists the gaps.

### Edge cases and discriminating values

- The plausible bugs here also include a scaling slip (nondimensional against SI, years against seconds, bar against Pa), an off-by-one node index, and a wrong path (melt against solid table, Adams-Williamson against external mesh, conventional against constant mixing length): the guard of a pinned value includes a value that separates the chosen path from its sibling.
- Read JSON fields as SI (`values * scaling`) before a comparison, and name the unit in a comment; a nondimensional value is order one and looks plausible.
- Grey-body flux: a surface temperature well above `teqm`, so a T^3 slip misses by orders of magnitude; Adams-Williamson: check the surface and the core-mantle boundary, not the surface alone; interpolation: query off-node; two-phase blending: distinct end-members, both limits and one interior point.
- `-gravity` is negative by convention: a test with the wrong sign can pass a loose tolerance; use a tight one and a guard on the gradient direction.
- Regression comparisons against `tests/expected_output/` use rtol = atol = 1e-5 (native mesh) and 2e-3 (external mesh, midpoint-rule shell masses). Changing a frozen reference needs a pull request that explains the physics change and updates `docs/Validation/`.
- SPIDER runs are deterministic (serial CVODE, fixed tolerances); do not add randomness. Run output goes to `tmp_path`, never into the repository tree.

### Docstrings and names

The file docstring names the C source (`Tests for <file>.c`), the invariants and contract clauses, and links `docs/How-to/build_tests.md`. Each test docstring states the physical scenario or contract clause; a comment says why an input, a node count or a tolerance was chosen. Names describe behaviour (`test_pressure_increases_monotonically_with_depth`, not `test_mesh`); parametrize ids name the physical scenario (fully molten, mixed phase, external mesh).

### Coverage gates

C line coverage comes from gcov and gcovr on `--coverage` builds, `cJSON.c` excluded. The fast gate (`[tool.spider.coverage_fast]`, unit and smoke, every pull request) and the full gate (`[tool.spider.coverage_full]`, all tiers, nightly) only move up, to at most 90 % (`tools/update_coverage_threshold.py --target fast|full`, `ECOSYSTEM_CEILING`). A new pure evaluator extends a C test executable and its wrapper; a new option path gets a smoke run asserting on JSON content; a new output field gets a closure or bound check. `python tools/check_test_quality.py --baseline` rewrites `tools/test_quality_baseline.json`; run it only after a change that reduced violations.

### Review of test changes

A pull request that adds or changes more than 50 lines under `tests/` (`git diff origin/main...HEAD -- tests/`, over all its commits) gets an independent review of its tests before merge; fixes go in a follow-up commit whose subject states the outcome. Recurring faults: an exit-code-only test, a nondimensional value pinned without its scaling, the gravity sign under a loose tolerance, an interpolation test at a table node, a solver run that stopped at a step limit and still wrote output (assert the step count and final time), a restart that writes into a cached run, a frozen reference regenerated to make a test pass, an optional import without `importorskip`, and a file without its module-level `pytestmark`.
