"""Tests for matprop.c (two-phase material property blending).

Invariants exercised: recovery of the configured viscosity end members
in the fully molten and fully solid limits of the rheological blend,
positivity of density, heat capacity, thermal expansivity, and
viscosity at every node, constancy of the blended conductivity when
both phases share one value, and monotonicity of the viscosity across
the rheological transition in a part-solidified mantle. See
docs/How-to/build_tests.md for the tier system.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests._json_utils import data_si, read_output

pytestmark = [pytest.mark.smoke, pytest.mark.timeout(60)]

# Viscosity end members configured in tests/opts/blackbody50.opts.
MELT_LOG10_VISC = 2.0  # log10(Pa s)
SOLID_LOG10_VISC = 21.0  # log10(Pa s)


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_viscosity_recovers_configured_end_members(blackbody_short, cached_spider_run):
    """The phase-blended viscosity reaches both configured end members.

    Analytical anchor: in the single-phase limits the two-phase blend
    must return the pure-phase viscosities, melt_log10visc = 2.0 and
    solid_log10visc = 21.0 from blackbody50.opts. The hot initial
    condition (adiabat entropy 2600 J/kg/K) is fully molten at every
    node; a cold restart of the same configuration at 1600 J/kg/K puts
    the deep mantle below the solidus, providing the solid limit.
    """
    # Melt limit: phi = 1 at all 50 basic nodes of the standard IC.
    doc_hot = read_output(blackbody_short, 0)
    phi_hot = data_si(doc_hot, 'phi_b')
    visc_hot = data_si(doc_hot, 'visc_b')  # Pa s
    molten = phi_hot > 0.99
    # The selection must not be vacuous; the hot IC melts every node.
    assert molten.sum() == 50
    # abs=0.01 in log10 space: the smooth rheological step saturates at
    # phi = 1 and the observed deviation is only 3e-6 decades, so the
    # tolerance carries three decades of headroom while staying 1900x
    # tighter than the 19-decade melt-to-solid contrast.
    np.testing.assert_allclose(np.log10(visc_hot[molten]), MELT_LOG10_VISC, atol=0.01)

    # Solid limit: a 0-step run with a cold adiabat; the IC alone
    # exercises the blend, so no time integration is needed.
    outdir = cached_spider_run(
        overrides=('-nstepsmacro', '0', '-ic_adiabat_entropy', '1600'),
        name='cold_solid_ic',
    )
    doc_cold = read_output(outdir, 0)
    phi_cold = data_si(doc_cold, 'phi_b')
    visc_cold = data_si(doc_cold, 'visc_b')  # Pa s
    # Threshold 1e-3 rather than 1e-2: just below phi = 0.01 the smooth
    # step (phi_critical 0.4, phi_width 0.15) still carries ~0.5% melt
    # weight and log10(visc) sits at 20.91; below 1e-3 the residual
    # stays under 0.033 decades. Eleven deep nodes qualify.
    solid = phi_cold < 1e-3
    assert solid.sum() >= 5
    # abs=0.05 covers the observed 0.033-decade residual of the smooth
    # step at exactly phi = 0 while remaining 380x smaller than the
    # end-member contrast.
    np.testing.assert_allclose(np.log10(visc_cold[solid]), SOLID_LOG10_VISC, atol=0.05)

    # Swapped-phase guard: the recovered limits must span far more than
    # any blending artefact; 19 decades separate the configured end
    # members, so a melt/solid swap fails by more than 10 decades.
    log10_gap = np.log10(visc_cold[solid]).min() - np.log10(visc_hot[molten]).max()
    assert log10_gap > 10.0
    # Positivity: the blend must never produce a non-positive viscosity.
    assert np.all(visc_hot > 0)
    assert np.all(visc_cold > 0)


@pytest.mark.physics_invariant
def test_material_properties_positive_and_conductivity_constant(blackbody_full):
    """Blended material properties stay positive; equal-phase conductivity is exact.

    In the part-solidified 1200-year state the blend is evaluated across
    the whole melt-fraction range reached by the run, including the
    surface and core-mantle boundary nodes as the geometric edge cases.
    """
    doc = read_output(blackbody_full, 1200)
    rho_b = data_si(doc, 'rho_b')  # kg/m^3
    cp_b = data_si(doc, 'cp_b')  # J/kg/K
    cond_b = data_si(doc, 'cond_b')  # W/m/K
    alpha_b = data_si(doc, 'alpha_b')  # 1/K

    # Positivity at every node, surface (index 0) through CMB (index -1).
    assert np.all(rho_b > 0)
    assert np.all(cp_b > 0)
    assert np.all(alpha_b > 0)

    # Both phases are configured with conductivity 4.0 W/m/K, so the
    # blend must return the common value at ANY melt fraction; a
    # weighting defect that leaks the melt fraction into the result
    # would break the constancy. rel=1e-10 against the observed 2e-16
    # round-off leaves six decades of headroom.
    np.testing.assert_allclose(cond_b, 4.0, rtol=1e-10)
    # Scale guard: silicate conductivities are of order 1 W/m/K; a
    # nondimensional leak or unit slip would move the value far from 4.
    assert 1.0 < cond_b.mean() < 10.0  # W/m/K


@pytest.mark.physics_invariant
def test_viscosity_rises_monotonically_across_rheological_transition(blackbody_full):
    """Viscosity grows monotonically as the melt fraction falls with depth.

    In the part-solidified 1200-year state the melt fraction decreases
    strictly from the surface (phi = 0.76) to the CMB (phi = 0.39),
    crossing the configured transition midpoint phi_critical = 0.4, so
    the node sequence sweeps the steep flank of the rheological step.
    """
    doc = read_output(blackbody_full, 1200)
    phi_b = data_si(doc, 'phi_b')
    visc_b = data_si(doc, 'visc_b')  # Pa s
    log10_visc = np.log10(visc_b)

    # Boundedness: melt fraction is a mass fraction in [0, 1].
    assert np.all(phi_b >= 0)
    assert np.all(phi_b <= 1)
    # The run must actually straddle the transition midpoint, otherwise
    # the monotonicity below would only probe the flat end members.
    assert phi_b.min() < 0.4 < phi_b.max()

    # phi falls strictly with depth in this state (surface first), and
    # log10(visc) rises strictly with it; the smallest observed step is
    # 0.08 decades, so strict inequality holds with real margin rather
    # than numerical wiggle.
    assert np.all(np.diff(phi_b) < 0)
    assert np.all(np.diff(log10_visc) > 0)
    # Discrimination: the traversal spans > 3 decades (observed 10.2),
    # so a frozen or phase-swapped blend cannot pass.
    assert log10_visc[-1] - log10_visc[0] > 3.0
