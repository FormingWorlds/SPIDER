# Building tests

This guide explains how to write tests for SPIDER. For running the existing suite, see [Testing SPIDER](test.md); for what each physics source is validated against, see the [Validation](../Validation/index.md) pages.

SPIDER is scientific simulation code, so its tests are held to physics-grade standards: every test should be able to catch a real physical or numerical regression, not merely confirm that code runs. A test that passes for the wrong reason is worse than no test, because it manufactures confidence.

## The tier system

Every test file declares its tier and a defensive timeout at module level, directly after the imports:

```python
pytestmark = [pytest.mark.smoke, pytest.mark.timeout(60)]
```

| Tier | What belongs here | Timeout | Where it runs |
|------|-------------------|---------|---------------|
| `unit` | C test executables and Python-side checks; no full `spider` runs | 30 s | Every pull request |
| `smoke` | Short real runs (a few macro steps, 50 nodes) with physics checks on the JSON output | 60 s | Every pull request |
| `integration` | Full regression cases against the frozen references in `tests/expected_output/` | 300 s | Nightly |
| `slow` | Long validation runs, cross-implementation comparisons | 3600 s | Nightly |

The tier marker decides where the test runs; the timeout is a net against hangs, not a budget to fill. A unit test should finish in well under a second, a smoke test in well under 30. If a test needs more, move it up a tier.

## Structure: tests mirror sources

Each physics source file has a companion test file: `twophase.c` is tested by `tests/test_twophase.py`, `eos_lookup.c` by `tests/test_eos_lookup.py`, and so on. `bash tools/validate_test_structure.sh` enforces the mapping together with the marker discipline. Cross-cutting concerns (the frozen-reference regression, plotting) live in their own clearly named files.

## Three ways to reach the C code

1. **C test executables** (unit tier). Pure evaluator functions (interpolation, EOS evaluations, phase blending) are exercised through the small programs under `tests/c/`, built with `make tests_c`. Each executable evaluates functions at probe points given on its command line and prints one JSON object; the pytest wrapper makes every assertion. Keep the C side a thin evaluator: pins, tolerances, and guards belong in Python where they are visible and reviewable.
2. **Short real runs** (smoke tier). The `run_spider` and `cached_spider_run` fixtures in `tests/conftest.py` drive the binary with an options file plus minimal overrides and return the output directory. Session-scoped caching means one run serves many tests: prefer reading the shared `blackbody_short` or `blackbody_full` fixtures over launching a new run, and add a new cached configuration only when no existing one exercises your contract.
3. **Frozen-reference regression** (integration tier). Full configurations compared against `tests/expected_output/`. The references are the contract: regenerate them only in a pull request that explains the physics or solver change that moved them.

Read JSON output through `tests/_json_utils.py`, which reconstructs SI values as `values * scaling`. Never assert on a raw `values` entry: nondimensional internals are order unity and make wrong results look plausible.

## What every test must contain

1. **At least one edge case**: a boundary value (melt fraction 0 or 1, the surface node, the last table row), a degenerate input, or an extreme parameter.
2. **At least one error-contract or limit-input exercise**: if the code validates its input (missing table file, refused option combinations), assert the failure is loud; if it is closed-form mathematics, probe a limit where the answer is known exactly (the surface density at zero pressure, the interpolation identity at a table node).
3. **Assertions that discriminate**: values a plausibly wrong implementation would not produce. Point checks at symmetric or degenerate inputs (a temperature where every exponent gives the same answer, a composition where swapped coefficients cancel) verify nothing.

Two or more assertions per test, and every test carries a docstring naming the physical scenario or contract clause it verifies. `python tools/check_test_quality.py --check` enforces these rules mechanically and fails the pull request on regressions against `tools/test_quality_baseline.json`.

Forbidden patterns the checker flags: single-assert tests, standalone weak assertions (`is not None`, `> 0`, `len(...) > 0`, bare `isinstance`), missing docstrings, and `==` against float literals. Exit-code-only subprocess tests are the same trap in disguise: parse the JSON and assert on physics.

## Pinned values and discrimination guards

When a test pins a number, accompany the pin with guards showing that plausible wrong results fall outside the tolerance:

```python
def test_grey_body_flux_matches_stefan_boltzmann_limit(blackbody_short):
    """Pin the grey-body surface flux against sigma*(T^4 - Teqm^4)."""
    doc = read_output(blackbody_short, 200)
    t_surf = atmosphere_si(doc, 'temperature_surface')
    f_atm = atmosphere_si(doc, 'Fatm')
    sigma = 5.670367e-08  # W m-2 K-4, the value in constants.c
    expected = sigma * (t_surf**4 - 273.0**4)
    assert f_atm == pytest.approx(expected, rel=1e-6)
    # Exponent guard: a T^3 slip is off by orders of magnitude here.
    wrong = sigma * (t_surf**3 - 273.0**3)
    assert abs(f_atm - wrong) > 0.5 * f_atm
    # Sign guard: a hot interior radiates outward.
    assert f_atm > 0
    # Scale guard: magma-ocean fluxes, not nondimensional leaks.
    assert 1e2 < f_atm < 1e9
```

The guard classes to cover: exponent or factor errors, sign errors (`-gravity` is negative by SPIDER convention and a recurring trap), unit or scaling slips (guard the absolute magnitude and name the unit in a comment), and wrong-path selection (melt table versus solid table, one boundary condition versus another). When the primary assertion is itself a conservation closure, the equality already discriminates factor errors; keep the sign and scale guards.

State the tolerance rationale in a comment whenever it is not obvious, for example: `rtol=2e-3 because the external-mesh pathway uses midpoint-rule shell masses while the native path integrates analytically`.

## Physics invariants and validation markers

Every test on a physics source should assert at least one of:

- **Conservation**: mantle mass closure, per-volatile reservoir closure, elemental balance across reactions.
- **Positivity and boundedness**: temperatures, pressures, densities positive; melt fractions in [0, 1].
- **Monotonicity or symmetry**: pressure increasing with depth, liquidus above solidus, SI outputs invariant under the choice of nondimensionalisation.
- **A pinned value with discrimination guards**, as above.

Tag such tests `@pytest.mark.physics_invariant`. Tests that pin behaviour against a published benchmark, an analytical limit, or an independent cross-implementation get `@pytest.mark.reference_pinned` as well; each physics source keeps at least one, inventoried under [Validation](../Validation/index.md). `python tools/check_test_quality.py --reference-pinned-status` prints the sources still missing one.

## Determinism and hygiene

- SPIDER runs are deterministic (serial CVODE with fixed tolerances); do not introduce randomness into tests.
- Output goes to pytest-managed temporary directories, never into the repository tree. Never write into a cached fixture's output directory; restart tests copy the snapshot out first.
- Optional Python dependencies (`matplotlib`, and others as they appear) are guarded with `pytest.importorskip('<name>')` at module top so a minimal environment still collects the suite.
- Keep the Python style ruff-clean: `ruff check --fix tests/ tools/ py/`.

## Checklist for a new physics source

1. Add the source and header, and register the file in the `Makefile`.
2. Create `tests/test_<stem>.py` with the module-level `pytestmark`.
3. Add at least one `physics_invariant` test from the families above.
4. Choose a reference anchor (paper value, analytical limit, or independent cross-check), write the `reference_pinned` test, and add the `docs/Validation/<stem>.md` page recording the anchor, tolerance rationale, and guards.
5. If the source has pure evaluator functions, extend a C test executable under `tests/c/` (or add a new one to the `tests_c` target) and drive it from the unit tier.
6. Run the local gate: `pytest -m "(unit or smoke) and not skip"`, `bash tools/validate_test_structure.sh`, `python tools/check_test_quality.py --check`.
