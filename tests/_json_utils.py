"""Helpers for reading SPIDER JSON output in tests.

SPIDER writes one JSON file per macro step. Every physical quantity is a
dimensionalisable field: a dict carrying ``values`` (numbers or numeric
strings), a ``scaling`` factor (numeric string, possibly whitespace
padded), a ``scaled`` flag, and ``units``. The SI value of a field is
``values * scaling`` whenever ``scaled`` is ``'false'``.

These helpers centralise that reconstruction so no test ever pins a
nondimensional internal by accident.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def read_output(output_dir: Path, time_years: int | str) -> dict:
    """Load the JSON document for one macro step.

    Parameters
    ----------
    output_dir : Path
        Directory the run wrote its JSON files into.
    time_years : int or str
        Output time in years; selects ``<time_years>.json``.

    Returns
    -------
    dict
        The parsed JSON document.
    """
    path = Path(output_dir) / f'{time_years}.json'
    with open(path) as fh:
        return json.load(fh)


def field_si(field: dict) -> np.ndarray:
    """Reconstruct the SI values of a dimensionalisable field.

    Parameters
    ----------
    field : dict
        A dimensionalisable-field dict with ``values``, ``scaling``, and
        ``scaled`` entries.

    Returns
    -------
    numpy.ndarray
        The field values in SI units (``values * scaling`` unless the
        field is already scaled).
    """
    values = np.array([float(v) for v in field['values']], dtype=float)
    if str(field.get('scaled', 'false')).lower() == 'true':
        return values
    return values * float(field['scaling'])


def data_si(doc: dict, name: str) -> np.ndarray:
    """SI array for a field in the document's ``data`` section."""
    return field_si(doc['data'][name])


def atmosphere_si(doc: dict, name: str) -> float:
    """SI scalar for a field in the document's ``atmosphere`` section."""
    arr = field_si(doc['atmosphere'][name])
    return float(arr[0])


def solution_entries(doc: dict) -> list[dict]:
    """Non-empty subdomain entries of the ``solution`` section.

    Empty ``values`` lists (fields disabled in the given configuration)
    are dropped, matching the frozen-reference format.
    """
    return [e for e in doc['solution']['subdomain data'] if len(e['values']) > 0]


def parse_expected_output(path: Path) -> list[dict]:
    """Parse a frozen reference file from ``tests/expected_output/``.

    The format is a flat sequence of ``description:`` / ``scaling:`` /
    ``val:`` lines per solution subdomain, as written by
    ``tests/json_timestep_to_txt.py``.

    Returns
    -------
    list of dict
        One entry per subdomain with ``description`` (str), ``scaling``
        (float), and ``values`` (numpy array of floats).
    """
    entries: list[dict] = []
    current: dict | None = None
    for line in Path(path).read_text().splitlines():
        if line.startswith('description: '):
            current = {'description': line[len('description: ') :], 'values': []}
            entries.append(current)
        elif line.startswith('scaling: '):
            assert current is not None, f'scaling before description in {path}'
            current['scaling'] = float(line[len('scaling: ') :])
        elif line.startswith('val: '):
            assert current is not None, f'val before description in {path}'
            current['values'].append(float(line[len('val: ') :]))
    for entry in entries:
        entry['values'] = np.array(entry['values'], dtype=float)
    return entries
