"""Tests for py/plot_spider_lite.py.

Exercises the standalone plotting utility end-to-end on real run output:
figure generation for multiple and single output times, and the failure
contract for a missing output directory. See docs/How-to/build_tests.md
for the tier system.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip('matplotlib')

pytestmark = [pytest.mark.smoke, pytest.mark.timeout(120)]

REPO_ROOT = Path(__file__).resolve().parent.parent
PLOT_SCRIPT = REPO_ROOT / 'py' / 'plot_spider_lite.py'


def _run_plot(cwd: Path, args: tuple) -> subprocess.CompletedProcess:
    """Run the plotting script headless in ``cwd``."""
    env = dict(os.environ, MPLBACKEND='Agg')
    return subprocess.run(
        [sys.executable, str(PLOT_SCRIPT), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


def test_interior_figure_written_for_selected_times(blackbody_short, tmp_path):
    """The four-panel interior figure lands in plots/interior.pdf.

    Selecting all three output times of the short run exercises the
    multi-profile legend path.
    """
    proc = _run_plot(tmp_path, ('-d', str(blackbody_short), '-t', '0,100,200'))
    assert proc.returncode == 0, proc.stderr
    figure = tmp_path / 'plots' / 'interior.pdf'
    assert figure.is_file()
    # A real four-panel vector figure is tens of kB; a blank canvas is not.
    assert figure.stat().st_size > 5000
    assert figure.read_bytes()[:5] == b'%PDF-'


def test_single_time_selection_also_plots_the_last_output(blackbody_short, tmp_path):
    """Selecting one time still produces a valid figure.

    The time-selection code always appends the final output, so the
    single-time edge case exercises the deduplication of that append.
    """
    proc = _run_plot(tmp_path, ('-d', str(blackbody_short), '-t', '0'))
    assert proc.returncode == 0, proc.stderr
    figure = tmp_path / 'plots' / 'interior.pdf'
    assert figure.is_file()
    assert figure.read_bytes()[:5] == b'%PDF-'


def test_missing_output_directory_fails_loudly(tmp_path):
    """A nonexistent run directory is a hard error, not an empty figure."""
    proc = _run_plot(tmp_path, ('-d', str(tmp_path / 'does_not_exist')))
    assert proc.returncode != 0
    # No figure may be produced on the failure path.
    assert not (tmp_path / 'plots' / 'interior.pdf').exists()
