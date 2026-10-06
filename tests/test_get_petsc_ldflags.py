"""Tests for the macOS linker flags in ``tools/get_petsc.sh``."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'get_petsc.sh'


def test_macos_ldflags_add_no_homebrew_library_path():
    """The macOS LDFLAGS only silence linker warnings and add no library path, so a Homebrew
    SUNDIALS 7 cannot shadow the SUNDIALS 2.5 PETSc downloads (configure then misses
    CVDense); mpicc already carries the MPI library path."""
    text = SCRIPT.read_text()
    assignments = re.findall(r'^\s*ldflags=(.*)$', text, re.M)
    assert assignments == ['""', '"-Wl,-w"']
    assert 'brew --prefix' not in text
    assert '-L' not in ''.join(assignments)
