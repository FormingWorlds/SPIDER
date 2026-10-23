# SPIDER short instructions

The full instructions are in `AGENTS.md` (repository rules and review points) and `tests/AGENTS.md` (test rules). This file repeats what a review or a chat needs when it cannot read them.

## Commands

```bash
make -j && make -j tests_c          # needs PETSC_DIR and PETSC_ARCH
pytest -m "(unit or smoke) and not skip"
ruff check --fix <changed .py files> && ruff format <changed .py files>
bash tools/validate_test_structure.sh
python tools/check_test_quality.py --check
python tools/generate_options_reference.py --check
python tools/agents/check_agents_md.py
```

## Review checklist

- Temperature, pressure, entropy, viscosity, density and heat capacity stay positive; pressure increases with depth; the melt fraction stays in [0, 1]; the liquidus lies above the solidus; `mass_liquid + mass_solid = mass_mantle`.
- The nondimensional scaling is applied once on input and inverted once on output; a new JSON field is a `DimensionalisableField` with `scaling` and `units`; `-gravity` is negative.
- Every PETSc call has its return code checked and every create its destroy; the code stays serial; a change of stiffness gets a smoke test on the step count or final time.
- PROTEUS (`src/proteus/interior_energetics/spider.py`) reads the JSON fields listed in `AGENTS.md`, restarts from the binary's own output, passes `-coresize`, `-rho_core`, `-cp_core`, uses `-SURFACE_BC 4` and `1`, and may pass an external mesh; a change to any of these comes with the PROTEUS change.
- Tests: `<file>.c` is tested in `tests/test_<file>.py`; each file has `pytestmark = [pytest.mark.<tier>, pytest.mark.timeout(<s>)]`; assertions on JSON use SI values (`values * scaling`); each test has a docstring, at least 2 assertions, an edge case and the error path; pinned values have sign, scale and wrong-formula guards.
- Commit messages, pull-request text, comments, test names and CI job names describe the change: no tool attribution, no internal plan labels, no em or en dashes; an inline comment block has at most 4 lines.

This checklist is a subset of the review points of `AGENTS.md` (its Review section and its physics and coupling contract) and `tests/AGENTS.md`; change them together.
