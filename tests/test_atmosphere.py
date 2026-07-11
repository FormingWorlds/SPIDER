"""Tests for atmosphere.c (grey-body surface flux and derived temperatures).

Driven through the shared cached blackbody50 runs of the spider binary.
Invariants exercised: the Stefan-Boltzmann grey-body analytical limit
for the surface flux, secular cooling of the surface temperature and
outgoing flux across macro steps, the skin-temperature closed form, and
positivity and ordering of the reported temperatures. The fully molten
initial condition (t = 0) is the hottest edge state and must radiate
the strictly largest flux. See docs/How-to/build_tests.md for the tier
system.
"""

from __future__ import annotations

import pytest

from tests._json_utils import atmosphere_si, read_output

pytestmark = [pytest.mark.smoke, pytest.mark.timeout(60)]

# Stefan-Boltzmann constant as hard-coded in constants.c; the CODATA
# update differs only in the seventh digit, far inside the pin
# tolerances used below, but the source value is the contract.
SIGMA = 5.670367e-08  # W m^-2 K^-4
TEQM = 273.0  # K, blackbody50 planetary equilibrium temperature
EMISSIVITY = 1.0  # blackbody50 emissivity0 (SURFACE_BC 1, grey body)


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_grey_body_flux_matches_stefan_boltzmann_limit(blackbody_short):
    """The reported surface flux equals the grey-body analytical limit.

    Anchor: the Stefan-Boltzmann grey-body flux
    Fatm = emissivity * sigma * (T_surf^4 - teqm^4), the closed form
    atmosphere.c evaluates for SURFACE_BC 1 with emissivity0 = 1. The
    200-year output is read so the pin sits well away from the initial
    condition.
    """
    doc = read_output(blackbody_short, 200)
    t_surf = atmosphere_si(doc, 'temperature_surface')  # K
    fatm = atmosphere_si(doc, 'Fatm')  # W/m2

    expected = EMISSIVITY * SIGMA * (t_surf**4 - TEQM**4)
    # rel=1e-6: the run reproduces the closed form to machine precision;
    # 1e-6 leaves headroom for compiler value reordering only.
    assert fatm == pytest.approx(expected, rel=1e-6)

    # Exponent guard: a T^3 slip at T_surf ~ 1860 K gives ~360 W/m2
    # instead of ~6.7e5 W/m2, off by three orders of magnitude and far
    # beyond the pin tolerance.
    wrong_cubed = EMISSIVITY * SIGMA * (t_surf**3 - TEQM**3)
    assert abs(fatm - wrong_cubed) > 0.5 * fatm
    # Sign guard: the hot interior radiates outward.
    assert fatm > 0
    # Scale guard: magma-ocean fluxes sit at 1e4..1e7 W/m2; a
    # nondimensional value leaking through unscaled would sit near unity.
    assert 1e2 < fatm < 1e9


@pytest.mark.physics_invariant
def test_surface_cools_and_flux_decays_across_macro_steps(blackbody_short):
    """Secular cooling: T_surf and Fatm fall monotonically over 200 years.

    The blackbody50 configuration has no internal heating, so the
    grey-body boundary drains energy and both the surface temperature
    and the outgoing flux must decrease between successive outputs.
    The t = 0 document is the fully molten initial condition, the
    hottest edge state, and must carry the strictly largest flux
    (limit-input check). The radiative skin temperature obeys its
    closed form and stays below the surface temperature throughout.
    """
    docs = [read_output(blackbody_short, t) for t in (0, 100, 200)]
    t_surf = [atmosphere_si(d, 'temperature_surface') for d in docs]
    fatm = [atmosphere_si(d, 'Fatm') for d in docs]
    t_skin = [atmosphere_si(d, 'Tskin') for d in docs]

    # Monotone cooling with all temperatures physical (positive Kelvin).
    assert t_surf[0] > t_surf[1] > t_surf[2] > 0
    assert fatm[0] > fatm[1] > fatm[2] > 0
    # Limit input: the initial condition radiates strictly more than
    # any later output.
    assert fatm[0] > max(fatm[1:])
    for ts, tk, fa in zip(t_surf, t_skin, fatm):
        # Skin closed form Tskin = (Fatm / (2 sigma) + teqm^4)^(1/4);
        # halving the net flux places the skin below the surface.
        assert tk == pytest.approx((fa / (2.0 * SIGMA) + TEQM**4) ** 0.25, rel=1e-6)
        assert 0 < tk < ts
    # The emissivity stays at the configured constant for SURFACE_BC 1.
    for d in docs:
        assert atmosphere_si(d, 'emissivity') == pytest.approx(EMISSIVITY, rel=1e-12)
