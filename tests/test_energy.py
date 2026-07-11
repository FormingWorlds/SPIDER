"""Tests for energy.c (heat flux assembly and transport mechanisms).

Invariants exercised: assembly of the total heat flux from the four
transport components at interior nodes, positivity of the eddy
diffusivity, consistency of the energy flow Etot_b with Jtot_b times
the spherical area, the zero-flux analytical limit of each disabled
transport mechanism, and the identity between the top-node flux and
the grey-body atmospheric flux. See docs/How-to/build_tests.md for
the tier system.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests._json_utils import atmosphere_si, data_si, read_output

pytestmark = [pytest.mark.smoke, pytest.mark.timeout(60)]

FLUX_COMPONENTS = ('Jconv_b', 'Jcond_b', 'Jmix_b', 'Jgrav_b')


@pytest.mark.physics_invariant
def test_total_flux_assembles_from_transport_components(blackbody_short):
    """Jtot equals the sum of the four transport fluxes at interior nodes.

    Conservation contract of the flux assembly: with conduction,
    convection, mixing, and separation all enabled, the total heat flux
    at every interior basic node is exactly the component sum. The
    evolved 200-year state exercises all four mechanisms at once.
    """
    doc = read_output(blackbody_short, 200)
    jtot = data_si(doc, 'Jtot_b')  # W/m^2
    jsum = sum(data_si(doc, name) for name in FLUX_COMPONENTS)

    # rtol=1e-8: the sum is exact in the solver, but the convective and
    # mixing terms partially cancel near the CMB, so the JSON's finite
    # output precision leaves a residual (observed max rel 2e-10); the
    # margin absorbs compiler-to-compiler value reordering on top.
    np.testing.assert_allclose(jtot[1:], jsum[1:], rtol=1e-8)
    # Edge case, surface node: index 0 carries the imposed grey-body
    # boundary flux instead of the assembled interior sum, so the
    # closure must NOT hold there (observed 35% apart at 200 years);
    # this guards against a blanket slice hiding a shifted BC.
    assert abs(jtot[0] - jsum[0]) > 0.01 * abs(jtot[0])

    # Positivity: the eddy diffusivity backing the convective flux can
    # never be negative; here it spans 3e4 to 3e7 m^2/s.
    kappah = data_si(doc, 'kappah_b')  # m^2/s
    assert np.all(kappah >= 0)
    assert 1e3 < kappah.max() < 1e12  # m^2/s, vigorous magma-ocean convection

    # Consistency: the energy flow is the flux times the true spherical
    # area (area_b carries the 4*pi), exact to output precision.
    etot = data_si(doc, 'Etot_b')  # W
    area_b = data_si(doc, 'area_b')  # m^2
    assert np.all(np.isfinite(etot))
    np.testing.assert_allclose(etot, jtot * area_b, rtol=1e-12)


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_disabled_transport_mechanisms_carry_zero_flux(blackbody_short, cached_spider_run):
    """Each disabled transport mechanism contributes exactly zero flux.

    Analytical anchor: a transport mechanism switched off by its option
    must carry identically zero flux, and the remaining mechanisms must
    assemble the total alone. Both limits run 0 macro steps; the flux
    arrays are already populated from the initial state.
    """
    # Conduction off: Jcond vanishes while convection keeps transporting.
    no_cond = cached_spider_run(
        overrides=('-nstepsmacro', '0', '-CONDUCTION', '0'),
        name='no_conduction',
    )
    doc_nc = read_output(no_cond, 0)
    jcond_nc = data_si(doc_nc, 'Jcond_b')  # W/m^2
    # atol=1e-20 W/m^2 sits 25 decades below the active fluxes in this
    # state (1e5 to 2e9 W/m^2); the observed values are exactly zero.
    np.testing.assert_allclose(jcond_nc, 0.0, atol=1e-20)
    # Wrong-path guard: convection must remain active, otherwise the
    # zero above would only prove a dead run.
    jconv_nc = data_si(doc_nc, 'Jconv_b')  # W/m^2
    assert np.abs(jconv_nc).max() > 1e3

    # Everything but conduction off: Jtot reduces to Jcond alone.
    cond_only = cached_spider_run(
        overrides=(
            '-nstepsmacro',
            '0',
            '-CONVECTION',
            '0',
            '-MIXING',
            '0',
            '-SEPARATION',
            '0',
        ),
        name='conduction_only',
    )
    doc_co = read_output(cond_only, 0)
    for name in ('Jconv_b', 'Jmix_b', 'Jgrav_b'):
        np.testing.assert_allclose(data_si(doc_co, name), 0.0, atol=1e-20)
    jtot_co = data_si(doc_co, 'Jtot_b')  # W/m^2
    jcond_co = data_si(doc_co, 'Jcond_b')  # W/m^2
    # Interior nodes: the assembly collapses to the conductive flux with
    # zero observed residual; rtol=1e-12 is the output-precision floor.
    np.testing.assert_allclose(jtot_co[1:], jcond_co[1:], rtol=1e-12, atol=1e-20)
    # Edge case, surface node: the grey-body boundary flux (8e5 W/m^2)
    # overrides the tiny conductive flux (0.01 W/m^2) at index 0.
    assert abs(jtot_co[0] - jcond_co[0]) > 1e3

    # Scale guard on the full-physics reference state: the peak total
    # flux at the fully molten IC is convective and large (observed
    # 2e9 W/m^2); a nondimensional leak would sit near unity.
    jtot_full = data_si(read_output(blackbody_short, 0), 'Jtot_b')
    assert 1e6 < np.abs(jtot_full).max() < 1e12  # W/m^2


@pytest.mark.physics_invariant
def test_surface_node_flux_is_the_grey_body_atmospheric_flux(blackbody_short):
    """The top-node total flux and the atmospheric Fatm are the same quantity.

    With SURFACE_BC 1 the grey-body flux emissivity*sigma*(T_surf^4 -
    Teqm^4) is imposed as the top-node total heat flux, so Jtot_b[0]
    and Fatm agree identically in W/m^2 with no 4*pi factor between
    them (areas enter only through Etot_b = Jtot_b * area_b).
    """
    doc = read_output(blackbody_short, 200)
    jtot_surface = data_si(doc, 'Jtot_b')[0]  # W/m^2
    fatm = atmosphere_si(doc, 'Fatm')  # W/m^2
    t_surf = atmosphere_si(doc, 'temperature_surface')  # K

    # Identity between the two output fields (observed bit-exact).
    assert jtot_surface == pytest.approx(fatm, rel=1e-12)

    # Closed-form pin with the Stefan-Boltzmann value from constants.c;
    # emissivity0 = 1 and teqm = 273 K per blackbody50.opts. The JSON
    # round-trip leaves < 1e-15 rel (observed 2e-16).
    sigma = 5.670367e-8  # W/m^2/K^4, as defined in constants.c
    expected = 1.0 * sigma * (t_surf**4 - 273.0**4)
    assert fatm == pytest.approx(expected, rel=1e-12)

    # Exponent guard: at T_surf = 1857 K, well above Teqm, a T^3 slip
    # changes the flux by a factor of several hundred.
    wrong_cubed = sigma * (t_surf**3 - 273.0**3)
    assert abs(fatm - wrong_cubed) > 0.5 * fatm
    # Constant guard: the 2018 CODATA sigma (5.670374419e-8) shifts the
    # flux by 1.3e-6 relative, resolvable above the 1e-12 tolerance, so
    # the pin identifies which constant the source actually uses.
    assert abs(fatm - 5.670374419e-8 * (t_surf**4 - 273.0**4)) > 1e-7 * fatm
    # Sign guard: a hot interior radiates outward.
    assert fatm > 0
    # Scale guard: magma-ocean surface fluxes are 1e2 to 1e9 W/m^2; a
    # nondimensional value leaking through unscaled would sit near unity.
    assert 1e2 < fatm < 1e9  # W/m^2
