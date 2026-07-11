"""Tests for eos_lookup.c (tabulated P-S equation of state).

Driven through the tests/c/test_eos executable on the shipped
1TPa-dK09-elec-free tables (de Koker and Stixrude 2009 melt and solid
properties with the Andrault et al. 2011 liquidus and Hirschmann 2013
solidus, as assembled for Bower et al. 2018). Invariants exercised:
agreement with an independent bilinear evaluation of the same tables,
positivity and pressure-monotonicity of the thermodynamic quantities,
invariance of SI outputs under the choice of nondimensionalisation, and
the hard-failure contract for a missing table file. See
docs/How-to/build_tests.md for the tier system.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests._table_utils import bilinear, read_2d_table

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]

REPO_ROOT = Path(__file__).resolve().parent.parent
OPTS = ('-options_file', str(REPO_ROOT / 'tests' / 'opts' / 'blackbody50.opts'))
TABLE_DIR = REPO_ROOT / 'lookup_data' / '1TPa-dK09-elec-free'

# Interior probe points chosen off-node in both coordinates so that any
# indexing or weighting defect changes the interpolated value: mid-mantle
# pressures for an Earth-sized planet, entropies inside the melt table
# range around the blackbody50 initial condition.
PROBE_P = (7.3e9, 2.6e10, 8.9e10)  # Pa
PROBE_S = (2653.0, 2711.0, 2790.0)  # J/kg/K


def _melt_eval(c_test, p_list, s_list, extra=()):
    """Evaluate the melt lookup EOS at SI probe points."""
    return c_test(
        'test_eos',
        (
            *OPTS,
            '-P_si',
            ','.join(str(p) for p in p_list),
            '-S_si',
            ','.join(str(s) for s in s_list),
            *extra,
        ),
    )


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_melt_density_matches_independent_bilinear_evaluation(c_test):
    """The C lookup reproduces an independent bilinear read of the same table.

    Cross-implementation cross-check: tests/_table_utils.py evaluates
    density_melt.dat with numpy primitives, sharing no code with
    interp.c. Agreement at off-node points pins the whole chain (file
    parsing, scaling, index search, weighting).
    """
    out = _melt_eval(c_test, PROBE_P, PROBE_S)
    xa, ya, za = read_2d_table(TABLE_DIR / 'density_melt.dat')
    expected = [bilinear(xa, ya, za, p, s) for p, s in zip(PROBE_P, PROBE_S)]
    assert out['rho'] == pytest.approx(expected, rel=1e-9)

    # Wrong-table discrimination: the solid table at the same probe
    # points gives densities well outside the tolerance.
    solid = _melt_eval(c_test, PROBE_P, PROBE_S, extra=('-eos_prefix', 'solid'))
    for rho_melt, rho_solid in zip(out['rho'], solid['rho']):
        assert abs(rho_melt - rho_solid) > 0.01 * rho_melt
    # Sign and scale guards: silicate densities at 7-90 GPa sit in the
    # thousands of kg/m3; a nondimensional leak would sit near unity.
    assert all(rho > 0 for rho in out['rho'])
    assert all(2.0e3 < rho < 8.0e3 for rho in out['rho'])


@pytest.mark.physics_invariant
def test_thermodynamic_quantities_positive_and_rho_monotonic_in_pressure(c_test):
    """T, rho, Cp, and alpha stay positive; density grows with pressure.

    The P = 0 probe is the table edge (surface of the planet), the
    extreme end of the physically valid range.
    """
    p_grid = (0.0, 5.0e9, 2.0e10, 8.0e10, 3.0e11)
    s_fixed = (2700.0,) * len(p_grid)
    out = _melt_eval(c_test, p_grid, s_fixed)
    for key in ('T', 'rho', 'cp', 'alpha'):
        assert all(v > 0 for v in out[key]), f'{key} must stay positive'
    # Compression along an isentrope: density strictly increases with P.
    rho = out['rho']
    assert all(a < b for a, b in zip(rho, rho[1:]))
    # Thermal expansivity decreases under compression for this EOS.
    alpha = out['alpha']
    assert all(a > b for a, b in zip(alpha, alpha[1:]))


@pytest.mark.physics_invariant
def test_si_outputs_invariant_under_nondimensionalisation_choice(c_test):
    """The same SI probe points give the same SI answers for any scalings.

    Symmetry contract of the nondimensionalisation: the blackbody50
    scalings (entropy0 = 2600, radius0 = 1e8, time0 = 3.154e6) and the
    parameter defaults (1e3, 1e6, 3.154e7) must agree to rounding, so a
    missed or doubled scaling anywhere in the chain fails loudly.
    """
    scaled = _melt_eval(c_test, PROBE_P, PROBE_S)
    defaults = c_test(
        'test_eos',
        (
            *OPTS,
            '-entropy0',
            '1.0E3',
            '-radius0',
            '1.0E6',
            '-time0',
            '3.154E7',
            '-P_si',
            ','.join(str(p) for p in PROBE_P),
            '-S_si',
            ','.join(str(s) for s in PROBE_S),
        ),
    )
    for key in ('T', 'rho', 'cp', 'alpha', 'dTdPs', 'phase_boundary_S'):
        assert scaled[key] == pytest.approx(defaults[key], rel=1e-9), key
    # The comparison is only meaningful if the two runs used different
    # scalings; the blackbody50 entropy scale differs from the default.
    assert 2600.0 != pytest.approx(1.0e3, rel=0.5)


def test_missing_table_file_is_a_hard_setup_error(c_test):
    """EOS setup fails hard when a table file cannot be opened.

    Error contract: a silent fallback to another table would poison
    every downstream quantity, so the executable must exit nonzero
    before producing any output.
    """
    with pytest.raises(RuntimeError, match='exited with code'):
        c_test(
            'test_eos',
            (
                '-melt_alpha_filename',
                '/nonexistent/alpha.dat',
                '-P_si',
                '1.0e9',
                '-S_si',
                '2600.0',
            ),
        )
