#!/usr/bin/env python3
"""Generate shields.io endpoint-badge JSON files for the test-suite counts.

Counts tests by pytest collection (no binary or PETSc required) and
writes one shields.io endpoint-badge JSON file per public badge:

    {"schemaVersion": 1, "label": "<label>", "message": "<count>", "color": "blue"}

Three badges are published, two categories that sum to the total:

* ``tests-total.json``       - every collected test (``not skip``).
* ``tests-unit.json``        - the unit tier (C test executables and Python logic).
* ``tests-integration.json`` - the smoke, integration, and slow tiers combined.

The internal pytest marker scheme has four tiers (``unit``, ``smoke``,
``integration``, ``slow``); the public badge surface collapses ``smoke +
integration + slow`` into a single "integration tests" category so the
count badges match the two-category convention used across the ecosystem
modules. Internal CI granularity is unaffected: the four markers are
still registered in ``pyproject.toml`` and drive ``ci.yml`` and
``nightly.yml`` directly.

Usage
-----
    python tools/generate_test_badges.py --out badge_payload/

The published copies live on the ``badges`` branch, written there by the
``Refresh test count badges`` workflow; nothing is committed into the
source tree on ``main``. The publish job rebuilds the branch from the
generated files on every run, so a category that is no longer emitted
here disappears from the branch on the next refresh. Collection needs
the Python test dependencies (pytest, pytest-timeout, numpy) but neither
PETSc nor a built binary. A collection failure or a zero count fails the
run loudly instead of publishing a wrong number.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

# name -> (badge label, pytest -m expression). The public surface is the
# total plus two categories that partition it: the unit tier, and the
# smoke, integration, and slow tiers combined under "integration tests".
_BADGES = {
    'total': ('tests', 'not skip'),
    'unit': ('unit tests', 'unit and not skip'),
    'integration': ('integration tests', '(smoke or integration or slow) and not skip'),
}

_COLLECTED_RE = re.compile(r'(\d+)(?:/\d+)? tests? collected')


def count_tests(marker_expression: str) -> int:
    """Return the number of tests pytest collects for a marker expression.

    Parameters
    ----------
    marker_expression : str
        The ``-m`` filter to count.

    Returns
    -------
    int
        Number of collected (selected) tests.

    Raises
    ------
    RuntimeError
        If collection fails or the count cannot be parsed. Propagated
        deliberately so a broken suite fails the badge run rather than
        publishing a wrong number.
    """
    proc = subprocess.run(
        [
            sys.executable, '-m', 'pytest', '--collect-only', '-q',
            '-m', marker_expression, '-p', 'no:cacheprovider',
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    # pytest exits 5 when a filter selects nothing; that still parses below.
    if proc.returncode not in (0, 5):
        raise RuntimeError(
            f'pytest collection failed for -m "{marker_expression}":\n'
            f'{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}'
        )
    for line in reversed(proc.stdout.splitlines()):
        if 'no tests collected' in line:
            return 0
        match = _COLLECTED_RE.search(line)
        if match:
            return int(match.group(1))
    raise RuntimeError(
        f'could not parse the collection count for -m "{marker_expression}":\n'
        f'{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}'
    )


def write_badge(out_dir: Path, name: str, label: str, count: int) -> Path:
    """Write one shields.io endpoint-badge JSON file.

    Parameters
    ----------
    out_dir : Path
        Directory to write the JSON file into. Created if absent.
    name : str
        Suffix used in the filename ``tests-<name>.json``.
    label : str
        Badge label rendered on the left side of the shield.
    count : int
        Badge message rendered on the right side of the shield.

    Returns
    -------
    Path
        Path of the written JSON file.
    """
    payload = {
        'schemaVersion': 1,
        'label': label,
        'message': str(count),
        'color': 'blue',
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'tests-{name}.json'
    out_path.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    return out_path


def main() -> int:
    """Entry point.

    Returns
    -------
    int
        Process exit code (0 on success; failures raise).
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--out',
        type=Path,
        required=True,
        help='Directory to write the badge JSON files into.',
    )
    args = parser.parse_args()

    counts = {name: count_tests(expr) for name, (_, expr) in _BADGES.items()}
    if counts['total'] == 0:
        raise RuntimeError('collected zero tests in total; refusing to publish.')
    if counts['unit'] + counts['integration'] != counts['total']:
        raise RuntimeError(
            f'category counts do not partition the total ({counts}); '
            'a test is missing a tier marker or carries two.'
        )
    for name, (label, _) in _BADGES.items():
        write_badge(args.out, name, label, counts[name])
        print(f'{label}: {counts[name]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
