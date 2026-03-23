# Tutorial: first SPIDER run

This page walks you through a minimal SPIDER run, from compile to quick visualization.

!!! info "Prerequisites"
    - You have installed PETSc and SPIDER by going through the [installation guide](../How-to/installation.md). 
    - You have a working C compiler. 
    - Preferably: you are in a Conda environment with python version 3.12.

## 1. Run a known example

Use one of the provided options files:

```bash
./spider -options_file tests/opts/blackbody50.opts
```

This writes model output to the default output directory (typically `output/`).

!!! info "Runtime" 
    A first run on a laptop/workstation typically finishes in seconds to a few minutes, depending on CPU and PETSc settings.

To quickly verify output structure:

```bash
ls output
```
You should see text files with radial profiles and time-series data.

Expected signs of success:

- `output` exists and is non-empty.
- Multiple text files are produced (for example, interior profile and time-series outputs).
- No PETSc crash/solver error is printed to terminal.

## 2. Make a quick plot

```bash
python py/plot_spider_lite.py -h
python py/plot_spider_lite.py -d output
```

The plotting script generates a basic figure of interior profiles from your run output inside the directory `plots/`. 

## 3. Next steps

- Try a different options file in `tests/opts/`.
- Compare your run output against files in `tests/expected_output/`.

## Common first-run issues

- `PETSC_DIR` or `PETSC_ARCH` not set:
  Re-export them in your shell and rebuild.
- `./spider` not found:
  Build failed or you are not in the project root.
- Plot script fails:
  Install Python dependencies from `py/requirements.txt`.