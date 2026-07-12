"""Tests for reaction.c (interior chemical reactions between volatiles).

Runs the shipped reaction configuration (a case from Bower et al. 2021:
three Earth oceans of hydrogen with C/H = 0.1 wt%, H2O/H2 and CO2/CO
reaction pairs, coupled atmosphere) for one macro step. Invariants
exercised: per-volatile reservoir closure, reaction-transfer accounting
against the initial inventory, elemental conservation across each
reaction pair, and reservoir positivity. See
docs/How-to/build_tests.md for the tier system.
"""

from __future__ import annotations

import pytest

from tests._json_utils import field_si, read_output

pytestmark = [pytest.mark.smoke, pytest.mark.timeout(120)]

VOLATILES = ('H2O', 'H2', 'CO2', 'CO')

# Atomic and molecular masses (g/mol) for elemental bookkeeping.
M_H2 = 2.01588
M_H2O = 18.01528
M_C = 12.011
M_CO2 = 44.01
M_CO = 28.01


@pytest.fixture(scope='module')
def reaction_run(cached_spider_run):
    """One macro step of the Bower et al. (2021) reaction configuration.

    A single 1000-year step keeps the smoke budget while exercising the
    full reaction, outgassing, and atmosphere coupling.
    """
    return cached_spider_run(
        opts_file='reaction.opts',
        overrides=('-nstepsmacro', '1'),
        name='reaction_short',
    )


def _reservoirs(doc, volatile):
    """SI reservoir masses (kg) for one volatile."""
    block = doc['atmosphere'][volatile]
    return {
        key: float(field_si(block[key])[0])
        for key in (
            'initial_kg',
            'liquid_kg',
            'solid_kg',
            'atmosphere_kg',
            'reaction_kg',
            'physical_kg',
        )
    }


@pytest.mark.physics_invariant
def test_reservoir_closure_for_every_volatile(reaction_run):
    """physical_kg is the sum of the melt, solid, and atmosphere reservoirs.

    The closure must hold at the initial condition and after the first
    macro step. The fully molten mantle is the limit input where the
    solid reservoir vanishes identically.
    """
    for time in (0, 1000):
        doc = read_output(reaction_run, time)
        for volatile in VOLATILES:
            r = _reservoirs(doc, volatile)
            total = r['liquid_kg'] + r['solid_kg'] + r['atmosphere_kg']
            assert r['physical_kg'] == pytest.approx(total, rel=1e-10), (
                f'{volatile} at t = {time}'
            )
            assert all(r[k] >= 0.0 for k in ('liquid_kg', 'solid_kg', 'atmosphere_kg'))
            # Fully molten mantle: nothing is frozen into a solid yet.
            assert r['solid_kg'] == pytest.approx(0.0, abs=1e6)


@pytest.mark.physics_invariant
def test_reaction_transfer_balances_the_initial_inventory(reaction_run):
    """initial_kg equals physical_kg plus the reaction transfer.

    reaction_kg books the mass a volatile has handed to (positive) or
    received from (negative) its reaction partners; the identity closes
    the per-volatile budget. At t = 0 no reactions have run yet, so the
    transfer is identically zero (edge case).
    """
    doc0 = read_output(reaction_run, 0)
    for volatile in VOLATILES:
        r = _reservoirs(doc0, volatile)
        assert r['reaction_kg'] == pytest.approx(0.0, abs=1e3)
        assert r['physical_kg'] == pytest.approx(r['initial_kg'], rel=1e-10)

    doc1 = read_output(reaction_run, 1000)
    for volatile in VOLATILES:
        r = _reservoirs(doc1, volatile)
        # rel 1e-5: the budget closes to the tolerance of the coupled
        # volatile solve (observed residual 1.4e-6 on CO2 after one
        # 1000-year step).
        assert r['initial_kg'] == pytest.approx(
            r['physical_kg'] + r['reaction_kg'], rel=1e-5
        ), volatile
    # The step must have actually reacted something, otherwise the
    # closure above is trivially the t = 0 identity.
    r_h2 = _reservoirs(doc1, 'H2')
    assert abs(r_h2['reaction_kg']) > 1e15


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_elements_conserved_across_each_reaction_pair(reaction_run):
    """Hydrogen and carbon move between partners without loss.

    Analytical anchor: closed-system elemental conservation for the
    H2O/H2 and CO2/CO reaction pairs of the Bower et al. (2021) setup.
    The hydrogen handed off by H2 (its reaction_kg is pure hydrogen)
    must reappear in the hydrogen fraction of the H2O gained, and the
    carbon lost by CO2 must reappear in CO.
    """
    doc = read_output(reaction_run, 1000)
    h2o = _reservoirs(doc, 'H2O')
    h2 = _reservoirs(doc, 'H2')
    co2 = _reservoirs(doc, 'CO2')
    co = _reservoirs(doc, 'CO')

    # Hydrogen balance: H2 lost (positive reaction_kg, all hydrogen)
    # equals the hydrogen content of the H2O gained (negative
    # reaction_kg). rel 1e-3 absorbs the coupled-solver tolerance.
    h_from_h2o = -h2o['reaction_kg'] * (M_H2 / M_H2O)
    assert h2['reaction_kg'] == pytest.approx(h_from_h2o, rel=1e-3)
    # Sign structure: in this reducing step H2O is produced and H2
    # consumed; a sign error in either transfer flips the comparison.
    assert h2o['reaction_kg'] < 0.0 < h2['reaction_kg']

    # Carbon balance for the CO2/CO pair: the carbon handed off by CO
    # (positive reaction_kg) reappears in the carbon fraction of the
    # CO2 gained (negative reaction_kg).
    c_gained_by_co2 = -co2['reaction_kg'] * (M_C / M_CO2)
    c_lost_by_co = co['reaction_kg'] * (M_C / M_CO)
    assert c_lost_by_co == pytest.approx(c_gained_by_co2, rel=1e-3)
    assert co2['reaction_kg'] < 0.0 < co['reaction_kg']

    # Scale guard: the transfers after 1000 years are large in absolute
    # terms (1e17 to 1e18 kg) yet small against the 4e21 kg water
    # inventory; both bounds discriminate unit slips.
    assert 1e16 < abs(h2o['reaction_kg']) < 1e20
    assert abs(h2o['reaction_kg']) < 0.01 * h2o['initial_kg']


# The full named-reaction library configuration: seven volatiles and
# the IVTANTHERMO water, IVTANTHERMO carbon dioxide, IVTANTHERMO
# methane, and ammonia reactions (tests/opts/reaction_library.opts).
LIBRARY_VOLATILES = ('H2O', 'H2', 'CO2', 'CO', 'CH4', 'NH3', 'N2')
LIBRARY_MOLAR_MASS = {
    'H2O': 0.01801528,
    'H2': 0.00201588,
    'CO2': 0.04401,
    'CO': 0.02801,
    'CH4': 0.01604,
    'NH3': 0.017031,
    'N2': 0.028014,
}
LIBRARY_STOICHIOMETRY = {
    'H2O': {'H': 2, 'O': 1},
    'H2': {'H': 2},
    'CO2': {'C': 1, 'O': 2},
    'CO': {'C': 1, 'O': 1},
    'CH4': {'C': 1, 'H': 4},
    'NH3': {'N': 1, 'H': 3},
    'N2': {'N': 2},
}


@pytest.fixture(scope='module')
def library_run(cached_spider_run):
    """One macro step of the full named-reaction library configuration."""
    return cached_spider_run(
        opts_file='reaction_library.opts',
        overrides=('-nstepsmacro', '1', '-n', '50'),
        name='reaction_library',
    )


def _library_element_moles(doc, element):
    """Moles of one element summed over all seven volatile inventories."""
    total = 0.0
    for volatile in LIBRARY_VOLATILES:
        block = doc['atmosphere'][volatile]
        kg = sum(
            float(field_si(block[key])[0])
            for key in ('liquid_kg', 'solid_kg', 'atmosphere_kg')
        )
        moles = kg / LIBRARY_MOLAR_MASS[volatile]
        total += moles * LIBRARY_STOICHIOMETRY[volatile].get(element, 0)
    return total


@pytest.mark.physics_invariant
def test_reaction_library_conserves_h_c_n(library_run):
    """The four-reaction network conserves hydrogen, carbon, and nitrogen.

    The methane reaction exchanges C and H, the ammonia reaction N and
    H, and the water and carbon dioxide reactions H and C, but none of
    them creates or destroys those elements, so the molar totals over
    all seven volatiles are the same before and after the macro step.
    """
    doc_0 = read_output(library_run, 0)
    doc_1 = read_output(library_run, 1000)

    # rel=1e-5: the coupled volatile solve conserves the totals to its
    # own tolerance (observed drifts at or below 1.5e-6).
    for element in ('H', 'C', 'N'):
        total_0 = _library_element_moles(doc_0, element)
        total_1 = _library_element_moles(doc_1, element)
        assert total_1 == pytest.approx(total_0, rel=1e-5), element
        assert total_0 > 0

    # Equilibrium partitioning discrimination: at these conditions the
    # ammonia reaction pushes nearly all nitrogen into N2, so the
    # realised NH3 share of the N inventory is tiny even though 0.5 ppm
    # of NH3 was requested. An inert ammonia reaction would leave the
    # requested 20 percent molar share in place.
    n2_block = doc_0['atmosphere']['N2']
    n2_kg = sum(
        float(field_si(n2_block[key])[0])
        for key in ('liquid_kg', 'solid_kg', 'atmosphere_kg')
    )
    n_total = _library_element_moles(doc_0, 'N')
    assert 2.0 * n2_kg / LIBRARY_MOLAR_MASS['N2'] > 0.99 * n_total

    # Edge case: the trace species (NH3) still carries a positive,
    # finite inventory through the equilibrium.
    nh3_kg = sum(
        float(field_si(doc_0['atmosphere']['NH3'][key])[0])
        for key in ('liquid_kg', 'solid_kg', 'atmosphere_kg')
    )
    assert 0 < nh3_kg < 1e21  # kg


@pytest.mark.physics_invariant
def test_oxygen_flows_through_the_melt_buffer(library_run):
    """Oxygen is exchanged with the melt fO2 buffer, not conserved.

    Every reaction in the library carries an oxygen-fugacity
    stoichiometry, so the volatile O inventory drifts over a step
    (observed 5e-3 relative in 1000 years) while H stays conserved in
    the same window. A conserved O total would mean the fO2 coupling
    is inert, which this test is designed to expose.
    """
    doc_0 = read_output(library_run, 0)
    doc_1 = read_output(library_run, 1000)

    o_0 = _library_element_moles(doc_0, 'O')
    o_1 = _library_element_moles(doc_1, 'O')
    assert o_0 > 0
    # The fO2 exchange must move a resolvable amount of oxygen.
    assert abs(o_1 - o_0) / o_0 > 1e-4

    # Contrast: hydrogen is conserved in the very same step, so the
    # oxygen drift is the fO2 pathway and not a global mass leak.
    h_0 = _library_element_moles(doc_0, 'H')
    h_1 = _library_element_moles(doc_1, 'H')
    assert h_1 == pytest.approx(h_0, rel=1e-5)

    # Positivity to solver tolerance: the coupled volatile solve has no
    # hard positivity clamp, so a trace reservoir can undershoot zero
    # by roundoff (observed -7e9 kg of CH4 against its 4.2e18 kg
    # inventory, i.e. -2e-9 relative). Bound the undershoot at 1e-6 of
    # the species inventory instead of asserting a hard zero.
    for volatile in LIBRARY_VOLATILES:
        block = doc_1['atmosphere'][volatile]
        floor = -1e-6 * float(field_si(block['initial_kg'])[0])
        for key in ('liquid_kg', 'solid_kg', 'atmosphere_kg'):
            assert float(field_si(block[key])[0]) >= floor, (volatile, key)
