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

pytestmark = [pytest.mark.smoke, pytest.mark.timeout(120)]

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


# Two-isotope internal heating configuration. The half-lives (100 and
# 200 years) are deliberately short so the decay resolves within the
# 200-year run; the production rates and concentrations are of the
# order of al26 and k40 in early solar system material.
HEATING_OVERRIDES = (
    '-nstepsmacro', '2',
    '-radionuclide_names', 'al26,k40',
    '-al26_t0', '0.0',
    '-al26_abundance', '1.0',
    '-al26_concentration', '10.0',
    '-al26_heat_production', '0.3568',
    '-al26_half_life', '100.0',
    '-k40_t0', '0.0',
    '-k40_abundance', '1.0',
    '-k40_concentration', '300.0',
    '-k40_heat_production', '2.92e-5',
    '-k40_half_life', '200.0',
    '-HTIDAL', '1',
    '-htidal_value', '1.0e-7',
)
# Specific heating of each isotope at t0: concentration (mass fraction)
# times isotopic abundance times heat production. al26 dominates.
H_AL26 = 10.0e-6 * 1.0 * 0.3568  # 3.568e-6 W/kg
H_K40 = 300.0e-6 * 1.0 * 2.92e-5  # 8.76e-9 W/kg
HTIDAL_VALUE = 1.0e-7  # W/kg, prescribed constant tidal heating


@pytest.fixture(scope='module')
def heating_run(cached_spider_run):
    """Two-macro-step blackbody50 run with radiogenic and tidal heating."""
    return cached_spider_run(overrides=HEATING_OVERRIDES, name='heating')


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_radiogenic_heating_pins_two_isotope_decay(heating_run):
    """Radiogenic heating sums both isotopes and follows exponential decay.

    Anchor: analytical limit. Each radionuclide contributes
    concentration * abundance * heat_production * 2^(-(t - t0)/half_life)
    of specific heating, uniform across the mantle. At t = 0 the sum is
    3.57676e-6 W/kg, and after 200 years (two al26 half-lives, one k40
    half-life) the total falls to 0.2506 of its initial value.
    """
    h_0 = data_si(read_output(heating_run, 0), 'Hradio_s')  # W/kg
    h_200 = data_si(read_output(heating_run, 200), 'Hradio_s')  # W/kg

    # Radiogenic heating is spatially uniform: the same isotopes and
    # concentration heat every shell (rel 1e-12 is roundoff headroom).
    np.testing.assert_allclose(h_0, h_0[0], rtol=1e-12)

    # rel=1e-6: the sum is evaluated in closed form from the option
    # values, so only scaling round-trip error enters.
    assert h_0[0] == pytest.approx(H_AL26 + H_K40, rel=1e-6)
    # Isotope-sum guard: dropping k40 shifts the total by 2.4e-3
    # relative, three orders above the pin tolerance.
    assert abs(h_0[0] - H_AL26) > 1e-3 * h_0[0]

    # Decay pin: the two-isotope weighted decay factor after 200 years.
    expected_ratio = (H_AL26 * 0.25 + H_K40 * 0.5) / (H_AL26 + H_K40)
    ratio = h_200[0] / h_0[0]
    # rel=1e-4: the run writes output exactly at t = 200 years, so the
    # closed-form factor applies with only output rounding on top.
    assert ratio == pytest.approx(expected_ratio, rel=1e-4)
    # Decay guards: no decay gives 1.0, a single-isotope slip gives
    # exactly 0.25 (al26 only) or 0.5 (k40 only); the two-isotope value
    # 0.25061 is resolved from all three far beyond the tolerance.
    assert abs(ratio - 1.0) > 0.7
    assert abs(ratio - 0.25) > 5e-4
    assert abs(ratio - 0.5) > 0.2
    # Sign guard: heat production is strictly positive.
    assert np.all(h_0 > 0) and np.all(h_200 > 0)


@pytest.mark.physics_invariant
def test_prescribed_tidal_heating_is_uniform_and_steady(heating_run):
    """HTIDAL 1 applies a constant specific heating that does not decay.

    The prescribed scalar must appear unchanged at every node and at
    every output time, in contrast to the radiogenic contribution in
    the same run, which decays by a factor of four over the window.
    """
    ht_0 = data_si(read_output(heating_run, 0), 'Htidal_s')  # W/kg
    ht_200 = data_si(read_output(heating_run, 200), 'Htidal_s')  # W/kg

    # rel=1e-12: the option value is stored and re-emitted, not
    # recomputed.
    np.testing.assert_allclose(ht_0, HTIDAL_VALUE, rtol=1e-12)
    np.testing.assert_allclose(ht_200, HTIDAL_VALUE, rtol=1e-12)

    # Scale guard: a nondimensional leak (the value divided by the
    # heat-generation scaling) would land far outside this bracket.
    assert 5e-8 < ht_0[0] < 2e-7  # W/kg

    # Contrast with the decaying radiogenic term in the same run: the
    # tidal column is time independent while Hradio drops fourfold.
    h_0 = data_si(read_output(heating_run, 0), 'Hradio_s')
    h_200 = data_si(read_output(heating_run, 200), 'Hradio_s')
    assert h_200[0] < 0.3 * h_0[0]
    assert ht_200[0] == pytest.approx(ht_0[0], rel=1e-12)


@pytest.mark.physics_invariant
def test_tidal_heating_profile_from_file_is_recovered(
    blackbody_short, run_spider, tmp_path
):
    """HTIDAL 2 reads a per-node heating profile and applies it verbatim.

    A linear ramp from 1e-8 to 5e-8 W/kg across the staggered nodes is
    written in the Interp1d file format (header with row count, scaling
    line, then pressure and heating columns) and must be recovered
    node for node. A file with the wrong number of rows must be
    refused, exercising the documented length check.
    """
    pressure_s = data_si(read_output(blackbody_short, 0), 'pressure_s')  # Pa
    n = len(pressure_s)
    ramp = np.linspace(1.0e-8, 5.0e-8, n)  # W/kg

    lines = [
        f'# 5 {n}',
        '# Pressure, Htidal',
        '# column * scaling factor should be SI units',
        '# scaling factors (constant) for each column given on line below',
        '# 1.0 1.0',
    ]
    lines += [f'{p:.18e} {h:.18e}' for p, h in zip(pressure_s, ramp)]
    profile = tmp_path / 'htidal_ramp.dat'
    profile.write_text('\n'.join(lines) + '\n')

    outdir = run_spider(
        overrides=('-nstepsmacro', '1', '-HTIDAL', '2', '-htidal_filename', str(profile)),
        name='htidal_file',
    )
    ht = data_si(read_output(outdir, 0), 'Htidal_s')  # W/kg

    # rel=1e-10: the file values are read by node index with unit
    # scalings, so recovery is exact to I/O rounding.
    np.testing.assert_allclose(ht, ramp, rtol=1e-10)
    # Orientation guard: a reversed node indexing would flip the ramp;
    # the endpoints differ by a factor of five.
    assert ht[0] == pytest.approx(1.0e-8, rel=1e-10)
    assert ht[-1] == pytest.approx(5.0e-8, rel=1e-10)
    assert np.all(np.diff(ht) > 0)

    # Error contract: the reader checks the header's row count against
    # the staggered mesh and refuses a profile of the wrong length.
    short_lines = [f'# 5 {5}'] + lines[1:5]
    short_lines += [f'{pressure_s[0]:.18e} 1.0e-8'] * 5
    short = tmp_path / 'htidal_short.dat'
    short.write_text('\n'.join(short_lines) + '\n')
    with pytest.raises(RuntimeError):
        run_spider(
            overrides=('-nstepsmacro', '1', '-HTIDAL', '2', '-htidal_filename', str(short)),
            name='htidal_short',
        )


@pytest.fixture(scope='module')
def steady_state_run(cached_spider_run):
    """One-step blackbody50 run with the steady-state initial condition."""
    return cached_spider_run(
        overrides=('-nstepsmacro', '1', '-dtmacro', '10', '-ic_steady_state_energy'),
        name='steady_ic',
    )


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_steady_state_ic_balances_interior_and_surface(steady_state_run):
    """The steady-state IC equalises the energy flow through the mantle.

    Anchor: analytical limit. With -ic_steady_state_energy the surface
    radiation balance is solved together with a steady interior, so at
    t = 0 the energy flow Etot is the same through every basic node
    (observed relative spread 2e-11) and the surface flux satisfies the
    grey-body law sigma * (T_surf^4 - teqm^4) with emissivity 1.
    """
    doc = read_output(steady_state_run, 0)
    etot = data_si(doc, 'Etot_b')  # W
    fatm = atmosphere_si(doc, 'Fatm')  # W/m^2
    t_surf = atmosphere_si(doc, 'temperature_surface')  # K

    # Steady state: constant energy flow through the interior. The
    # 1e-8 bound sits three orders above the observed 2e-11 spread yet
    # far below the order-one spread of the default (non-steady) IC.
    assert (etot.max() - etot.min()) / abs(etot.mean()) < 1e-8
    assert np.all(etot > 0)

    # Grey-body pin with the sigma hard-coded in constants.c.
    sigma = 5.670367e-8  # W m^-2 K^-4
    expected = sigma * (t_surf**4 - 273.0**4)
    # rel=1e-5: the radiation balance is solved to snes_rtol 1e-9; the
    # margin absorbs output rounding of T_surf.
    assert fatm == pytest.approx(expected, rel=1e-5)
    # Exponent guard: a T^3 slip at ~1960 K misses by a factor of ~300.
    assert abs(fatm - sigma * (t_surf**3 - 273.0**3)) > 0.5 * fatm
    # Sign and scale guards.
    assert fatm > 0
    assert 1e2 < fatm < 1e9  # W/m^2
