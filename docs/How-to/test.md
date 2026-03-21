# Testing SPIDER

This guide explains how to validate your SPIDER installation using the test suite.

!!! info "Prerequisites"
    - SPIDER is compiled and the `spider` executable exists in the project root.
    - PETSc is installed.
    - Python 3.12 is available (preferably in a Conda environment).

## 1. Install SciATH

Get SciATH (Scientific Application Test Harness), which is a Python module:

```bash
cd /somewhere/to/install
git clone https://github.com/sciath/sciath -b dev
```

Add the module to your Python path:

```bash
export PYTHONPATH=$PYTHONPATH:/path/to/sciath
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
    .tools/get_spider.sh
    ```

## 3. Test

From the SPIDER root directory, test SPIDER's basic functionality:

```bash
make test
```

This command:

1. Creates a `test_dir/` output directory.
2. Runs the test harness on the suite defined in `tests/tests.yml`.
3. Reports the location of the test output and a test report by SciATH.

All test outputs are collected in `test_dir/`. After tests complete, you can find:

```
test_dir/
  - pth.conf                         # Configuration file for test harness
  - blackbody50_output/              # Output from standard test
  - external_mesh_roundtrip_output/  # External mesh validation
  - non_aw_mesh_output/              # Non-AW mesh validation
  - plot_test_output/                # Plotting test output
  - sciath_test_report.txt           # SciATH test report
```

## What the test suite validates

The test suite (defined in `tests/tests.yml`) runs several checks:

| Test | Purpose |
|------|---------|
| `blackbody50` | Core interior dynamics on a Earth-like blackbody planet. Final state is compared against known outputs. Check `tests/opts/blackbody50.opt` for exact configuration.|
| `plot_test` | Validates the Python plotting script (`py/plot_spider_lite.py`) runs without error. |
| `external_mesh_roundtrip` | Verifies SPIDER accepts external mesh files and produces correct results. |
| `non_aw_mesh` | Confirms SPIDER works with non-Adams-Williamson density profiles. |

Each test runs one or more commands and compares output against expected values with specified tolerances.

## Common test issues

### SciATH not found

```
Error: sciath module not found
```

**Solution:**  
Ensure SciATH is cloned and added to `PYTHONPATH`:

```bash
export PYTHONPATH=$PYTHONPATH:/path/to/sciath
make test
```

### Tolerance mismatches

If a test fails with a tolerance error (e.g., relative tolerance exceeded), it usually indicates:

- A code change that alters output slightly (check your recent commits).
- Different compiler flags or PETSc version (some tests have tight tolerances). Note that by default, PETSc version 3.19.0 is installed, and newer versions might lead to tolerance errors. 
- Differences in floating-point rounding between systems.

Most tests have `rtol: 1e-5` (relative tolerance) and `atol: 1e-5` (absolute tolerance). See `tests/tests.yml` for specific thresholds.

### Plot test fails

The `plot_test` checks that the Python plotting script runs without error. If it fails, plot the test output manually and see what is going wrong:

```bash
python py/plot_spider_lite.py -d test_dir/blackbody50_output/sandbox/output
```

This generates a file called `interior.pdf` into a `plots/` directory. 

If need, install missing dependencies:

```bash
pip install -r py/requirements.txt
```

## Comparing against expected output

After a test run completes, you can manually compare your output against known good results. A quick way to check everything worked well, is by comparing plots. If you have VS Code's `code` installed:

```bash
code test_dir/plot_test_output/sandbox/interior.pdf
code tests/expected_output/blackbody50-interior.png
```

or open the files manually.

Expected files are in `tests/expected_output/`. Small differences due to compiler or system differences are usually acceptable if they are within the specified tolerances.