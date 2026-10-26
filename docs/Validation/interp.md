# interp.c: 1-D and 2-D lookup interpolation

## What this page checks

This page checks interpolation routines in `interp.c`, which evaluate tabulated material properties.
`interp.c` provides one-dimensional and two-dimensional linear table interpolation.
Validation means that we test interpolator behavior against affine data with exact analytical solutions.
If table interpolation fails, material properties across the mantle are evaluated incorrectly.
The section below details the validation check, its tolerance, and its test command.

## Affine data reproduced exactly including last node

**Why this check exists.** Table interpolators can suffer from index off-by-one errors, boundary truncation bugs, or incorrect linear weighting. An interpolation bug distorts lookups across all equation of state tables.

**What it tests.** The test evaluates piecewise-linear interpolation on synthetic affine data y = 2x + 1 at on-node, off-node, and exact-endpoint queries. Nearest-neighbour values at bracketing nodes (5 and 7 around the pinned 6) sit far outside tolerance. Sign and range guards bound the pinned value. A companion test pins the chord value 6.5 on y = x**2, confirming that higher-order schemes would fail.

**How we know the right answer.** Piecewise-linear interpolation reproduces affine data exactly by mathematical definition. Numerical queries match analytical values to rel 1e-14 across nodes, interior intervals, and endpoints.

**Why it matters.** The interpolation layer feeds the tabulated equation-of-state lookups in SPIDER (`eos_lookup.c`).

**Known limit.** The case covers 1-D interpolation with unit scalings; the 2-D bilinear case (`test_bilinear_plane_exact_everywhere_including_grid_corner`) and per-column scaling are not part of it.

??? info "Test details"
    - Reference: Analytical limit: piecewise-linear interpolation reproduces affine data exactly.
    - Tolerance: rel 1e-14 on y = 2x + 1 at on-node, off-node, and exact-endpoint queries.
    - Test id: `tests/test_interp.py::test_affine_data_reproduced_exactly_including_last_node`
    - Command: `make tests_c`, then `pytest -o addopts= tests/test_interp.py::test_affine_data_reproduced_exactly_including_last_node`
    - Companion test: `tests/test_interp.py::test_out_of_range_queries_clamp_to_table_edges` asserts out-of-range clamping at table edges.

## Related code

- `interp.c`: `Interp1dCreateAndSet`, `Interp2dCreateAndSet`, `SetInterp1dValue`, `SetInterp2dValue`.
- `tests/test_interp.py`: `test_affine_data_reproduced_exactly_including_last_node`, `test_out_of_range_queries_clamp_to_table_edges`, `test_curved_data_follows_the_piecewise_linear_contract`.
