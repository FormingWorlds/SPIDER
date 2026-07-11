"""Tests for rhs.c (assembly of the entropy time derivative).

Reads the JSON output of dedicated short blackbody50 runs. rhs.c
assembles dS/dt from the flux divergence and source terms; the output
exposes it directly as dSdt_s. Invariants exercised: consistency of the
reported time derivative with the finite-difference slope of
consecutive outputs, and the cooling sign structure without heat
sources. See docs/How-to/build_tests.md for the tier system.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests._json_utils import data_si, read_output

pytestmark = [pytest.mark.smoke, pytest.mark.timeout(60)]

SECONDS_PER_YEAR = 365.25 * 24.0 * 3600.0


@pytest.fixture(scope='module')
def blackbody_dt10(cached_spider_run):
    """Two 10-year macro steps, short enough for tight slope comparisons.

    The 100-year default step leaves too much curvature between outputs
    for a finite-difference check; 10-year steps bound the trapezoid
    error near the solver tolerance level.
    """
    return cached_spider_run(
        overrides=('-nstepsmacro', '2', '-dtmacro', '10'),
        name='blackbody_dt10',
    )


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_reported_dsdt_matches_finite_difference_of_outputs(blackbody_dt10):
    """dSdt_s agrees with the slope of the entropy between outputs.

    Analytical anchor: the time derivative assembled by rhs.c must be
    the derivative of the trajectory the timestepper actually follows,
    so the midpoint average of dSdt_s at 10 and 20 years matches
    (S(20) - S(10)) / dt. Observed agreement is 0.7% at every node
    (midpoint rule over 10 years); rel 2e-2 leaves headroom without
    admitting a wrong-term regression, which shifts dSdt by order
    unity.
    """
    d1 = read_output(blackbody_dt10, 10)
    d2 = read_output(blackbody_dt10, 20)
    dt = 10.0 * SECONDS_PER_YEAR
    fd_slope = (data_si(d2, 'S_s') - data_si(d1, 'S_s')) / dt
    midpoint = 0.5 * (data_si(d1, 'dSdt_s') + data_si(d2, 'dSdt_s'))
    np.testing.assert_allclose(fd_slope, midpoint, rtol=2e-2)
    # Sign guard: the mantle cools everywhere in this configuration.
    assert np.all(midpoint < 0.0)
    # Scale guard: early magma-ocean cooling rates are of order
    # 1e-8 J/kg/K/s here; ten decades either way flags a unit slip
    # (e.g. per year instead of per second).
    assert 1e-12 < np.max(np.abs(midpoint)) < 1e-4


@pytest.mark.physics_invariant
def test_cooling_sign_structure_and_finiteness(blackbody_short):
    """Without heat sources every node loses entropy and stays finite.

    blackbody50 configures no radiogenic or tidal heating, so dS/dt < 0
    throughout the mantle; the source arrays are identically zero (limit
    input for the source-term assembly).
    """
    doc = read_output(blackbody_short, 200)
    dsdt = data_si(doc, 'dSdt_s')
    assert np.all(np.isfinite(dsdt))
    assert np.all(dsdt < 0.0)
    # Source terms are switched off in this configuration.
    assert np.allclose(data_si(doc, 'Hradio_s'), 0.0, atol=1e-30)
    assert np.allclose(data_si(doc, 'Htidal_s'), 0.0, atol=1e-30)
    # Vigorous convection keeps the top of the molten layer on an
    # adiabat, so the entropy declines uniformly there (observed spread
    # 4e-5 of the magnitude over the first 20 staggered nodes). Closer
    # to the solidification front the rate departs from the adiabatic
    # value even while phi is still 1, so the window stays well above
    # the front.
    top = dsdt[:20]
    spread = float(np.max(top) - np.min(top))
    assert abs(spread) < 1e-3 * float(np.abs(top).max())
