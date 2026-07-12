"""Tests for poststep.c (post-step event checks and rollback).

Driven through short blackbody50 runs of the spider binary with the
post-step machinery active. Contract clauses exercised: a surface
temperature drop beyond tsurf_poststep_change rolls the offending step
back and stops the run early with the rolled-back state as the final
output, and activating the post-step check without rollback support is
refused. See docs/How-to/build_tests.md for the tier system.
"""

from __future__ import annotations

import pytest

from tests._json_utils import atmosphere_si, read_output

pytestmark = [pytest.mark.smoke, pytest.mark.timeout(120)]

# blackbody50 cools by hundreds of kelvin in the first 100-year macro
# step, so a 1 K ceiling guarantees the event fires on step one.
TSURF_CEILING = 1.0  # K
NOMINAL_STEPS = 6
NOMINAL_END = 600  # years, 6 steps of the default 100-year dtmacro


@pytest.fixture(scope='module')
def rollback_run(cached_spider_run):
    """Six-step run whose first step exceeds the tsurf-change ceiling."""
    return cached_spider_run(
        overrides=(
            '-nstepsmacro', str(NOMINAL_STEPS),
            '-activate_poststep',
            '-activate_rollback',
            '-tsurf_poststep_change', str(TSURF_CEILING),
        ),
        name='rollback_event',
    )


def test_tsurf_event_rolls_back_and_stops_early(rollback_run):
    """A tsurf drop beyond the ceiling ends the run at the rolled-back state.

    The run must terminate before its nominal six macro steps: the
    output directory holds the initial condition plus exactly one
    further state, written at the rolled-back time inside the first
    macro step, and the surface cooling across that window exceeds the
    1 K ceiling that triggered the event.
    """
    outputs = sorted(
        int(p.stem) for p in rollback_run.glob('*.json') if p.stem.isdigit()
    )

    # Early stop: the initial condition plus the rolled-back state.
    assert len(outputs) == 2
    assert outputs[0] == 0
    # The final output falls inside the first nominal macro step, far
    # short of the 600-year end of an uninterrupted run.
    assert 0 < outputs[-1] < NOMINAL_END
    assert outputs[-1] < 100  # years, within macro step one

    # Rollback semantics: the offending step is discarded, so the
    # written final state is from BEFORE the ceiling was crossed. The
    # cooling across the written window is therefore nonzero but
    # bounded by the ceiling (observed 0.99 K against the 1 K limit);
    # a run that wrote the over-limit state would exceed it by
    # hundreds of kelvin.
    t_start = atmosphere_si(read_output(rollback_run, 0), 'temperature_surface')
    t_end = atmosphere_si(read_output(rollback_run, outputs[-1]), 'temperature_surface')
    drop = t_start - t_end  # K
    assert 0 < drop <= TSURF_CEILING
    # The integrator ran close to the ceiling before the event fired.
    assert drop > 0.1 * TSURF_CEILING
    # Positivity: the rolled-back state is still physical.
    assert t_end > 0  # K


def test_poststep_without_rollback_is_refused(run_spider):
    """The post-step check requires rollback support and errors without it.

    poststep.c raises a hard error when the first post-step evaluation
    finds rollback inactive, so the run must exit nonzero rather than
    silently continue without the safety net.
    """
    with pytest.raises(RuntimeError) as excinfo:
        run_spider(
            overrides=(
                '-nstepsmacro', '2',
                '-activate_poststep',
                '-tsurf_poststep_change', str(TSURF_CEILING),
            ),
            name='poststep_no_rollback',
        )
    message = str(excinfo.value)
    # The documented refusal fired, not an arbitrary crash: the PETSc
    # error text names the missing option. (The exit code itself
    # differs by platform, so the message is the stable contract.)
    assert 'You must run with -activate_rollback' in message
    assert 'spider exited with code' in message
