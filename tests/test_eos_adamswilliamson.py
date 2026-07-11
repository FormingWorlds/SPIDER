"""Tests for eos_adamswilliamson.c (analytic Adams-Williamson density).

Driven through the tests/c/test_eos executable with
-eos_type adamswilliamson and the blackbody50 structural parameters.
Invariants exercised: the closed-form density profile
rho(P) = rhos - P * beta / g (with g negative by SPIDER convention),
its surface limit, compression monotonicity, and invariance of the SI
output under the choice of nondimensionalisation. See
docs/How-to/build_tests.md for the tier system.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]

REPO_ROOT = Path(__file__).resolve().parent.parent
OPTS = ('-options_file', str(REPO_ROOT / 'tests' / 'opts' / 'blackbody50.opts'))

# blackbody50 Adams-Williamson parameters (PREM lower-mantle fit).
RHOS = 4078.95095544  # kg/m^3 surface density
BETA = 1.1115348931000002e-07  # 1/m
GRAVITY = -10.0  # m/s^2, negative by convention


def _aw_eval(c_test, p_list, extra=()):
    """Evaluate the Adams-Williamson EOS at SI pressures."""
    n = len(p_list)
    return c_test(
        'test_eos',
        (
            *OPTS,
            '-eos_type', 'adamswilliamson',
            '-eos_prefix', 'adams_williamson',
            '-P_si', ','.join(str(p) for p in p_list),
            # Entropy is unused by the AW density but the executable
            # requires paired probe points.
            '-S_si', ','.join('2600.0' for _ in range(n)),
            *extra,
        ),
    )


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_density_matches_the_closed_form_profile(c_test):
    """The AW density reproduces rho(P) = rhos - P * beta / g exactly.

    Analytical limit: the Adams-Williamson equation of state is a closed
    form, so the evaluation must agree to rounding. P = 0 is the surface
    edge where rho reduces to the configured surface density, and
    1.35e11 Pa is the approximate core-mantle boundary pressure of the
    blackbody50 structure.
    """
    probes = (0.0, 1.0e10, 1.35e11)
    out = _aw_eval(c_test, probes)
    expected = [RHOS - p * BETA / GRAVITY for p in probes]
    assert out['rho'] == pytest.approx(expected, rel=1e-12)
    # Surface limit: exactly the configured surface density.
    assert out['rho'][0] == pytest.approx(RHOS, rel=1e-12)
    # Sign-of-beta guard: a sign-flipped compressibility would give
    # 3967.8 kg/m^3 at 10 GPa instead of 4190.1; both sit far outside
    # the tolerance.
    wrong_sign = RHOS + 1.0e10 * BETA / GRAVITY
    assert abs(out['rho'][1] - wrong_sign) > 100.0
    # Monotonicity under compression and physical scale (silicate
    # mantle densities, thousands of kg/m^3).
    assert out['rho'][0] < out['rho'][1] < out['rho'][2]
    assert all(3.0e3 < rho < 7.0e3 for rho in out['rho'])


@pytest.mark.physics_invariant
def test_si_density_invariant_under_nondimensionalisation_choice(c_test):
    """The same SI pressures give the same SI densities for any scalings.

    Symmetry contract of the nondimensionalisation, as for the lookup
    EOS: the blackbody50 scalings and the parameter defaults must agree
    to rounding so a missed or doubled scaling fails loudly.
    """
    probes = (0.0, 6.7e10)
    scaled = _aw_eval(c_test, probes)
    defaults = _aw_eval(
        c_test,
        probes,
        extra=('-entropy0', '1.0E3', '-radius0', '1.0E6', '-time0', '3.154E7'),
    )
    assert scaled['rho'] == pytest.approx(defaults['rho'], rel=1e-10)
    # The check discriminates only if the runs used different density
    # scalings; the blackbody50 and default scaling sets differ by
    # orders of magnitude in SC->DENSITY.
    assert scaled['rho'][1] == pytest.approx(RHOS - 6.7e10 * BETA / GRAVITY, rel=1e-12)
