"""Tests for ic.c (initial condition of the entropy profile).

Driven through cached blackbody50 runs of the spider binary, including
a zero-macro-step run that emits only the initial condition (the
limit-input configuration). Invariants exercised: the prescribed
adiabat entropy is recovered exactly at the top staggered node, the
initial profile is flat up to the small prescribed ic_dsdr gradient,
entropy positivity, discrimination between different ic_adiabat_entropy
values, and the loss of initial flatness once grey-body cooling has
acted. See docs/How-to/build_tests.md for the tier system.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests._json_utils import data_si, field_si, read_output, solution_entries

pytestmark = [pytest.mark.smoke, pytest.mark.timeout(120)]

# blackbody50 geometry: radius 6371000 m, coresize 0.55, so the mantle
# shell spans 6371000 * 0.45 m from surface to core-mantle boundary.
MANTLE_DEPTH = 2866950.0  # m
IC_ENTROPY = 2600.0  # J/kg/K, blackbody50 ic_adiabat_entropy
IC_DSDR = -1.0e-5  # J/kg/K/m, blackbody50 ic_dsdr


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_prescribed_adiabat_entropy_sets_the_initial_profile(
    blackbody_short, cached_spider_run
):
    """The IC recovers ic_adiabat_entropy at the top staggered node.

    Anchor: analytical limit. The initial condition prescribes
    S = ic_adiabat_entropy (2600 J/kg/K in blackbody50) at the top
    staggered node and integrates the small ic_dsdr gradient inward, so
    the top node carries the option value exactly and the profile mean
    sits slightly above it (the gradient raises entropy with depth).
    """
    doc = read_output(blackbody_short, 0)
    s_s = data_si(doc, 'S_s')  # J/kg/K, surface first
    entries = {e['description']: e for e in solution_entries(doc)}
    top = entries['S at top staggered node']
    s_top = float(top['values'][0]) * float(top['scaling'])  # J/kg/K

    # rel=1e-3 (2.6 J/kg/K) is generous against the observed exact
    # recovery but still rejects any competing entropy value by far.
    assert s_top == pytest.approx(IC_ENTROPY, rel=1e-3)
    assert s_s[0] == pytest.approx(IC_ENTROPY, rel=1e-3)
    # The ic_dsdr ramp bounds the mean from above: the mean must lie
    # between the top value and top + |ic_dsdr| * mantle depth
    # (2600 to 2628.7 J/kg/K; observed offset ~14.7 J/kg/K).
    assert IC_ENTROPY < s_s.mean() < IC_ENTROPY + abs(IC_DSDR) * MANTLE_DEPTH

    # Wrong-value discrimination: rerunning the IC with
    # -ic_adiabat_entropy 2400 shifts every staggered node by exactly
    # the 200 J/kg/K offset (the ramp term is identical), far beyond
    # the 2.6 J/kg/K pin tolerance.
    outdir = cached_spider_run(
        overrides=('-nstepsmacro', '0', '-ic_adiabat_entropy', '2400.0'), name='ic_2400'
    )
    s_24 = data_si(read_output(outdir, 0), 'S_s')
    assert s_24.mean() == pytest.approx(s_s.mean() - 200.0, rel=1e-9)
    assert abs(s_s.mean() - s_24.mean()) > 10 * (1e-3 * IC_ENTROPY)
    # Sign and scale guards: silicate specific entropies sit at a few
    # thousand J/kg/K; a nondimensional leak would sit near unity.
    assert np.all(s_s > 0)
    assert 1e3 < s_s.mean() < 1e4


@pytest.mark.physics_invariant
def test_initial_adiabat_is_nearly_flat_until_cooling_imprints_structure(blackbody_short):
    """The IC profile is flat up to the ic_dsdr ramp; cooling breaks it.

    The only structure the initial condition imprints is the prescribed
    ic_dsdr gradient, so the profile spread is bounded by
    |ic_dsdr| * mantle depth (28.7 J/kg/K, about 1.1 percent of the
    mean). After 200 years of grey-body cooling the top staggered node
    (the node exposed to the surface boundary) has lost entropy, so the
    near-flatness of the t = 0 edge state does not persist.
    """
    doc_0 = read_output(blackbody_short, 0)
    s_0 = data_si(doc_0, 'S_s')  # J/kg/K, surface first

    # Spread bounded by the prescribed gradient across the mantle:
    # 1e-5 J/kg/K/m * 2866950 m = 28.7 J/kg/K (observed 28.1).
    spread = s_0.max() - s_0.min()
    assert spread < abs(IC_DSDR) * MANTLE_DEPTH
    # The relative spread stays around one percent of the mean.
    assert spread / s_0.mean() < 0.02
    assert np.all(s_0 > 0)

    # Cooling imprint: the top staggered node has lost entropy by 200
    # years, and the drop (~160 J/kg/K observed) is resolved far above
    # the CVODE tolerance floor, so the inequality is strict by margin.
    s_200 = data_si(read_output(blackbody_short, 200), 'S_s')
    assert s_200[0] < s_0[0]
    assert s_0[0] - s_200[0] > 10.0  # J/kg/K


# Molar masses (kg/mol) of the reaction.opts volatiles, matching the
# per-volatile molar_mass options in the configuration.
MOLAR_MASS = {
    'H2O': 0.01801528,
    'H2': 0.00201588,
    'CO2': 0.04401,
    'CO': 0.02801,
}
# Elemental composition (atoms per molecule) for the mole bookkeeping.
STOICHIOMETRY = {
    'H2O': {'H': 2, 'O': 1},
    'H2': {'H': 2},
    'CO2': {'C': 1, 'O': 2},
    'CO': {'C': 1, 'O': 1},
}
# Requested inventories (ppm by mass of the mantle) for the abundance IC.
# The values sit 20 to 40 percent off the three-ocean equilibrium implied
# by the configured guess pressures (984, 0.45, 5.0, 22.6 ppm), so the
# Newton solve stays within its convergence basin on every platform while
# the reactions still have to redistribute a resolvable amount of mass.
ABUNDANCE_PPM = {'H2O': 800.0, 'H2': 0.6, 'CO2': 7.0, 'CO': 18.0}
# Requested inventories (Earth oceans) for the ocean-moles IC, matched to
# the abundance targets above; the mole count of one ocean is the
# OCEAN_MOLES constant in constants.c.
OCEAN_MOLES = 7.68894973907177e22  # mol per Earth ocean of H2O (or H2)
MOLES_OCEANS = {'H2O': 2.43, 'H2': 0.0163, 'CO2': 0.0087, 'CO': 0.0352}


def _volatile_reservoirs_kg(doc, volatile):
    """SI masses of the liquid, solid, and atmosphere reservoirs."""
    block = doc['atmosphere'][volatile]
    return {
        key: float(field_si(block[key])[0])
        for key in ('initial_kg', 'liquid_kg', 'solid_kg', 'atmosphere_kg', 'physical_kg')
    }


def _element_moles(masses_kg, element):
    """Total moles of one element across the four volatile inventories."""
    return sum(
        masses_kg[v] / MOLAR_MASS[v] * STOICHIOMETRY[v].get(element, 0)
        for v in MOLAR_MASS
    )


@pytest.fixture(scope='module')
def abundance_ic_run(cached_spider_run):
    """Zero-step reaction run with the abundance-based atmosphere IC.

    IC_ATMOSPHERE 1 solves the initial partial pressures and reaction
    masses from the per-volatile total abundances, subject to the
    water and carbon dioxide equilibrium constraints. Zero macro steps:
    the tests read only the initial condition, so the run skips time
    integration entirely.
    """
    return cached_spider_run(
        opts_file='reaction.opts',
        overrides=(
            '-IC_ATMOSPHERE', '1',
            '-nstepsmacro', '0',
            '-n', '50',
            '-H2O_initial_total_abundance', '800.0',
            '-H2_initial_total_abundance', '0.6',
            '-CO2_initial_total_abundance', '7.0',
            '-CO_initial_total_abundance', '18.0',
        ),
        name='ic_abundance',
    )


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_abundance_ic_realises_the_requested_inventory(abundance_ic_run):
    """The abundance IC conserves the requested elemental inventories.

    Anchor: mass-balance identity through the initial-pressure solve.
    Each volatile's initial_kg must equal the requested ppm of the
    mantle mass exactly, and because the water and carbon dioxide
    reactions conserve hydrogen and carbon, the realised reservoirs
    carry the same H and C mole totals as the request. Oxygen is NOT
    conserved among the volatiles: the reactions exchange it with the
    melt's oxygen-fugacity buffer (observed 2e-3 relative for these
    targets), which discriminates an inert fO2 pathway.
    """
    doc = read_output(abundance_ic_run, 0)
    mantle_kg = float(field_si(doc['atmosphere']['mass_mantle'])[0])

    requested = {}
    realised = {}
    for volatile, ppm in ABUNDANCE_PPM.items():
        res = _volatile_reservoirs_kg(doc, volatile)
        requested[volatile] = ppm * 1e-6 * mantle_kg
        realised[volatile] = res['liquid_kg'] + res['solid_kg'] + res['atmosphere_kg']
        # rel=1e-9: initial_kg is the requested abundance times the
        # mantle mass, stored rather than solved.
        assert res['initial_kg'] == pytest.approx(requested[volatile], rel=1e-9)
        # physical_kg is defined as the reservoir sum.
        assert res['physical_kg'] == pytest.approx(realised[volatile], rel=1e-10)

    # Elemental conservation through the equilibrium solve: H and C
    # totals match the request (observed to 3e-15 relative; rel=1e-9
    # leaves platform headroom). This is the discriminating check that
    # the solve redistributed mass without creating or destroying it.
    for element in ('H', 'C'):
        assert _element_moles(realised, element) == pytest.approx(
            _element_moles(requested, element), rel=1e-9
        )

    # Oxygen exchange: the realised volatile O inventory departs from
    # the requested one (observed 2.2e-3 relative; the threshold sits
    # twentyfold below) because the fO2 buffer participates in both
    # reactions. An inert fO2 pathway would conserve O to the same
    # 1e-9 the H and C totals meet.
    o_req = _element_moles(requested, 'O')
    o_real = _element_moles(realised, 'O')
    assert abs(o_real - o_req) > 1e-4 * o_req

    # Edge case: the reactions moved water mass at the IC (observed
    # 3.6e-3 relative), so the realised H2O reservoirs sit resolvably
    # off the bare request.
    assert abs(realised['H2O'] - requested['H2O']) > 1e-4 * requested['H2O']


@pytest.fixture(scope='module')
def ocean_moles_ic_run(cached_spider_run):
    """Zero-step reaction run with the ocean-moles atmosphere IC.

    The mole counts are chosen so the implied abundances match the
    abundance-IC configuration, keeping the equilibrium solve within
    its convergence basin. Zero macro steps: the tests read only the
    initial condition.
    """
    return cached_spider_run(
        opts_file='reaction.opts',
        overrides=(
            '-IC_ATMOSPHERE', '4',
            '-nstepsmacro', '0',
            '-n', '50',
            '-H2O_initial_ocean_moles', '2.43',
            '-H2_initial_ocean_moles', '0.0163',
            '-CO2_initial_ocean_moles', '0.0087',
            '-CO_initial_ocean_moles', '0.0352',
        ),
        name='ic_ocean_moles',
    )


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_ocean_moles_ic_converts_moles_to_mass(ocean_moles_ic_run):
    """IC_ATMOSPHERE 4 converts Earth-ocean mole counts to inventory mass.

    Anchor: the OCEAN_MOLES constant in constants.c (7.68894974e22 mol
    per Earth ocean). Each volatile's initial_kg must equal
    moles * OCEAN_MOLES * molar_mass, so the pin verifies both the
    constant and the per-volatile molar mass wiring.
    """
    doc = read_output(ocean_moles_ic_run, 0)

    for volatile, oceans in MOLES_OCEANS.items():
        res = _volatile_reservoirs_kg(doc, volatile)
        expected = oceans * OCEAN_MOLES * MOLAR_MASS[volatile]  # kg
        # rel=1e-9: a closed-form product of three stored constants.
        assert res['initial_kg'] == pytest.approx(expected, rel=1e-9)

    # Molar-mass discrimination: reading the CO2 inventory with the CO
    # molar mass shifts the expected mass by the mass ratio (36%), far
    # beyond the pin tolerance.
    co2 = _volatile_reservoirs_kg(doc, 'CO2')
    wrong = MOLES_OCEANS['CO2'] * OCEAN_MOLES * MOLAR_MASS['CO']
    assert abs(co2['initial_kg'] - wrong) > 0.3 * co2['initial_kg']

    # Edge case: the smallest inventory (CO2, 0.0087 oceans) still
    # produces a positive, finite mass at the expected scale.
    assert 0 < co2['initial_kg'] < 1e21  # kg
    assert np.isfinite(co2['initial_kg'])
