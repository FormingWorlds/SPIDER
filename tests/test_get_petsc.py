"""Tests for the verified PETSc download in ``tools/get_petsc.sh``.

The function and the pins are read from the shipped script, so a change to the
script re-runs these cases against its new text. Sources are ``file://`` URLs:
no network and no build.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'get_petsc.sh'


def _function() -> str:
    """Return the shipped fetch_verified definition with the console helpers it calls."""
    text = SCRIPT.read_text()
    helpers = re.search(r'^console\(\) \{.*?^\}\n\nannounce\(\) \{.*?^\}\n', text, re.S | re.M)
    body = re.search(r'^fetch_verified\(\) \{.*?^\}\n', text, re.S | re.M)
    return 'set -euo pipefail\nexec 3>&1\n' + helpers.group(0) + body.group(0)


def _run(body: str) -> subprocess.CompletedProcess:
    """Run ``body`` after the shipped function definitions."""
    return subprocess.run(['bash', '-c', _function() + body], capture_output=True, text=True)


def _sha256(data: bytes) -> str:
    """Return the SHA-256 hex digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def test_the_first_source_with_the_pinned_hash_wins(tmp_path):
    """A failed download, an empty mirror and a wrong file each give way to the next source,
    so only an archive with the pinned SHA-256 reaches unzip and the PETSc build."""
    good, bad = tmp_path / 'good.zip', tmp_path / 'bad.zip'
    good.write_bytes(b'petsc archive')
    bad.write_bytes(b'an error page')
    dest = tmp_path / 'petsc.zip'
    result = _run(
        f'fetch_verified {_sha256(b"petsc archive")} "{dest}" '
        f'"file://{tmp_path}/missing.zip" "" "file://{bad}" "file://{good}"\necho REACHED_UNZIP\n'
    )
    assert result.returncode == 0, result.stderr
    assert dest.read_bytes() == b'petsc archive'
    assert 'REACHED_UNZIP' in result.stdout
    assert f'download from file://{tmp_path}/missing.zip failed' in result.stdout
    assert f'served a file with SHA-256 {_sha256(b"an error page")}' in result.stdout


def test_no_matching_source_stops_before_unzip(tmp_path):
    """With no source serving the pinned file the script stops and leaves no archive."""
    bad = tmp_path / 'bad.zip'
    bad.write_bytes(b'an error page')
    dest = tmp_path / 'petsc.zip'
    result = _run(f'fetch_verified {"0" * 64} "{dest}" "file://{bad}" ""\necho REACHED_UNZIP\n')
    assert result.returncode == 1
    assert 'REACHED_UNZIP' not in result.stdout
    assert not dest.exists()
    assert f'no source served petsc.zip with SHA-256 {"0" * 64}' in result.stdout


def test_the_script_pins_the_zenodo_archive_and_its_hash():
    """The default source is the Zenodo archive, with its SHA-256 pinned beside it and both
    sources overridable for a mirror or a test."""
    text = SCRIPT.read_text()
    assert (
        'url="${PETSC_URL:-https://zenodo.org/records/15805756/files/petsc.zip?download=1}"'
        in text
    )
    assert 'mirror_url="${PETSC_MIRROR_URL:-https://dataverse.nl/api/access/datafile/683669}"' in text
    (sha,) = re.findall(r'^petsc_sha256="([0-9a-f]{64})"$', text, re.M)
    assert sha == 'c5bdb75048b609627bac7fdc83042078a629f5de0c6508b50166a351d2aa045d'
    assert 'fetch_verified "$petsc_sha256" "$zipfile" "$url" "$mirror_url"' in text
