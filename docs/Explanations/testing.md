# Testing suite

[![Tests](https://img.shields.io/github/actions/workflow/status/FormingWorlds/SPIDER/ci.yml?branch=main&label=Tests)](https://github.com/FormingWorlds/SPIDER/actions/workflows/ci.yml)
[![tests](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/FormingWorlds/SPIDER/badges/tests-total.json)](https://proteus-framework.org/testing)
[![unit tests](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/FormingWorlds/SPIDER/badges/tests-unit.json)](https://github.com/FormingWorlds/SPIDER/actions/workflows/ci.yml)
[![smoke tests](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/FormingWorlds/SPIDER/badges/tests-smoke.json)](https://github.com/FormingWorlds/SPIDER/actions/workflows/ci.yml)
[![integration tests](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/FormingWorlds/SPIDER/badges/tests-integration.json)](https://github.com/FormingWorlds/SPIDER/actions/workflows/nightly.yml)

SPIDER's tests run under pytest in four tiers. The unit tier drives small C test executables that evaluate pure functions (interpolation, equation-of-state lookups, phase blending) at probe points and checks the results in Python; the smoke tier runs the real `spider` binary for a few macro steps and asserts physical invariants on the JSON output (mass closure, positivity, monotonicity, boundary-condition identities); the integration tier compares full runs against frozen reference output; and the slow tier is reserved for long validation runs. Every physics source file has a companion test file, and each is pinned against a published benchmark, an analytical limit, or an independent cross-check, inventoried under [Validation](../Validation/index.md).

For how to run the suite locally, see [Testing SPIDER](../How-to/test.md); for how to write new tests, see [Building tests](../How-to/build_tests.md).

## Continuous integration

The `CI` workflow runs on every pull request: it builds SPIDER and the C test executables with coverage instrumentation against a cached PETSc, runs the unit and smoke tiers under a hard ten-minute cap, lints the Python files, validates the test structure and the test-quality baseline, and enforces the fast line-coverage gate. The `Nightly` workflow runs the complete suite including the frozen-reference regressions every night, enforces the full coverage gate, and uploads the coverage report to Codecov. Coverage thresholds move only upward (raised manually as measured coverage grows, with CI rejecting any decrease), capped at the PROTEUS-ecosystem ceiling of 90 percent.

## Badge system

The **Tests** badge is the status of the `CI` workflow on `main`. The count badges are produced by `tools/generate_test_badges.py` from pytest collection and published as shields.io endpoint JSON files on the repository's `badges` branch, refreshed whenever the suite changes on `main`: the total count, the fast tier that runs on every pull request, and the nightly tier. The same numbers appear on the central [PROTEUS testing dashboard](https://proteus-framework.org/testing).
