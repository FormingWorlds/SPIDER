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


@pytest.fixture(scope='module')
def core_flux_run(cached_spider_run):
    """Two-macro-step blackbody50 run with a prescribed core heat flux."""
    return cached_spider_run(
        overrides=('-nstepsmacro', '2', '-CORE_BC', '2', '-core_bc_value', '1.0e5'),
        name='core_flux',
    )


@pytest.mark.physics_invariant
def test_prescribed_core_flux_slows_cmb_cooling(core_flux_run, blackbody_short):
    """CORE_BC 2 injects heat at the CMB and slows the deep cooling.

    Against the default core-cooling run at identical initial
    conditions and output times, a prescribed 1e5 W/m^2 inflow keeps
    the deepest staggered node hotter after 200 years (observed 2515
    vs 2511 J/kg/K) and roughly doubles the total heat flux carried at
    the core-mantle boundary node.
    """
    flux_0 = data_si(read_output(core_flux_run, 0), 'S_s')  # J/kg/K
    cool_0 = data_si(read_output(blackbody_short, 0), 'S_s')  # J/kg/K
    # Edge case, identical IC: the boundary condition acts only during
    # integration, so t = 0 must agree between the two runs exactly.
    np.testing.assert_allclose(flux_0, cool_0, rtol=1e-12)

    flux_200 = data_si(read_output(core_flux_run, 200), 'S_s')
    cool_200 = data_si(read_output(blackbody_short, 200), 'S_s')
    # Direction discrimination: heating from below leaves the CMB node
    # hotter than core cooling does; the observed gap (3.9 J/kg/K) is
    # far above the CVODE tolerance floor.
    assert flux_200[-1] > cool_200[-1]
    assert flux_200[-1] - cool_200[-1] > 1.0  # J/kg/K

    # The prescribed inflow roughly doubles the CMB heat flux relative
    # to core cooling (observed 1.9e5 vs 9.2e4 W/m^2).
    jtot_flux = data_si(read_output(core_flux_run, 200), 'Jtot_b')  # W/m^2
    jtot_cool = data_si(read_output(blackbody_short, 200), 'Jtot_b')  # W/m^2
    assert jtot_flux[-1] > 1.5 * jtot_cool[-1]
    # Positivity: entropy stays physical under the modified BC.
    assert np.all(flux_200 > 0)


@pytest.fixture(scope='module')
def entropy_bc_run(cached_spider_run):
    """One-step run with constant-entropy boundaries and a steady IC.

    The prescribed boundary entropies (2550 and 2650 J/kg/K) bracket
    the 2600 J/kg/K adiabat; the steady-state energy solve keeps the
    perturbed initial condition integrable within one macro step.
    """
    return cached_spider_run(
        overrides=(
            '-nstepsmacro', '1',
            '-dtmacro', '10',
            '-ic_surface_entropy', '2550',
            '-ic_core_entropy', '2650',
            '-ic_steady_state_energy',
        ),
        name='entropy_bc_steady',
    )


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_constant_entropy_bc_pins_the_initial_surface(entropy_bc_run, blackbody_short):
    """ic_surface_entropy fixes the surface basic node exactly.

    Anchor: analytical identity. The constant-entropy boundary writes
    the option value (2550 J/kg/K) onto the surface basic node, and the
    subsequent steady-state solve preserves it, so the initial output
    carries the prescribed value exactly. The default run's surface
    (2599.7 J/kg/K, from the 2600 adiabat and the ic_dsdr gradient)
    discriminates the option not being applied.
    """
    s_b = data_si(read_output(entropy_bc_run, 0), 'S_b')  # J/kg/K

    # rel=1e-10: the value is assigned, not solved for.
    assert s_b[0] == pytest.approx(2550.0, rel=1e-10)

    # Discrimination guard: the default IC surface value differs by
    # ~50 J/kg/K, five orders above the pin tolerance.
    s_b_default = data_si(read_output(blackbody_short, 0), 'S_b')
    assert abs(s_b_default[0] - 2550.0) > 40.0  # J/kg/K

    # The core-side prescription seeds the deep profile before the
    # steady-state solve rebalances it; the result must stay physical
    # and within the entropy range of the loaded tables.
    assert np.all(s_b > 0)
    assert 2400.0 < s_b[-1] < 2700.0  # J/kg/K
