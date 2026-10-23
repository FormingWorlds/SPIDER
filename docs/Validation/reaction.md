# reaction.c: Interior chemical reactions

**Source under test**: `reaction.c`

## Cases

### Elements conserved across each reaction pair

**Reference-pinned test**: `tests/test_reaction.py::test_elements_conserved_across_each_reaction_pair`

**Reference**: Analytical conservation: closed-system elemental budgets across the H2O/H2 and CO2/CO reaction pairs of the Bower et al. (2021) three-ocean hydrogen configuration.

**Tolerance**: rel 1e-3 on the hydrogen and carbon transfer balances after one 1000-year step (observed at round-off level, below 1e-15).

**Command**: `make`, then `pytest -o addopts= tests/test_reaction.py::test_elements_conserved_across_each_reaction_pair`

**Discrimination guards**: Sign structure of the transfers (H2O produced from H2, CO2 from CO in this step); the H2O transfer lies between 1e16 and 1e20 kg and below 1 percent of the H2O inventory. Sibling tests in the same file check the per-volatile reservoir closure to rel 1e-10 (`test_reservoir_closure_for_every_volatile`) and the inventory closure to rel 1e-5 (`test_reaction_transfer_balances_the_initial_inventory`).

The reaction module exchanges mass between volatile pairs subject to elemental conservation. The reaction_kg bookkeeping is pinned so that the element handed off by one partner reappears exactly in the stoichiometric fraction of the other.
