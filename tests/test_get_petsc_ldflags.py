"""Tests for the macOS configure arguments of ``tools/get_petsc.sh``.

The platform and configure steps are read from the shipped script and run with stub tools
and a stub ``configure``: no build and no network.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'get_petsc.sh'


# A stub configure: records its arguments, its environment and four named variables.
CONFIGURE_STUB = """#!/bin/bash
printf "%s\\n" "$@" > args
export -p > env
for v in LDFLAGS LIBRARY_PATH LIBS CPATH; do printf "%s=%s\\n" "$v" "${!v-unset}"; done > named
"""


def _run_macos(tmp_path, tools, path_extra=':/usr/bin:/bin'):
    """Run the shipped platform and configure steps as macOS with stub ``tools``."""
    text = SCRIPT.read_text()
    start = text.index('current_step="Determining platform-specific flags"')
    block = text[start : text.index('# 9. Build PETSc')]
    for name in tools:
        (tmp_path / name).write_text('#!/bin/bash\necho /sdk\n')
    (tmp_path / 'configure').write_text(CONFIGURE_STUB)
    for stub in tmp_path.iterdir():
        stub.chmod(0o755)
    snippet = 'set -euo pipefail\nannounce() { :; }\nOSTYPE=darwin24\nworkpath=.\n' + block
    return subprocess.run(
        ['/bin/bash', '-c', snippet],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env={'PATH': f'{tmp_path}{path_extra}'},
    )


def _configure_args(tmp_path) -> list[str]:
    """Return the configure arguments, after checking no build variable names a library path."""
    named = (tmp_path / 'named').read_text().split()
    assert named == [f'{v}=unset' for v in ('LDFLAGS', 'LIBRARY_PATH', 'LIBS', 'CPATH')]
    assert 'homebrew/lib' not in (tmp_path / 'env').read_text()
    args = (tmp_path / 'args').read_text().splitlines()
    assert [a for a in args if '-L' in a] == []
    return args


def test_configure_on_macos_gets_no_library_path(tmp_path):
    """On macOS with a system MPI, PETSc configure gets LDFLAGS=-Wl,-w and no -L in any
    argument or build variable, so no library directory comes ahead of the SUNDIALS 2.5 it
    downloads."""
    result = _run_macos(tmp_path, ('xcrun', 'mpicc', 'mpirun'))
    assert result.returncode == 0, result.stderr
    args = _configure_args(tmp_path)
    assert {'LDFLAGS=-Wl,-w', '--download-sundials2'} <= set(args)
    assert '--download-mpich' not in args


def test_configure_on_macos_without_mpicc_downloads_mpich(tmp_path):
    """Without mpicc on PATH, PETSc downloads MPICH and still gets only LDFLAGS=-Wl,-w."""
    result = _run_macos(tmp_path, ('xcrun',), path_extra='')
    assert result.returncode == 0, result.stderr
    args = _configure_args(tmp_path)
    assert {'LDFLAGS=-Wl,-w', '--download-sundials2', '--download-mpich'} <= set(args)


def test_macos_without_xcrun_stops_before_configure(tmp_path):
    """Without xcrun the script stops with its install hint and never runs configure."""
    result = _run_macos(tmp_path, ('mpicc', 'mpirun'), path_extra='')
    assert result.returncode == 1
    assert 'xcrun not found' in result.stderr and 'xcode-select --install' in result.stderr
    assert not (tmp_path / 'args').exists()
