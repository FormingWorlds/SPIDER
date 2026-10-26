# reaction.c: Interior chemical reactions

## What this page checks

This page checks volatile chemical reactions in `reaction.c`, which models volatile speciation.
`reaction.c` calculates chemical equilibrium and volatile transfers between gas pairs.
Validation means that we check elemental conservation in reacting pairs against exact stoichiometric balances.
If reaction bookkeeping is incorrect, volatile elements appear or disappear during mantle degassing.
The text below details the check, its tolerance, and its test command.

## Elements conserved across each reaction pair

**Why this check exists.** Reaction bookkeeping can violate elemental stoichiometry, misapply molar conversions or swap reactant signs; conservation holds for any equilibrium constant, so a wrong equilibrium constant is not caught. A bug in reaction bookkeeping alters total carbon or hydrogen mass during runs.

**What it tests.** The test evaluates closed-system elemental budgets for H2O/H2 and CO2/CO reaction pairs of the Bower et al. (2021) three-ocean hydrogen configuration. It checks hydrogen and carbon transfer balances after one 1000-year step. The test guards reaction signs (H2O produced from H2, CO2 from CO in this step), and bounds H2O transfer between 1e16 and 1e20 kg, below 1 percent of H2O inventory. Sibling tests verify reservoir closure to rel 1e-10 (`test_reservoir_closure_for_every_volatile`), and inventory closure to rel 1e-5 (`test_reaction_transfer_balances_the_initial_inventory`).

**How we know the right answer.** Stoichiometric conservation in closed chemical systems requires identical element mass before and after reaction. Balances match to rel 1e-3 (observed below 1e-15).

**Why it matters.** In a SPIDER run with volatiles, the reaction module sets the volatile chemistry of the magma ocean and its atmosphere. PROTEUS does not use the reaction part of SPIDER.

**Known limit.** The check tests conservation for carbon and hydrogen pairs, but volatile oxygen exchanges with the melt iron buffer.

??? info "Test details"
    - Reference: Analytical conservation: closed-system elemental budgets across the H2O/H2 and CO2/CO reaction pairs of the Bower et al. (2021) three-ocean hydrogen configuration.
    - Tolerance: rel 1e-3 on the hydrogen and carbon transfer balances after one 1000-year step (observed at round-off level, below 1e-15).
    - Test id: `tests/test_reaction.py::test_elements_conserved_across_each_reaction_pair`
    - Command: `make`, then `pytest -o addopts= tests/test_reaction.py::test_elements_conserved_across_each_reaction_pair`
    - Companion test: `tests/test_reaction.py::test_reservoir_closure_for_every_volatile` checks per-volatile mass closure between melt and gas reservoirs.

## Related code

- `reaction.c`: `get_log10_modified_equilibrium_constant`, `get_reaction_quotient_products`, `get_reaction_quotient_reactants`.
- `tests/test_reaction.py`: `test_elements_conserved_across_each_reaction_pair`, `test_reservoir_closure_for_every_volatile`, `test_reaction_transfer_balances_the_initial_inventory`.
