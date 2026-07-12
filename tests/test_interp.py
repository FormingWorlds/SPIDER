"""Tests for interp.c (1-D and 2-D lookup interpolation).

Driven through the tests/c/test_interp executable on synthetic tables
whose exact values are known in closed form. Invariants exercised:
piecewise-linear reproduction of affine data (analytical limit),
boundedness under out-of-range clamping, and the piecewise-linear (not
higher-order) contract on curved data. See docs/How-to/build_tests.md
for the tier system.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]


@pytest.fixture(scope='session')
def linear_table_1d(tmp_path_factory):
    """Synthetic 1-D table of y = 2x + 1 on x = 0..10, 11 nodes, unit scalings."""
    path = tmp_path_factory.mktemp('interp_tables') / 'linear_1d.dat'
    lines = ['# 3 11', '# x, y', '# 1.0 1.0']
    lines += [f'{float(i):.16e} {2.0 * i + 1.0:.16e}' for i in range(11)]
    path.write_text('\n'.join(lines) + '\n')
    return path


@pytest.fixture(scope='session')
def quadratic_table_1d(tmp_path_factory):
    """Synthetic 1-D table of y = x**2 on x = 0..10, 11 nodes, unit scalings."""
    path = tmp_path_factory.mktemp('interp_tables') / 'quadratic_1d.dat'
    lines = ['# 3 11', '# x, y', '# 1.0 1.0']
    lines += [f'{float(i):.16e} {float(i * i):.16e}' for i in range(11)]
    path.write_text('\n'.join(lines) + '\n')
    return path


@pytest.fixture(scope='session')
def plane_table_2d(tmp_path_factory):
    """Synthetic 2-D table of z = 3x + 5y on a 5 x 4 regular grid, unit scalings."""
    path = tmp_path_factory.mktemp('interp_tables') / 'plane_2d.dat'
    lines = ['# 3 5 4', '# x, y, z', '# 1.0 1.0 1.0']
    # Row-major with x fastest, matching the SPIDER reader.
    lines += [
        f'{float(i):.16e} {float(j):.16e} {3.0 * i + 5.0 * j:.16e}'
        for j in range(4)
        for i in range(5)
    ]
    path.write_text('\n'.join(lines) + '\n')
    return path


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_affine_data_reproduced_exactly_including_last_node(c_test, linear_table_1d):
    """Piecewise-linear interpolation reproduces y = 2x + 1 exactly.

    Analytical limit: linear interpolation is exact on affine data at
    every query point, on-node and off-node. x = 10.0 probes the last
    table node exactly, the edge where an index search may step out of
    the array.
    """
    out = c_test(
        'test_interp',
        ('-file_1d', str(linear_table_1d), '-x_1d', '0.0,2.5,7.0,10.0'),
    )
    assert out['y_1d'] == pytest.approx([1.0, 6.0, 15.0, 21.0], rel=1e-14)
    # The derivative of the affine data is the constant slope 2.
    assert out['dydx_1d'] == pytest.approx([2.0] * 4, rel=1e-14)
    # Nearest-neighbour discrimination: at x = 2.5 the neighbouring node
    # values are 5 and 7; both sit far outside the tolerance around 6.
    assert abs(out['y_1d'][1] - 5.0) > 0.5
    assert abs(out['y_1d'][1] - 7.0) > 0.5
    # Sign and scale guards on the pinned interior value.
    assert out['y_1d'][1] > 0
    assert 1.0 < out['y_1d'][1] < 21.0


@pytest.mark.physics_invariant
def test_out_of_range_queries_clamp_to_table_edges(c_test, linear_table_1d):
    """Out-of-range queries truncate to the table edge instead of extrapolating.

    Boundedness contract: the EOS tables must never be extrapolated, so
    y(15) returns y(xmax) = 21 (not the extrapolated 31) and y(-5)
    returns y(xmin) = 1 (not -9).
    """
    out = c_test(
        'test_interp',
        ('-file_1d', str(linear_table_1d), '-x_1d', '-5.0,15.0'),
    )
    assert out['xmin_1d'] == pytest.approx(0.0, abs=1e-15)
    assert out['xmax_1d'] == pytest.approx(10.0, rel=1e-14)
    assert out['y_1d'] == pytest.approx([1.0, 21.0], rel=1e-14)
    # Extrapolation discrimination: the linear continuations (-9 and 31)
    # differ from the clamped values by far more than the tolerance.
    assert abs(out['y_1d'][0] - (-9.0)) > 5.0
    assert abs(out['y_1d'][1] - 31.0) > 5.0


def test_curved_data_follows_the_piecewise_linear_contract(c_test, quadratic_table_1d):
    """Interpolating y = x**2 off-node returns the chord value, not the curve.

    Between the nodes at x = 2 and x = 3 the chord gives (4 + 9)/2 = 6.5
    at x = 2.5; the true curve gives 6.25. Pinning 6.5 discriminates the
    piecewise-linear contract from a higher-order or exact evaluation.
    """
    out = c_test('test_interp', ('-file_1d', str(quadratic_table_1d), '-x_1d', '2.5,2.0'))
    assert out['y_1d'][0] == pytest.approx(6.5, rel=1e-14)
    # The curve value would be 6.25: resolvable far above tolerance.
    assert abs(out['y_1d'][0] - 6.25) > 0.1
    # On-node query is exact for any interpolation scheme.
    assert out['y_1d'][1] == pytest.approx(4.0, rel=1e-14)


@pytest.mark.physics_invariant
def test_bilinear_plane_exact_everywhere_including_grid_corner(c_test, plane_table_2d):
    """Bilinear interpolation reproduces z = 3x + 5y exactly on and off grid.

    The plane is in the bilinear function space, so any deviation flags
    an indexing or weighting defect. The (4, 3) probe hits the extreme
    grid corner (both coordinates at their last node), and the (5, 4)
    probe checks clamping to that corner rather than extrapolation
    (which would give 35).
    """
    out = c_test(
        'test_interp',
        (
            '-file_2d',
            str(plane_table_2d),
            '-x_2d',
            '0.5,2.0,4.0,5.0',
            '-y_2d',
            '1.5,0.0,3.0,4.0',
        ),
    )
    assert out['z_2d'][:3] == pytest.approx([9.0, 6.0, 27.0], rel=1e-14)
    # Clamped corner: z(xmax, ymax) = 27, not the extrapolated 3*5 + 5*4 = 35.
    assert out['z_2d'][3] == pytest.approx(27.0, rel=1e-14)
    assert abs(out['z_2d'][3] - 35.0) > 5.0
