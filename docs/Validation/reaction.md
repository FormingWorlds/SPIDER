# reaction.c: Interior chemical reactions

**Source under test**: `reaction.c`

**Reference-pinned test**: `tests/test_reaction.py::test_elements_conserved_across_each_reaction_pair`

**Anchor**: Analytical conservation: closed-system elemental budgets across the H2O/H2 and CO2/CO reaction pairs of the Bower et al. (2021) three-ocean hydrogen configuration.

**Tolerance**: rel 1e-3 on the hydrogen and carbon transfer balances after one 1000-year step (observed residuals near 5e-5).

**Discrimination guards**: Sign structure of the transfers (H2O produced from H2, CO2 from CO in this step); per-volatile reservoir closure to rel 1e-10 and inventory closure to rel 1e-5; transfer magnitudes bounded against the total inventory.

The reaction module exchanges mass between volatile pairs subject to elemental conservation. The reaction_kg bookkeeping is pinned so that the element handed off by one partner reappears exactly in the stoichiometric fraction of the other.
