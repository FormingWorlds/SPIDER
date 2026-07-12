"""Shared fixtures for the SPIDER pytest suite.

The suite drives the compiled ``spider`` binary (smoke tier and up) and
the C test executables under ``tests/c/`` (unit tier). Expensive runs
are shared through session-scoped caches so each configuration is
computed once per session.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
OPTS_DIR = REPO_ROOT / 'tests' / 'opts'
C_TESTS_DIR = REPO_ROOT / 'tests' / 'c'

# Session cache of completed spider runs, keyed by (opts_file, overrides).
_RUN_CACHE: dict[tuple, Path] = {}


def _spider_executable() -> Path | None:
    """Locate the spider binary: $SPIDER_EXEC first, then the repo root."""
    env = os.environ.get('SPIDER_EXEC')
    candidates = [Path(env)] if env else [REPO_ROOT / 'spider']
    for p in candidates:
        if p.is_file() and os.access(p, os.X_OK):
            return p
    return None


@pytest.fixture(scope='session')
def spider_exec() -> Path:
    """Path to the built spider binary; skips the test when it is absent."""
    p = _spider_executable()
    if p is None:
        pytest.skip('spider binary not found; build it with make or set SPIDER_EXEC')
    return p


@pytest.fixture(scope='session')
def run_spider(spider_exec, tmp_path_factory):
    """Factory fixture: run spider into a fresh output directory.

    Returns a callable ``_run(opts_file, overrides, name, timeout)`` that
    executes ``spider -options_file tests/opts/<opts_file> -outputDirectory
    <fresh tmp dir> <overrides...>``, captures stdout/stderr next to the
    output, raises on a nonzero exit, and returns the output directory.
    """

    def _run(
        opts_file: str = 'blackbody50.opts',
        overrides: tuple = (),
        name: str = 'run',
        timeout: float = 600.0,
    ) -> Path:
        outdir = tmp_path_factory.mktemp(name)
        cmd = [
            str(spider_exec),
            '-options_file',
            str(OPTS_DIR / opts_file),
            '-outputDirectory',
            str(outdir),
            *map(str, overrides),
        ]
        proc = subprocess.run(
            cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout
        )
        (outdir / 'spider_stdout.log').write_text(proc.stdout)
        (outdir / 'spider_stderr.log').write_text(proc.stderr)
        if proc.returncode != 0:
            # The PETSc error block sits near the top of a long stderr
            # stream while the tail is MPI abort boilerplate; keep both
            # so tests can assert on the actual error message.
            stream = proc.stderr or proc.stdout
            petsc = '\n'.join(
                line for line in stream.splitlines() if 'PETSC ERROR' in line
            )[:2000]
            tail = stream[-2000:]
            raise RuntimeError(
                f'spider exited with code {proc.returncode} for {cmd}:\n{petsc}\n{tail}'
            )
        return outdir

    return _run


@pytest.fixture(scope='session')
def cached_spider_run(run_spider):
    """Session-scoped cache of spider runs, keyed by configuration.

    Use this instead of ``run_spider`` whenever the run's output is
    read-only for the test: identical configurations are computed once
    per session. Tests must never write into a cached output directory;
    restart tests copy the JSON files to their own ``tmp_path`` first.
    """

    def _get(
        opts_file: str = 'blackbody50.opts',
        overrides: tuple = (),
        name: str = 'cached',
        timeout: float = 600.0,
    ) -> Path:
        key = (opts_file, tuple(map(str, overrides)))
        if key not in _RUN_CACHE:
            _RUN_CACHE[key] = run_spider(opts_file, overrides, name=name, timeout=timeout)
        return _RUN_CACHE[key]

    return _get


@pytest.fixture(scope='session')
def blackbody_short(cached_spider_run) -> Path:
    """Two-macro-step blackbody50 run (n=50), the shared smoke-tier artifact.

    Output times are 0, 100, and 200 years; most smoke-tier invariant
    tests read ``200.json``.
    """
    return cached_spider_run(overrides=('-nstepsmacro', '2'), name='blackbody_short')


@pytest.fixture(scope='session')
def blackbody_full(cached_spider_run) -> Path:
    """Full 12-macro-step blackbody50 run matching the frozen reference.

    This is the configuration behind ``tests/expected_output/
    expected_blackbody50.txt`` (final output at 1200 years).
    """
    return cached_spider_run(name='blackbody_full')


@pytest.fixture(scope='session')
def c_test():
    """Run a C test executable from ``tests/c/`` and parse its JSON stdout.

    The callable skips the test when the executable has not been built
    (``make tests_c``) and raises on a nonzero exit so an internal PETSc
    failure is a hard test failure, never a silent pass.
    """

    def _run(name: str, args: tuple = ()) -> dict:
        exe = C_TESTS_DIR / name
        if not (exe.is_file() and os.access(exe, os.X_OK)):
            pytest.skip(f'{exe.name} not built; run make tests_c')
        proc = subprocess.run(
            [str(exe), *map(str, args)], capture_output=True, text=True, timeout=60
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f'{exe.name} exited with code {proc.returncode}:\n{proc.stderr[-2000:]}'
            )
        # The executable prints one JSON object; tolerate PETSc chatter
        # around it by slicing from the first '{' to the last '}' and
        # dropping interleaved warning lines (e.g. the EOS-table clamp
        # warnings, which print during evaluation).
        text = proc.stdout
        start, end = text.find('{'), text.rfind('}')
        if start < 0 or end < 0:
            raise RuntimeError(f'{exe.name} produced no JSON on stdout:\n{text[-2000:]}')
        payload = '\n'.join(
            line
            for line in text[start : end + 1].splitlines()
            if not line.startswith('WARNING')
        )
        return json.loads(payload)

    return _run
