"""Tests for bc.c (surface and core-mantle boundary conditions).

Driven through short cached blackbody50 runs of the spider binary.
Invariants exercised: the prescribed-flux surface boundary condition
(SURFACE_BC 4) echoing its SI value to the output with the emissivity
derived by inverting the grey-body law, dispatch discrimination against
the grey-body branch, temperature ordering between the surface and the
core-mantle boundary on the default grey-body run, the parameterised
ultrathin boundary layer placing the reported surface temperature below
the top basic node, and the zero-pressure limit at the surface node.
See docs/How-to/build_tests.md for the tier system.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests._json_utils import atmosphere_si, data_si, read_output

pytestmark = [pytest.mark.smoke, pytest.mark.timeout(120)]

# Stefan-Boltzmann constant as hard-coded in constants.c.
SIGMA = 5.670367e-08  # W m^-2 K^-4
TEQM = 273.0  # K, blackbody50 planetary equilibrium temperature
PRESCRIBED_FLUX = 1.0e5  # W/m2, SI value passed via -surface_bc_value


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_prescribed_flux_bc_echoes_value_and_inverts_emissivity(cached_spider_run):
    """SURFACE_BC 4 fixes the outgoing flux at the prescribed SI value.

    Anchor: analytical identity. The prescribed flux must appear
    unchanged in the output, and bc.c/atmosphere.c derive the effective
    emissivity by inverting the grey-body law,
    emissivity = Fatm / (sigma * (T_surf^4 - teqm^4)).
    """
    outdir = cached_spider_run(
        overrides=('-nstepsmacro', '1', '-SURFACE_BC', '4', '-surface_bc_value', '1.0e5'),
        name='bc_prescribed_flux',
    )
    doc = read_output(outdir, 100)
    fatm = atmosphere_si(doc, 'Fatm')  # W/m2
    t_surf = atmosphere_si(doc, 'temperature_surface')  # K
    emissivity = atmosphere_si(doc, 'emissivity')

    # rel=1e-9: the option value is stored and re-emitted, not
    # recomputed, so only scaling round-trip error can enter.
    assert fatm == pytest.approx(PRESCRIBED_FLUX, rel=1e-9)

    # Wrong-path guard: the grey-body branch at this run's own surface
    # temperature would give ~8.4e5 W/m2, more than a factor of eight
    # above the prescribed value, so the pin discriminates the
    # SURFACE_BC dispatch and not a coincidental grey-body agreement.
    grey = SIGMA * (t_surf**4 - TEQM**4)
    assert abs(PRESCRIBED_FLUX - grey) > 0.1 * grey
    # Emissivity inversion pin: ~0.12 here, clearly away from the
    # configured emissivity0 = 1.0 of the grey-body branch.
    assert emissivity == pytest.approx(PRESCRIBED_FLUX / grey, rel=1e-6)
    assert abs(emissivity - 1.0) > 0.5
    # Sign and scale guards: outward flux in the magma-ocean range; a
    # nondimensional leak would sit near unity.
    assert fatm > 0
    assert 1e2 < fatm < 1e9


@pytest.mark.physics_invariant
def test_mantle_cools_from_the_top_between_surface_and_cmb(blackbody_short):
    """Grey-body cooling keeps the CMB hotter than the surface node.

    On the default SURFACE_BC 1 run the mantle loses heat through the
    top, so the basic-node temperature profile (ordered surface first)
    must be hotter at the core-mantle boundary than at the surface. The
    parameterised ultrathin boundary layer in bc.c drops the reported
    surface temperature below the top basic node, so the two agree in
    scale but are not equal. The surface node is the zero-pressure
    limit of the Adams-Williamson profile.
    """
    doc = read_output(blackbody_short, 200)
    temp_b = data_si(doc, 'temp_b')  # K, surface first
    pressure_b = data_si(doc, 'pressure_b')  # Pa, surface first
    t_surf = atmosphere_si(doc, 'temperature_surface')  # K

    # Cooling from the top: CMB node hotter than the surface node,
    # every node at a physical (positive Kelvin) temperature.
    assert temp_b[-1] > temp_b[0]
    assert np.all(temp_b > 0)
    # The reported surface temperature sits BELOW the top basic node:
    # the boundary layer drops ~2500 K at the node to ~1860 K at the
    # surface (observed ratio ~0.74). Assert the ordering plus a factor
    # of two scale agreement instead of equality.
    assert 0 < t_surf < temp_b[0]
    assert t_surf > 0.5 * temp_b[0]
    # Edge case, surface basic node: the pressure is zero to rounding.
    # The output carries about -1e-3 Pa of roundoff against a 1.4e11 Pa
    # CMB pressure, so bound the magnitude rather than the sign.
    assert abs(pressure_b[0]) < 1.0  # Pa
    # Scale guard on the deep end: blackbody50 reaches ~1.38e11 Pa at
    # the CMB; a nondimensional leak would sit near unity.
    assert 1e10 < pressure_b[-1] < 1e12
