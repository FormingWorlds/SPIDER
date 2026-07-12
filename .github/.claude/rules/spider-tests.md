# SPIDER Test Quality Rules

This file is the canonical deep-dive on test quality. The high-level summary lives in [`.github/copilot-instructions.md`](../../copilot-instructions.md) under "Testing Standards". The two files MUST stay in sync. If you change one, mirror the change in the other.

> **Discovery note.** SPIDER keeps its Claude-Code rule files under `.github/.claude/rules/` (not the conventional repo-root `.claude/`) so they can be tracked in git and shared across collaborators. Claude does NOT auto-discover them at this path; the repo-root `CLAUDE.md` (symlinked to `.github/copilot-instructions.md`) names this file and `spider-code-review.md` explicitly. **When opening or editing any file under `tests/**` or any C source, read this file first.**

Sister rule files:

- [`.github/copilot-instructions.md`](../../copilot-instructions.md): high-level rules, applied repo-wide.
- [`.github/.claude/rules/spider-code-review.md`](spider-code-review.md): review-pass gate, domain-aware code review (nondimensional scaling boundaries, PETSc/SUNDIALS failure modes, JSON output contract, PROTEUS-coupling patterns).

SPIDER is scientific simulation code and the test suite is held to physics-grade rigor. Tests exist to catch real bugs. A test that asserts the wrong thing, or that passes for the wrong reason, is worse than no test because it generates false confidence. The rules below codify what "real test" means here, adapted to a C code driven through a Python harness.

---

## 1. Anti-happy-path rules (every new test)

Every new test function MUST include:

1. **At least one edge case**: a boundary value (melt fraction phi = 0 or 1, the surface node, the core-mantle boundary node, the first or last table row), an empty or degenerate input, or an extreme physical parameter.
2. **At least one path that exercises the error contract**:
   - If the code under test has documented validation (the binary refuses options without `-options_file`, refuses MPI ranks > 1, errors on an out-of-range table lookup), test that the error fires AND that no partial output was produced.
   - If the code has no validation (closed-form evaluations: Adams-Williamson profile, grey-body flux, interpolation), exercise the **limit-input behavior** (e.g. the surface node where the AW profile reduces to the surface density; an interpolation query exactly at a node where the result is the node value) and assert the corresponding mathematical invariant.
   - "No validation in source therefore no error test" is not an exemption; the limit-input substitute is.
3. **Assertion values NOT trivially derivable from the implementation**: discriminating numeric pins (see Section 2) or property-based assertions (monotonicity, conservation, symmetry, boundedness).

### Forbidden patterns

These are flagged by `tools/check_test_quality.py` and rejected at PR time.

- **Single-assert test functions**. Two or more assertions per test; the second usually pins the invariant the first hand-waves over. Exception: a single assertion of a hard-fail invariant (mass closure within `1e-12`) is acceptable if the test is the only test of that invariant in the file.
- **Weak assertions when they stand alone as the sole meaningful check.** The shapes are:
  - `assert result is not None`
  - `assert result > 0`
  - `assert len(result) > 0`
  - `assert isinstance(result, dict)`
  - `assert result is None` where the function returns `None` implicitly

  Required carve-out: the three-class discrimination guard (Section 2) uses `assert val > 0` as the sign-error guard and `assert lo < val < hi` as the scale-error guard alongside a primary `pytest.approx(...)` pin. Those secondary lines are NOT flagged when paired with a stronger primary assertion in the same test. The linter applies the carve-out automatically: weak shapes are flagged only when the test has exactly one `assert` statement and that assertion is itself the weak shape.
- **Exit-code-only assertions when JSON output exists.** `assert proc.returncode == 0` alone is the subprocess analogue of `assert result is not None`. Parse the JSON and assert on physical content. The exit code check is fine as a first line, never as the only line.
- **Tests with no function-level docstring**. The docstring states which physical scenario or contract clause is being verified.
- **`==` adjacent to a float literal**. Use `pytest.approx(val, rel=...)` or `np.testing.assert_allclose(...)`.
- **Tests asserting on a fixture's implicit default**: trivially true; delete the test.

---

## 2. Discriminating test values

The test contract is: a regression that introduces a plausible bug must fail the test. "Plausible bug" means off-by-one exponent, wrong sign, swapped factor of 2, missing factor of pi, dimensionally-wrong unit, **wrong-scaling (nondimensional vs dimensional) slip**, off-by-one node indexing. Pick input values where the wrong result is far from the correct one.

### Bad / good examples

| Pattern | Bad (any-formula-passes) | Good (discriminates) |
|---|---|---|
| Adams-Williamson density `rho(r) = rhos * exp(beta * (R - r))` | Test at the surface only (`r = R`, any beta gives rhos) | Test at the surface AND the CMB; assert the ratio matches `exp(beta * depth)` so a sign-flipped or zeroed beta fails |
| Grey-body flux `F = sigma * emissivity * (T^4 - Teqm^4)` | `T = Teqm` (F = 0 for any exponent) | T well above Teqm so T^3 vs T^4 differ far beyond tolerance |
| 1D interpolation | Query at a table node (identity for any scheme) | Query off-node where linear vs nearest-neighbour differ; pin the linear value |
| Two-phase blending | phi = 0.5 with equal end-members (any weighting passes) | Distinct end-member values; check both limits AND one interior point |
| Nondimensional scaling | Assert a scaled value is "reasonable" | Multiply `values * scaling` from the JSON and pin the SI result |

### Discrimination guard (REQUIRED for pinned-value tests)

When a test pins a numeric value, include explicit assertions that the wrong-formula result would differ from the correct one for **each plausible bug class**. At minimum:

1. **Exponent or factor error** (off-by-one exponent, missing factor of 2 / pi / 4pi). `abs(val - wrong_value)` discriminates.
2. **Sign error** (`-x` vs `+x`; SPIDER's `-gravity` is negative by convention, a recurring source). `abs()` hides this; assert the sign explicitly.
3. **Unit or scaling error** (SI vs nondimensional, years vs seconds, bar vs Pa). Pin the absolute scale with the unit named in the comment; when reading JSON, always reconstruct SI as `values * scaling` before pinning.
4. **Wrong-path selection** (melt table vs solid table, conventional vs constant mixing length, AW mesh vs external mesh). When the code dispatches on an option, the guard MUST include a value that distinguishes the chosen path from a sibling path.

**Carve-out for conservation-style invariants.** When the primary assertion IS a conservation closure (`mass_liquid + mass_solid == pytest.approx(mass_mantle)`), the equality form already discriminates exponent / factor errors by construction. Sign and scale guards remain mandatory.

Canonical pattern:

```python
def test_grey_body_surface_flux_matches_stefan_boltzmann():
    """Pin the grey-body surface flux against sigma*(T^4 - Teqm^4) from the run JSON."""
    T_surf = json_field(out, 'temperature_surface')       # K, SI after scaling
    F_atm = json_field(out, 'Fatm')                       # W/m^2
    sigma = 5.670374419e-8                                # W m^-2 K^-4 (CODATA)
    expected = 1.0 * sigma * (T_surf**4 - 273.0**4)       # emissivity0 = 1, teqm = 273
    assert F_atm == pytest.approx(expected, rel=1e-6)
    # Exponent guard: a T^3 slip at T_surf ~ 2600 K is off by ~650x.
    wrong_cubed = sigma * (T_surf**3 - 273.0**3)
    assert abs(F_atm - wrong_cubed) > 0.5 * F_atm
    # Sign guard: the surface radiates outward, F_atm > 0 for a hot interior.
    assert F_atm > 0
    # Scale guard: magma-ocean fluxes are 1e4..1e7 W/m^2, not 1e-3 or 1e12
    # (a nondimensional value leaking through unscaled would sit near unity).
    assert 1e2 < F_atm < 1e9
```

The guard lines are mandatory whenever the test's primary assertion is a `pytest.approx` against a hand-calculated or published value. Property-based assertions do not need a separate guard because they are already discriminating across the input space.

---

## 3. Physics-invariant assertions (tiered)

### When required

Every test on a **physics source** must assert at least one of the four invariants below. Physics sources are:

```
atmosphere.c   bc.c   energy.c   eos.c   eos_adamswilliamson.c   eos_composite.c
eos_lookup.c   ic.c   interp.c   matprop.c   mesh.c   reaction.c
rheologicalfront.c   rhs.c   twophase.c
```

Per-source-file granularity: each physics source needs at least one `@pytest.mark.physics_invariant` test and at least one `@pytest.mark.reference_pinned` test in `tests/test_<file>.py`.

Utility sources are exempt from the physics-invariant requirement but still subject to all anti-happy-path rules:

```
cJSON.c (vendored)   constants.c   ctx.c   dimensionalisablefield.c   eos_output.c
main.c   monitor.c   parameters.c   poststep.c   rollback.c   util.c
```

### The four invariant families

1. **Conservation**
   - Mantle mass closure: `mass_liquid + mass_solid ≈ mass_mantle` at every output step.
   - Per-shell mass consistency: shell masses from the mesh times density integrate to the mantle mass.
   - Energy flux consistency: the surface flux equals the interior heat extraction rate plus source terms within tolerance during quasi-steady cooling.
2. **Positivity / boundedness**
   - T > 0 K, P > 0 Pa at every node; entropy positive.
   - Melt fraction phi in [0, 1] at every node; global melt fraction in [0, 1].
   - Viscosity, density, heat capacity positive at every node.
3. **Monotonicity or symmetry**
   - Pressure strictly increasing with depth; density non-decreasing with depth for a stable profile.
   - Liquidus above solidus at every pressure in the loaded tables.
   - Secular cooling with no internal heating: total entropy non-increasing between macro steps.
4. **Pinned numeric value with a discrimination guard**: see Section 2. Acceptable as the sole invariant when a closed-form result or published table value is the contract.

Property-based assertions are preferred over point-value pins when both are possible.

### Validation certification markers

- **`@pytest.mark.physics_invariant`** -- this test asserts at least one of the four invariants. Tag every qualifying test in a physics-source test file.
- **`@pytest.mark.reference_pinned`** -- this test pins behavior against a **published benchmark** (cite explicitly in the test docstring, e.g. Bower et al. 2018 evolution figures, Andrault et al. 2011 liquidus, Hirschmann 2013 solidus), an **analytical limit** (Adams-Williamson profile, Stefan-Boltzmann grey-body flux, interpolation identity at nodes), or a **cross-implementation cross-check** (SPIDER vs Aragog at the same initial condition).
  - **Per-source-file**: each physics source must have at least one `reference_pinned` test in `tests/test_<file>.py`, recorded in `docs/Validation/<file>.md`.
  - **Status report**: `python tools/check_test_quality.py --reference-pinned-status` prints the punch list.

Both markers are registered in `pyproject.toml`. They do not gate CI on their own.

---

## 4. The C test executable pattern

Most SPIDER functions take PETSc types (`Ctx`, `Vec`, `DM`) and cannot be called from Python. Pure evaluator functions (interpolation, EOS evaluations, two-phase blending) are tested through small C executables under `tests/c/`:

- Each executable (`tests/c/test_<area>.c`) links against the SPIDER object files (`make tests_c`), calls `PetscInitialize`, evaluates the functions under test at inputs chosen by the pytest wrapper (passed as command-line arguments where practical, or hard-coded probe points otherwise), and prints a single JSON object of `name: value` pairs to stdout. Exit code 0 on evaluation success, nonzero on internal failure.
- The pytest wrapper (`tests/test_<file>.py`, unit tier) runs the executable via the `c_test` conftest fixture, parses the JSON, and makes ALL assertions in Python: `pytest.approx` pins, discrimination guards, invariant checks. The C side computes; the Python side judges.
- Rationale: tolerances, anchors, and guards stay in Python where `tools/check_test_quality.py` lints them and where `docs/Validation/` cites them; the C side stays free of assertion logic that the linter cannot see.
- A C executable that cannot initialize (missing data table, PETSc error) must exit nonzero so the wrapper reports a hard failure, never a silent pass.

When adding a new pure evaluator to a physics source, extend the matching `tests/c/test_<area>.c` (or add a new one and wire it into the Makefile `tests_c` target) rather than testing only through full binary runs.

---

## 5. Cached-run fixtures

Full `spider` runs are the expensive resource. `tests/conftest.py` provides session-scoped cached fixtures (one short blackbody run shared across all smoke-tier invariant tests; keyed by options tuple). Rules:

- Never launch a fresh multi-step run for an assertion an existing cached run supports.
- A test that needs a different configuration adds a new cached key, with the smallest `-nstepsmacro` and `-n` that exercise the contract.
- Cached-run tests are smoke tier (they depend on the built binary) even when each individual assertion is cheap.
- Restart tests (`-IC_INTERIOR 2`) chain off a cached fresh run's output directory; copy it to `tmp_path` first so the cached artifact is never mutated.

---

## 6. Optional-dependency imports

Any test that imports an optional dependency MUST call `pytest.importorskip` at module top:

```python
import pytest

pytest.importorskip('matplotlib')
```

Optional deps recognized by the linter (`OPTIONAL_DEPS` in `tools/check_test_quality.py`): `matplotlib` (plotting helper tests), `aragog` (cross-implementation checks, nightly), `bibtexparser` (citation checker). The binary and the C test executables are NOT Python imports; their absence is handled by the conftest fixtures via `pytest.skip` with an actionable message.

---

## 7. Marker discipline and timeouts

Every test file MUST begin with:

```python
import pytest

pytestmark = [pytest.mark.<tier>, pytest.mark.timeout(<budget>)]
```

with budgets:

- `unit` -> `timeout(30)` (target wall-time per test < 1 s; PetscInitialize startup dominates).
- `smoke` -> `timeout(120)` (target < 30 s on a development machine; the ceiling absorbs the slower CI runners, which also pay the session-cached run on its first consumer).
- `integration` -> `timeout(300)`.
- `slow` -> `timeout(3600)`.

PR CI runs `pytest -m "(unit or smoke) and not skip and not slow and not integration"`. Tests without the tier marker are invisible to CI and shipped untested. The lint script blocks any file missing the module-level `pytestmark`. Per-function markers are additive, not a replacement.

The timeout ceiling exists so a hung CVODE solve or a deadlocked subprocess surfaces as a specific-test failure rather than a generic job timeout.

---

## 8. Float and numerical comparison

- NEVER use `==` for floats. Use `pytest.approx(val, rel=1e-5)` or `np.testing.assert_allclose(...)`.
- State the tolerance rationale in a comment when non-obvious. E.g. "rtol=2e-3 because the external-mesh pathway uses midpoint-rule quadrature for shell masses while AW uses analytical integrals".
- Regression comparisons against `tests/expected_output/` use rtol=atol=1e-5 (native mesh) and 2e-3 (external mesh).
- Always reconstruct SI values from JSON as `values * scaling` before comparing; never pin nondimensional internals unless the test is explicitly about the scaling.

---

## 9. Voice rule for test artifacts

The repo-wide voice rule (zero AI-process disclosure in any public artifact) applies to test code with the same strictness as to source. In scope: test-skip reasons, test-file / function docstrings, test names, parametrize ids, log-capture assertions, commit messages on test-touching commits, PR titles and bodies, GitHub Actions job / step names, inline C comments, shipped log strings, and all public docs (which apply the rule silently, never document it). Out of scope: this file, `spider-code-review.md`, `copilot-instructions.md`.

Banned phrases inside in-scope artifacts: "audit", "review pass", "adversarial review", AI-roadmap labels, `claude-config/...` paths, "Generated with Claude", AI-tool names, em-dashes, en-dashes (except bibliographic page ranges), process meta-commentary.

Write the OUTCOME, never the PROCESS. First-person voice. Going-forward only.

---

## 10. Fixture and parameter conventions

- Options files under `tests/opts/` are the canonical run configurations; per-test overrides are appended `-flag value` pairs kept minimal and explicit.
- SI units everywhere in assertions; name the unit in a comment on every pinned value.
- Use `@pytest.mark.parametrize` when the same contract spans multiple regimes (fully molten, fully solid, mixed phase; native vs external mesh). Each parametrize id reads like a physical scenario.
- Run output goes to `tmp_path`; the cached fixtures manage their own session-scoped tmp directories.

---

## 11. Documentation per test

- **File-level docstring**: name the C source under test (`Tests for <file>.c`), list the invariants and contract clauses exercised, link to `docs/How-to/build_tests.md`.
- **Function-level docstring**: the physical scenario or contract clause in plain language. Required (lint-enforced).
- **Inline comments**: why a specific input, node count, or tolerance was chosen.

---

## 12. Naming

- Test names describe behavior: `test_pressure_increases_monotonically_with_depth`, NOT `test_mesh`.
- Test file names mirror source 1:1: `<file>.c` -> `tests/test_<file>.py`. Documented exceptions:
  - **`tests/test_regression.py`**: full end-to-end regression cases against frozen expected output (they exercise every source at once; assigning them to one mirror file would be arbitrary).
  - **`tests/test_aragog_crosscheck.py`**: cross-implementation validation, slow tier.
  - **`tests/test_plot_spider_lite.py`**: mirrors `py/plot_spider_lite.py` (Python source).
- Group related tests in classes when they share setup.

---

## 13. Adversarial review trigger

A pull request that adds or substantially modifies **> 50 lines of test code across all its commits** triggers an independent review pass before merge. The denominator is PR-level (`git diff origin/main...HEAD -- 'tests/**'`). The reviewer cites the anti-happy-path rule (Section 1), the discrimination-guard requirement (Section 2), and the physics-invariant tier (Section 3); flags single-assert tests, exit-code-only tests, weak assertions, missing module-level markers, missing certification markers, and dead tests. Findings are addressed in a follow-up commit whose subject describes the OUTCOME.

---

## 14. Tooling

- `bash tools/validate_test_structure.sh` -- structural check (marker presence, mirror mapping).
- `python tools/check_test_quality.py --check` -- CI mode: AST scan for forbidden patterns and marker requirements. Fails the PR if violations exceed the baseline (`tools/test_quality_baseline.json`).
- `python tools/check_test_quality.py --baseline` -- regenerate the baseline after a deliberate sweep only.
- `python tools/check_test_quality.py --reference-pinned-status` -- punch list of physics sources missing a `reference_pinned` test.
- `python tools/update_coverage_threshold.py --target fast|full` -- one-way coverage ratchet, capped at the 90% ecosystem ceiling.
- `ruff check tests/ tools/ py/` and `ruff format tests/ tools/ py/` -- Python lint before commit.

---

## 15. Coverage strategy (operator's view)

C line coverage is measured with gcov/gcovr on `--coverage` builds; `cJSON.c` is excluded as vendored code.

| Gate | Tests | Target | When |
|---|---|---|---|
| Fast gate (`tool.spider.coverage_fast`) | unit + smoke | moves only upward toward **90%** | Every PR |
| Full gate (`tool.spider.coverage_full`) | unit + smoke + integration + slow | moves only upward toward **90%** | Nightly |

The ratchet is one-way and run manually (`tools/update_coverage_threshold.py`), capped at 90%. Never decrease a threshold. The CI guard rejects any PR that lowers either `fail_under` below `min(base_ref, 90.0)`.

What this means for adding code:

- A new pure evaluator in a physics source: extend the C test executable + the unit-tier wrapper.
- A new option-dispatched code path: a smoke-tier run with the option set, asserting on JSON content, plus a line in the options reference.
- A new output field: extend the JSON invariant tests so the field is covered by at least one closure or boundedness check.

---

## 16. Failure modes to recognize on review

These are real patterns for this codebase. The lint script catches some mechanically; reviewers catch the rest.

| Pattern | Example | Why it slips | Fix |
|---|---|---|---|
| **Exit-code-only test** | `spider` runs, test asserts `returncode == 0` | The run "worked" but the physics regressed silently | Parse the JSON; assert closure / boundedness / pinned values |
| **Nondimensional leak** | A JSON `values` entry pinned without multiplying by `scaling` | Scaled values are O(1) and look plausible | Always reconstruct SI as `values * scaling`; scale guard in the pin |
| **Sign convention on gravity** | `-gravity -10.0` (negative by convention); a test computes a profile with +10 and matches within loose tolerance | Loose tolerance masks the sign | Tight tolerance + sign guard on the gradient direction |
| **Table-node-only interpolation test** | Interpolation queried exactly at table nodes | Identity at nodes for any scheme | Off-node queries where schemes differ |
| **Suspiciously-fast solver run** | CVODE hits max steps or a tolerance floor, output written anyway | Exit code still 0 | Assert step count and final time from the JSON, not just presence |
| **Cached-run mutation** | A restart test writes into the cached fresh-run directory | Later tests read mutated state | Copy cached output to `tmp_path` before restarting from it |
| **Frozen-reference drift** | `expected_blackbody50.txt` regenerated casually to make a failing test pass | The reference IS the contract | Regenerating the reference requires a PR that explains the physics change and updates `docs/Validation/` |
| **Optional dep imported unconditionally** | `import matplotlib` at module top | Minimal CI env fails collection | `pytest.importorskip('matplotlib')` |
| **Missing module-level marker** | File added with per-function markers only | CI marker filter misses the file's tier intent | Restore module-level `pytestmark` |

When you spot a new variant, add it here.

---

## 17. Sister rules (cross-link)

- `.github/copilot-instructions.md` "Testing Standards" -- the high-level summary.
- `.github/.claude/rules/spider-code-review.md` -- the review-pass gate and domain-aware source review (scaling boundaries, PETSc error handling, JSON contract, PROTEUS coupling).

Any change to the rule set: update both files in the same commit and call out the cross-reference in the commit body.
