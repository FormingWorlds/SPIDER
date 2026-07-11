"""Tests for eos_composite.c (two-phase melt + solid blending).

Driven through the tests/c/test_eos_composite executable, which builds
the same melt + solid lookup pair as the blackbody50 configuration and
evaluates the composite across the melting interval. Invariants
exercised: melt-fraction boundedness and its linear-in-entropy contract,
fusion consistency with the phase boundaries, and the pure-phase limits
far from the melting interval. See docs/How-to/build_tests.md for the
tier system.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]

REPO_ROOT = Path(__file__).resolve().parent.parent
OPTS = ('-options_file', str(REPO_ROOT / 'tests' / 'opts' / 'blackbody50.opts'))

# One mid-mantle pressure; the melting interval there spans roughly
# 1524 (solidus) to 2128 (liquidus) J/kg/K for the shipped tables.
P_MID = 1.0e10  # Pa


def _composite_eval(c_test, s_list, p=P_MID):
    """Evaluate the composite EOS at fixed pressure and given entropies."""
    n = len(s_list)
    return c_test(
        'test_eos_composite',
        (
            *OPTS,
            '-P_si',
            ','.join(str(p) for _ in range(n)),
            '-S_si',
            ','.join(str(s) for s in s_list),
        ),
    )


@pytest.mark.physics_invariant
def test_phase_fraction_bounded_and_truncation_contract_visible(c_test):
    """The melt fraction is clamped to [0, 1] outside the melting interval.

    Far below the solidus and far above the liquidus the untruncated
    linear map leaves [0, 1]; the public value must clamp (graceful-clamp
    error contract), never extrapolate.
    """
    out = _composite_eval(c_test, (1200.0, 1800.0, 2128.0, 3100.0))
    phi = out['phase_fraction']
    assert all(0.0 <= p <= 1.0 for p in phi)
    # The clamp is doing real work at the extremes: the raw values sit
    # outside [0, 1] there.
    raw = out['phase_fraction_no_truncation']
    assert raw[0] < 0.0
    assert raw[3] > 1.0
    # Interior point: raw and clamped agree where no clamping is needed.
    assert phi[1] == pytest.approx(raw[1], rel=1e-12)


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_fusion_equals_liquidus_minus_solidus_and_phi_is_linear_in_entropy(c_test):
    """Fusion entropy and melt fraction follow their defining relations.

    Analytical limit: by construction of the two-phase region,
    fusion = S_liquidus - S_solidus and
    phi = (S - S_solidus) / fusion between the boundaries. Probing at
    one quarter of the interval discriminates the correct denominator
    (fusion, about 604 J/kg/K here) from the plausible wrong one
    (the liquidus entropy, about 2128 J/kg/K).
    """
    out = _composite_eval(c_test, (1675.34,))
    liq = out['liquidus_S'][0]
    sol = out['solidus_S'][0]
    fusion = out['fusion'][0]
    assert fusion == pytest.approx(liq - sol, rel=1e-10)
    # Liquidus must sit above solidus for the loaded tables.
    assert liq > sol
    # The probe entropy is S_solidus + 0.25 * fusion for the shipped
    # tables (1524.43 + 151.0); a wrong-denominator regression would
    # return (S - sol)/liq of about 0.071 instead of 0.25.
    s_probe = 1675.34
    expected_phi = (s_probe - sol) / fusion
    assert out['phase_fraction'][0] == pytest.approx(expected_phi, rel=1e-6)
    assert abs(out['phase_fraction'][0] - (s_probe - sol) / liq) > 0.15
    # Scale guard: the fusion entropy of the dK09 tables at 10 GPa is a
    # few hundred J/kg/K, not a few or a few thousand.
    assert 100.0 < fusion < 1500.0


@pytest.mark.physics_invariant
def test_pure_phase_limits_recover_the_single_phase_lookups(c_test):
    """Far from the melting interval the composite matches the pure phases.

    Above the liquidus the composite must return the melt lookup values
    and below the solidus the solid lookup values (analytical limit of
    the blending). The melt and solid answers differ from each other by
    far more than the agreement tolerance, so a swapped-slot regression
    fails loudly.
    """
    s_melt, s_solid = 3000.0, 1200.0
    comp = _composite_eval(c_test, (s_melt, s_solid))

    pure = {}
    for prefix, s in (('melt', s_melt), ('solid', s_solid)):
        pure[prefix] = c_test(
            'test_eos',
            (*OPTS, '-eos_prefix', prefix, '-P_si', str(P_MID), '-S_si', str(s)),
        )
    # Composite above the liquidus = pure melt.
    assert comp['rho'][0] == pytest.approx(pure['melt']['rho'][0], rel=1e-10)
    assert comp['T'][0] == pytest.approx(pure['melt']['T'][0], rel=1e-10)
    # Composite below the solidus = pure solid.
    assert comp['rho'][1] == pytest.approx(pure['solid']['rho'][0], rel=1e-10)
    assert comp['T'][1] == pytest.approx(pure['solid']['T'][0], rel=1e-10)
    # Swapped-phase discrimination: melt and solid densities differ by
    # hundreds of kg/m3 at these probe points.
    assert abs(pure['melt']['rho'][0] - pure['solid']['rho'][0]) > 100.0
