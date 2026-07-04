#!/usr/bin/env python3
"""Generate a shields.io endpoint-badge JSON file for the SPIDER test count.

SPIDER's test suite is a set of SciATH integration cases defined in
``tests/tests.yml`` (each case drives the compiled C/PETSc ``spider`` binary
and its Python post-processing, not pytest). This script counts those cases
and writes a single shields.io endpoint-badge JSON file:

    {"schemaVersion": 1, "label": "tests", "message": "<count>", "color": "blue"}

The count is the number of entries in the ``tests:`` sequence of
``tests/tests.yml``, which is one-to-one with the cases the SciATH harness
builds and runs. ``tests/tests.yml`` is not standard YAML (SciATH allows
constructs such as ``key: val:`` that a general YAML parser rejects), so the
file is read with SciATH's own tolerant subset parser rather than PyYAML. The
count therefore depends only on the case list in ``tests/tests.yml``, and a
genuinely unparseable or empty file fails the run loudly instead of publishing
a wrong or zero number.

Usage
-----
    python tools/generate_test_badges.py --out badge_payload/

The published copy lives on the ``badges`` branch, written there by the
``Refresh test count badges`` workflow; nothing is committed into the source
tree on ``main``. SciATH must be importable: the workflow clones it into
``tests/sciath`` (mirroring the test job), and when run there this script adds
that directory to the import path automatically. SciATH's parser depends only
on the standard library, so no third-party install is needed to produce the
count.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TESTS_FILE = _REPO_ROOT / "tests" / "tests.yml"

# Single-file public surface. SPIDER has no unit/integration split to expose,
# so only the total count is published; faking sub-categories the suite does
# not have would misrepresent it.
_BADGE_NAME = "total"
_BADGE_LABEL = "tests"


def _ensure_sciath_importable() -> None:
    """Make the ``sciath`` package importable, vendoring it if needed.

    Prefers an already-installed or ``PYTHONPATH``-exposed SciATH. Falls back
    to the ``tests/sciath`` clone that the CI test job and the badge workflow
    create, so the same checkout works locally and in CI.

    Raises
    ------
    ModuleNotFoundError
        If SciATH is neither importable nor present at ``tests/sciath``.
    """
    try:
        import sciath  # noqa: F401

        return
    except ModuleNotFoundError as exc:
        # Fall back to the vendored clone only when the top-level ``sciath``
        # package itself is absent, which is the CI case (SciATH is cloned into
        # tests/sciath but not installed). Any other missing import, such as a
        # dependency missing from inside a broken SciATH install, is a genuine
        # fault and re-raises rather than being hidden behind the fallback.
        if exc.name != "sciath":
            raise

    vendored = _REPO_ROOT / "tests" / "sciath"
    if vendored.is_dir():
        sys.path.insert(0, str(vendored))
        return

    raise ModuleNotFoundError(
        "SciATH is not importable and no clone was found at "
        f"{vendored}. Clone it there (git clone --depth=1 "
        "https://github.com/sciath/sciath tests/sciath) or add it to "
        "PYTHONPATH before running this script."
    )


def count_sciath_tests(tests_file: Path) -> int:
    """Return the number of SciATH cases defined in ``tests_file``.

    Parameters
    ----------
    tests_file : Path
        Path to the SciATH test-definition YAML (``tests/tests.yml``).

    Returns
    -------
    int
        Number of entries in the ``tests:`` sequence, i.e. the number of
        cases the SciATH harness builds and runs.

    Raises
    ------
    FileNotFoundError
        If ``tests_file`` does not exist.
    sciath.yaml_parse.SciATHYAMLParseException
        If the file cannot be parsed. Propagated deliberately so a broken
        definition fails the badge run rather than publishing a wrong number.
    ValueError
        If the parsed file has no ``tests:`` sequence, or the sequence is
        empty. SPIDER always defines at least one case, so a zero count means
        the definition or the parse degraded and must not be published.
    """
    if not tests_file.is_file():
        raise FileNotFoundError(f"SciATH test definition not found: {tests_file}")

    _ensure_sciath_importable()
    from sciath import yaml_parse

    data = yaml_parse.parse_yaml_subset_from_file(str(tests_file))
    if not isinstance(data, dict) or not isinstance(data.get("tests"), list):
        raise ValueError(f"{tests_file} must contain a 'tests:' sequence of cases.")

    count = len(data["tests"])
    if count == 0:
        raise ValueError(
            f"No SciATH cases found in {tests_file}; refusing to publish a zero count."
        )
    return count


def write_badge(out_dir: Path, name: str, label: str, count: int) -> Path:
    """Write a shields.io endpoint-badge JSON file.

    Parameters
    ----------
    out_dir : Path
        Directory to write the JSON file into. Created if absent.
    name : str
        Suffix used in the filename ``tests-<name>.json``.
    label : str
        Badge label rendered on the left side of the shield.
    count : int
        Badge message count rendered on the right side of the shield.

    Returns
    -------
    Path
        Path of the written JSON file.
    """
    payload = {
        "schemaVersion": 1,
        "label": label,
        "message": str(count),
        "color": "blue",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"tests-{name}.json"
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
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
        "--out",
        type=Path,
        required=True,
        help="Directory to write the tests-total.json badge file into.",
    )
    args = parser.parse_args()

    count = count_sciath_tests(_TESTS_FILE)
    write_badge(args.out, _BADGE_NAME, _BADGE_LABEL, count)
    print(f"{_BADGE_LABEL}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
