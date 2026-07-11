"""Tests for twophase.c (global melt and solid mass bookkeeping).

Reads the JSON output of the cached blackbody50 runs. twophase.c sets
the global liquid and solid masses and feeds the rheological-front
bookkeeping. Invariants exercised: mantle mass closure at every output
time, monotone solidification during secular cooling, and the identity
between the reported global melt fraction and the mass-weighted mean of
the local melt-fraction profile. See docs/How-to/build_tests.md for the
tier system.
"""

from __future__ import annotations

import pytest

from tests._json_utils import atmosphere_si, data_si, field_si, read_output

pytestmark = [pytest.mark.smoke, pytest.mark.timeout(60)]

# All output times of the 12-step blackbody50 run.
FULL_TIMES = tuple(range(0, 1300, 100))


@pytest.mark.physics_invariant
def test_mantle_mass_closure_at_every_output_time(blackbody_full):
    """mass_liquid + mass_solid equals mass_mantle at every macro step.

    Mass closure is the central conservation contract of the two-phase
    bookkeeping. The t = 0 edge is the fully molten limit input where
    mass_solid must vanish and the closure is trivially the liquid mass.
    """
    for time in FULL_TIMES:
        doc = read_output(blackbody_full, time)
        m_liq = atmosphere_si(doc, 'mass_liquid')
        m_sol = atmosphere_si(doc, 'mass_solid')
        m_man = atmosphere_si(doc, 'mass_mantle')
        assert m_liq + m_sol == pytest.approx(m_man, rel=1e-12), f't = {time} yr'
        assert m_liq >= 0.0 and m_sol >= 0.0
    # Fully molten limit at the initial condition.
    doc0 = read_output(blackbody_full, 0)
    assert atmosphere_si(doc0, 'mass_solid') == pytest.approx(0.0, abs=1e-6)
    # Scale guard: the blackbody50 mantle is Earth-like, a few 1e24 kg;
    # a nondimensional leak would sit near unity.
    assert 1.0e24 < atmosphere_si(doc0, 'mass_mantle') < 1.0e25


@pytest.mark.physics_invariant
def test_solidification_proceeds_monotonically_under_cooling(blackbody_full):
    """The solid mass grows and the liquid mass shrinks while cooling.

    No heat sources are configured, so secular cooling drives one-way
    solidification; the mantle mass itself stays constant (closed
    system).
    """
    m_liq, m_sol, m_man = [], [], []
    for time in FULL_TIMES:
        doc = read_output(blackbody_full, time)
        m_liq.append(atmosphere_si(doc, 'mass_liquid'))
        m_sol.append(atmosphere_si(doc, 'mass_solid'))
        m_man.append(atmosphere_si(doc, 'mass_mantle'))
    assert all(a >= b for a, b in zip(m_liq, m_liq[1:]))
    assert all(a <= b for a, b in zip(m_sol, m_sol[1:]))
    # Closed system: the mantle mass does not drift.
    assert m_man[0] == pytest.approx(m_man[-1], rel=1e-12)
    # By 1200 yr roughly half the mantle has solidified in this
    # configuration; the run must have left the trivial all-molten state
    # for the monotonicity checks above to discriminate anything.
    assert m_sol[-1] > 0.25 * m_man[-1]


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_global_melt_fraction_is_the_mass_weighted_profile_mean(blackbody_full):
    """phi_global equals both Mliq/Mmantle and the mass-weighted phi_s mean.

    Analytical identity: the global melt fraction reported with the
    rheological front is defined by the same mass integrals that set
    mass_liquid, so it must equal Mliq/Mmantle and the mass-weighted
    mean of the staggered-node melt fraction. t = 1200 yr probes the
    part-solidified state (phi about 0.51) where a volume weighting or
    an unweighted mean would differ well beyond the tolerance.
    """
    doc = read_output(blackbody_full, 1200)
    phi_reported = float(field_si(doc['rheological_front_phi']['phi_global'])[0])
    m_liq = atmosphere_si(doc, 'mass_liquid')
    m_man = atmosphere_si(doc, 'mass_mantle')
    assert phi_reported == pytest.approx(m_liq / m_man, rel=1e-10)

    phi_s = data_si(doc, 'phi_s')
    mass_s = data_si(doc, 'mass_s')
    weighted = float((phi_s * mass_s).sum() / mass_s.sum())
    assert phi_reported == pytest.approx(weighted, rel=1e-10)
    # Unweighted-mean guard: with the melt concentrated near the top,
    # the plain average of phi_s differs from the mass-weighted mean by
    # more than the tolerance.
    unweighted = float(phi_s.mean())
    assert abs(phi_reported - unweighted) > 1e-3
    # Boundedness and scale guards.
    assert 0.0 <= phi_reported <= 1.0
    assert 0.2 < phi_reported < 0.9
