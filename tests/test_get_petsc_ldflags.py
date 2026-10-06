"""Tests for the macOS linker flags in ``tools/get_petsc.sh``."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'get_petsc.sh'


def test_the_petsc_build_passes_no_library_path():
    """No code line of get_petsc.sh passes a -L to the build, so no library directory can come
    ahead of the SUNDIALS 2.5 that PETSc downloads; -Wl,-w stays."""
    code = [re.sub(r'(^|\s)#.*$', '', line).strip() for line in SCRIPT.read_text().splitlines()]
    assert [line for line in code if re.search(r'(^|[\s"=\'])-L[/$"\']', line)] == []
    assert 'ldflags="-Wl,-w"' in code
