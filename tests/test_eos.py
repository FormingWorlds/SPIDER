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


def _spaargaren_prefactor(mg_si):
    """log10 viscosity prefactor of Spaargaren et al. (2020), as in eos.c."""
    if mg_si <= 1.0:
        return 0.5185 * (1 - mg_si) / 0.3
    if mg_si <= 1.25:
        return -1.4815 * (mg_si - 1) / 0.25
    if mg_si <= 1.5:
        return -2 + 0.5185 * (1.5 - mg_si) / 0.25
    return -2.0


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_compositional_viscosity_matches_spaargaren(c_test):
    """The Mg/Si viscosity prefactor reproduces Spaargaren et al. (2020).

    Anchor: the piecewise log10 prefactor of Spaargaren et al. (2020).
    Two evaluations cover all four Mg/Si branches: 1.4 against a 1.6
    reference (upper-intermediate and Fp-rich branches) and 1.2 against
    a 0.9 reference (lower-intermediate and Mg-rich branches). The
    shift adds to the configured melt log10visc of 2.0.
    """
    probe = ((1.0e10,), (2600.0,))
    high = _eval_with(
        c_test, ('-melt_visc_comp', '1.4', '-melt_visc_ref_comp', '1.6'), *probe
    )
    low = _eval_with(
        c_test, ('-melt_visc_comp', '1.2', '-melt_visc_ref_comp', '0.9'), *probe
    )

    shift_high = _spaargaren_prefactor(1.4) - _spaargaren_prefactor(1.6)
    shift_low = _spaargaren_prefactor(1.2) - _spaargaren_prefactor(0.9)
    # Transcription pins: the helper re-encodes the published piecewise
    # coefficients independently of eos.c; these literals (hand-derived
    # from Spaargaren et al. 2020) guard the helper itself, so a shared
    # transcription error cannot silently cancel.
    assert shift_high == pytest.approx(0.2074, abs=1e-4)
    assert shift_low == pytest.approx(-1.35803, abs=1e-4)
    # abs=1e-9: the prefactor is a closed-form expression of the two
    # option values, so only roundoff enters.
    assert high['log10visc'][0] == pytest.approx(2.0 + shift_high, abs=1e-9)
    assert low['log10visc'][0] == pytest.approx(2.0 + shift_low, abs=1e-9)

    # Branch discrimination: the two configurations shift in opposite
    # directions and differ by more than 1.5 decades, so a collapsed
    # piecewise (any single branch applied throughout) fails.
    assert shift_high > 0 > shift_low
    assert abs(high['log10visc'][0] - low['log10visc'][0]) > 1.5

    # Edge case: with the compositional term disabled (no visc_comp
    # option) the melt viscosity is the bare configured constant.
    base = _eval(c_test, 'melt', *probe)
    assert base['log10visc'][0] == pytest.approx(2.0, abs=1e-10)


def _eval_with(c_test, extra, p_list, s_list):
    """Evaluate the melt EOS with additional viscosity options."""
    return c_test(
        'test_eos',
        (
            *OPTS,
            *extra,
            '-eos_prefix', 'melt',
            '-P_si', ','.join(str(p) for p in p_list),
            '-S_si', ','.join(str(s) for s in s_list),
        ),
    )


@pytest.mark.physics_invariant
def test_activation_terms_shape_the_viscosity_profile(c_test):
    """Activation volume and energy bend the viscosity with P and T.

    The unpinned activation-volume term adds V * P * exp(-P/Ps) / T to
    the log viscosity: it vanishes identically at the P = 0 surface
    limit (edge case), stiffens the deep mantle, and is damped by the
    pressure scale Ps. The pinned activation-energy term with a
    reference temperature below the actual temperature softens the
    melt, discriminating the sign convention of dT.
    """
    probes_p = (0.0, 6.55e10)  # Pa; surface limit and deep mantle
    probes_s = (2600.0, 2600.0)  # J/kg/K

    vol = _eval_with(
        c_test, ('-melt_activation_volume', '1.0e-6'), probes_p, probes_s
    )
    # Edge limit: no pressure, no activation-volume contribution; the
    # bare constant 2.0 returns exactly.
    assert vol['log10visc'][0] == pytest.approx(2.0, abs=1e-10)
    # Deep mantle stiffens: positive V and P give a positive shift.
    assert vol['log10visc'][1] > 2.0 + 1e-6

    # The pressure scale damps the deep contribution: with Ps = 10 GPa
    # the 65.5 GPa probe carries exp(-6.55) = 1.4e-3 of the undamped
    # term, so the shift shrinks by orders of magnitude but stays
    # positive.
    damped = _eval_with(
        c_test,
        (
            '-melt_activation_volume', '1.0e-6',
            '-melt_activation_volume_pressure_scale', '1.0e10',
        ),
        probes_p,
        probes_s,
    )
    undamped_shift = vol['log10visc'][1] - 2.0
    damped_shift = damped['log10visc'][1] - 2.0
    assert 0 < damped_shift < 0.1 * undamped_shift

    # Pinned activation energy with a reference temperature below the
    # melt temperature: dT < 0, so the melt is softer than the bare
    # constant, and the shift grows with temperature contrast (the
    # hotter 3000 J/kg/K probe sits further from the reference).
    energy = _eval_with(
        c_test,
        ('-melt_activation_energy', '1.0e5', '-melt_visc_ref_temp', '1500.0'),
        (1.0e10, 1.0e10),
        (2500.0, 3000.0),
    )
    assert energy['log10visc'][0] < 2.0
    assert energy['log10visc'][1] < 2.0
    # Temperature dependence: the two probes shift by different
    # amounts, so a T-independent (constant) offset fails.
    assert abs(energy['log10visc'][0] - energy['log10visc'][1]) > 1e-4
