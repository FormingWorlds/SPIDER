# Testing suite

[![Tests](https://img.shields.io/github/actions/workflow/status/FormingWorlds/SPIDER/ci.yml?branch=main&label=Tests)](https://github.com/FormingWorlds/SPIDER/actions/workflows/ci.yml)
[![tests](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/FormingWorlds/SPIDER/badges/tests-total.json)](https://proteus-framework.org/testing)

SPIDER's tests are integration cases run by the [SciATH](https://github.com/sciath/sciath) harness from `tests/tests.yml`.
Each case drives the compiled `spider` binary and compares its output against expected values within set tolerances.
The **Tests** badge reports whether the CI workflow, which builds SPIDER and runs the full suite on `main`, is passing; the **tests** badge shows how many cases the suite currently defines.
For how to run the suite locally, see [Testing SPIDER](../How-to/test.md).

## Badge system

The **Tests** badge is the status of the `CI` GitHub Actions workflow: it is green only when SPIDER builds against PETSc and every SciATH case passes on `main`.
The case count is produced by `tools/generate_test_badges.py` and published as a shields.io endpoint JSON file on the repository's `badges` branch, refreshed on `main` whenever the test suite changes.
The badge reads that file, so it shows the current case count.
The same number appears on the central [PROTEUS testing dashboard](https://proteus-framework.org/testing).
