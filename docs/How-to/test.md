# Testing SPIDER

This guide explains how to validate your SPIDER installation using the test suite. For guidance on writing new tests, see [Building tests](build_tests.md).

!!! info "Prerequisites"
    - SPIDER is compiled and the `spider` executable exists in the project root.
    - PETSc is installed.
    - Python 3.12 is available (preferably in a Conda environment).

## 1. Install the Python test dependencies

The test suite uses pytest:

```bash
pip install -r py/requirements.txt
pip install pytest pytest-timeout
```

## 2. Set `PETSC_DIR` and `PETSC_ARCH`

`PETSC_DIR` and `PETSC_ARCH` are not automatically set after installing SPIDER. Set them manually:

```bash
export PETSC_DIR=/somewhere/to/install/petsc
export PETSC_ARCH=arch-xxx-yyy
```

!!! info "What to set for `PETSC_DIR` and `PETSC_ARCH?`"
    The SPIDER installer automatically reports the `PETSC_ARCH` and `PETSC_DIR` that PETSc was built against. To see what you need to set for these variables, run the installer again:
    ```bash
    ./tools/get_spider.sh
    ```

## 3. Build the binary and the C test executables

```bash
make -j
make -j tests_c
```

The C test executables under `tests/c/` back the unit tier; tests that need them are skipped with an explanatory message when they have not been built.

## 4. Test

From the SPIDER root directory, run the fast tiers:

```bash
make test               # equivalent to: pytest -m "(unit or smoke) and not skip"
```

or the complete suite including the long-running tiers:

```bash
make test_all           # equivalent to: pytest -m "not skip"
```

Run output goes to pytest-managed temporary directories; nothing is written into the repository tree.

## Test tiers

The suite is organised in four tiers, selected with pytest markers:

| Tier | What it runs | Wall time | Command |
|------|--------------|-----------|---------|
| `unit` | C test executables and Python-side checks | seconds | `pytest -m unit` |
| `smoke` | Short real `spider` runs with physics checks on the JSON output | tens of seconds | `pytest -m smoke` |
| `integration` | Full regression cases against frozen expected output | minutes | `pytest -m integration` |
| `slow` | Long validation runs and cross-implementation checks | up to hours | `pytest -m slow` |

Pull-request CI runs the `unit` and `smoke` tiers; the nightly workflow runs `integration` and `slow`.

## What the regression tests validate

| Test | Purpose |
|------|---------|
| `test_regression.py::test_blackbody50_final_state_matches_frozen_reference` | Core interior dynamics on an Earth-like blackbody planet. The final state is compared against `tests/expected_output/expected_blackbody50.txt`. Check `tests/opts/blackbody50.opts` for the exact configuration. |
| `test_regression.py::test_external_mesh_run_reproduces_native_aw_reference` | Verifies SPIDER accepts external mesh files and reproduces the native-mesh results. |
| `test_regression.py::test_restart_from_snapshot_continues_the_run` | Verifies the restart pathway reads back SPIDER's own output and continues the run. |
| `test_plot_spider_lite.py` | Validates the Python plotting script (`py/plot_spider_lite.py`) end-to-end. |

For external mesh setup details and file format requirements, see [External Mesh Input](external_mesh_input.md).

## Common test issues

### spider binary not found

Tests that need the binary are skipped with the message `spider binary not found`. Build it first (`make -j`), or point the suite at an existing binary:

```bash
export SPIDER_EXEC=/path/to/spider
```

### Tolerance mismatches

If a regression test fails with a tolerance error, it usually indicates:

- A code change that alters output slightly (check your recent commits).
- Different compiler flags or PETSc version (some tests have tight tolerances). Note that by default, PETSc version 3.19.0 is installed, and newer versions might lead to tolerance errors.
- Differences in floating-point rounding between systems.

The native-mesh regression uses `rtol = atol = 1e-5`; the external-mesh pathway uses `2e-3` because its midpoint-rule shell masses differ from the analytical integrals at finite resolution.

### Plot test fails

The plotting tests check that `py/plot_spider_lite.py` runs end-to-end. If they fail, plot a run manually and see what is going wrong:

```bash
python py/plot_spider_lite.py -d /path/to/run/output
```

This generates a file called `interior.pdf` into a `plots/` directory.

If needed, install missing dependencies:

```bash
pip install -r py/requirements.txt
```

## Comparing against expected output

Frozen references live in `tests/expected_output/`. A quick way to check a run by eye is to compare plots:

```bash
python py/plot_spider_lite.py -d /path/to/run/output
code plots/interior.pdf
code tests/expected_output/blackbody50-interior.png
```

Small differences due to compiler or system differences are usually acceptable if they are within the specified tolerances. The frozen references are the regression contract: regenerate them only as part of a pull request that explains the underlying physics or solver change.
