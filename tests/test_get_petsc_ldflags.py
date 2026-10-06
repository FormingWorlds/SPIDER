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


def test_configure_on_macos_gets_no_library_path(tmp_path):
    """On macOS with a system MPI, PETSc configure gets LDFLAGS=-Wl,-w and no -L in any
    argument or exported variable, so no library directory comes ahead of the SUNDIALS 2.5
    it downloads."""
    text = SCRIPT.read_text()
    start = text.index('current_step="Determining platform-specific flags"')
    block = text[start : text.index('# 9. Build PETSc')]
    for name in ('xcrun', 'mpicc', 'mpirun'):
        (tmp_path / name).write_text('#!/bin/bash\necho /sdk\n')
    (tmp_path / 'configure').write_text('#!/bin/bash\nprintf "%s\\n" "$@" > args\nenv > env\n')
    for stub in tmp_path.iterdir():
        stub.chmod(0o755)
    snippet = 'set -euo pipefail\nannounce() { :; }\nOSTYPE=darwin24\nworkpath=.\n' + block
    result = subprocess.run(
        ['bash', '-c', snippet],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env={'PATH': f'{tmp_path}:/usr/bin:/bin'},
    )
    assert result.returncode == 0, result.stderr
    args = (tmp_path / 'args').read_text().splitlines()
    assert {'LDFLAGS=-Wl,-w', '--download-sundials2'} <= set(args)
    assert [a for a in args if '-L' in a] == []
    assert [v for v in (tmp_path / 'env').read_text().splitlines() if '-L' in v] == []
    assert '--download-mpich' not in args
