"""Tests for the macOS configure arguments of ``tools/get_petsc.sh``.

The platform and configure steps are read from the shipped script and run with stub tools
and a stub ``configure``: no build and no network.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'get_petsc.sh'


def _stub(directory: Path, name: str, body: str) -> None:
    """Write an executable stub command into ``directory``."""
    path = directory / name
    path.write_text(body)
    path.chmod(0o755)


def test_configure_on_macos_gets_no_library_path(tmp_path):
    """On macOS with a system MPI, PETSc configure gets LDFLAGS=-Wl,-w and no -L in any
    argument, so no library directory comes ahead of the SUNDIALS 2.5 it downloads."""
    text = SCRIPT.read_text()
    helpers = re.search(r'^console\(\) \{.*?^\}\n\nannounce\(\) \{.*?^\}\n', text, re.S | re.M)
    start = text.index('current_step="Determining platform-specific flags"')
    block = text[start : text.index('# 9. Build PETSc')]
    stubs = tmp_path / 'stubs'
    stubs.mkdir()
    _stub(stubs, 'xcrun', '#!/bin/bash\necho /sdk\n')
    for name in ('mpicc', 'mpirun'):
        _stub(stubs, name, '#!/bin/bash\nexit 0\n')
    work = tmp_path / 'petsc'
    work.mkdir()
    _stub(work, 'configure', f'#!/bin/bash\nprintf "%s\\n" "$@" > "{tmp_path}/args"\n')
    snippet = f'exec 3>&1\n{helpers.group(0)}OSTYPE=darwin24\nworkpath="{work}"\n{block}'
    result = subprocess.run(
        ['bash', '-c', snippet],
        capture_output=True,
        text=True,
        env={'PATH': f'{stubs}:/usr/bin:/bin', 'HOME': str(tmp_path)},
    )
    assert result.returncode == 0, result.stderr
    args = (tmp_path / 'args').read_text().splitlines()
    assert 'LDFLAGS=-Wl,-w' in args
    assert [a for a in args if '-L' in a] == []
    assert '--download-mpich' not in args and '--with-cxx=0' in args
