# interp.c: 1-D and 2-D lookup interpolation

**Source under test**: `interp.c`

**Reference-pinned test**: `tests/test_interp.py::test_affine_data_reproduced_exactly_including_last_node`

**Anchor**: Analytical limit: piecewise-linear interpolation reproduces affine data exactly.

**Tolerance**: rel 1e-14 on y = 2x + 1 at on-node, off-node, and exact-endpoint queries.

**Discrimination guards**: Nearest-neighbour values at the bracketing nodes (5 and 7 around the pinned 6) sit far outside the tolerance; sign and range guards bound the pinned value; a companion test pins the chord value 6.5 on y = x**2 so a higher-order scheme would fail.

The interpolation layer feeds every EOS table evaluation, so its contract (linear between nodes, clamped outside the table range, exact at the nodes including the last one) is pinned on synthetic tables whose values are known in closed form. Out-of-range clamping rather than extrapolation is asserted on both sides of the table.
