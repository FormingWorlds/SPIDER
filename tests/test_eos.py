"""Tests for eos.c (EOS interface: setup, viscosity, phase boundaries).

Driven through the tests/c/test_eos executable on the blackbody50
configuration. eos.c owns the option parsing shared by every EOS
implementation (viscosity and conductivity constants, phase-boundary
loading) and the generic evaluation entry points. Invariants exercised:
per-phase viscosity and conductivity dispatch, and agreement of the
loaded phase boundary with an independent read of the same table. See
docs/How-to/build_tests.md for the tier system.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests._table_utils import read_1d_table

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]

REPO_ROOT = Path(__file__).resolve().parent.parent
OPTS = ('-options_file', str(REPO_ROOT / 'tests' / 'opts' / 'blackbody50.opts'))
LIQUIDUS = REPO_ROOT / 'lookup_data' / '1TPa-dK09-elec-free' / 'liquidus_A11_H13.dat'


def _eval(c_test, prefix, p_list, s_list):
    """Evaluate one lookup EOS at SI probe points."""
    return c_test(
        'test_eos',
        (
            *OPTS,
            '-eos_prefix', prefix,
            '-P_si', ','.join(str(p) for p in p_list),
            '-S_si', ','.join(str(s) for s in s_list),
        ),
    )


@pytest.mark.physics_invariant
def test_viscosity_and_conductivity_dispatch_per_phase(c_test):
    """Each phase receives its own configured viscosity and conductivity.

    blackbody50 configures melt_log10visc = 2.0, solid_log10visc = 21.0,
    and 4.0 W/m/K conductivity for both phases with zero activation
    terms, so the evaluated values are the configured constants. The 19
    decade viscosity contrast discriminates a swapped-prefix regression.
    """
    melt = _eval(c_test, 'melt', (1.0e10,), (2600.0,))
    solid = _eval(c_test, 'solid', (1.0e10,), (2300.0,))
    assert melt['log10visc'][0] == pytest.approx(2.0, abs=1e-10)
    assert solid['log10visc'][0] == pytest.approx(21.0, abs=1e-10)
    # Swapped-phase guard: the two values are 19 decades apart.
    assert abs(melt['log10visc'][0] - solid['log10visc'][0]) > 10.0
    # Conductivity is 4.0 W/m/K for both phases in this configuration.
    assert melt['cond'][0] == pytest.approx(4.0, rel=1e-10)
    assert solid['cond'][0] == pytest.approx(4.0, rel=1e-10)


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_phase_boundary_matches_independent_table_read(c_test):
    """The loaded melt phase boundary reproduces the A11_H13 liquidus table.

    Cross-implementation cross-check: tests/_table_utils.py reads
    liquidus_A11_H13.dat (Andrault et al. 2011 liquidus with the
    Hirschmann 2013 solidus companion, the melting curves shipped for
    Bower et al. 2018) and interpolates it with numpy.interp, sharing no
    code with eos.c or interp.c. The P = 0 probe pins the table edge
    (limit input): the boundary must return the first table entry.
    """
    probes = (0.0, 1.0e10, 6.55e10)  # Pa; edge, mid-mantle, off-node deep point
    out = _eval(c_test, 'melt', probes, (2600.0,) * len(probes))
    xa, ya = read_1d_table(LIQUIDUS)
    expected = [float(np.interp(p, xa, ya)) for p in probes]
    assert out['phase_boundary_S'] == pytest.approx(expected, rel=1e-12)
    # Edge limit: the P = 0 value is the first table entry itself.
    assert out['phase_boundary_S'][0] == pytest.approx(ya[0], rel=1e-12)
    # Wrong-table guard: the solidus at 10 GPa sits near 1524 J/kg/K,
    # far below the liquidus value near 2128 J/kg/K.
    assert abs(out['phase_boundary_S'][1] - 1524.43) > 100.0
    # Sign and scale guards: liquidus entropies of the dK09 set are
    # positive and of order a few thousand J/kg/K.
    assert out['phase_boundary_S'][1] > 0
    assert 1.5e3 < out['phase_boundary_S'][1] < 4.0e3
