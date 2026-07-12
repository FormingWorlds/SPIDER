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
