"""Helpers for reading SPIDER lookup tables in tests.

The table format is the one parsed by interp.c: a first header line
``# HEAD NX [NY]`` giving the header length and grid size, per-column
SI scaling factors on header line ``HEAD - 1``, and whitespace-separated
data rows (x fastest for 2-D tables). These helpers return SI arrays so
tests can evaluate the tables independently of the C implementation.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


def read_2d_table(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Read a SPIDER 2-D lookup table.

    Parameters
    ----------
    path : Path
        Table file (e.g. ``lookup_data/1TPa-dK09-elec-free/density_melt.dat``).

    Returns
    -------
    xa : numpy.ndarray, shape (NX,)
        x nodes (pressure) in SI units.
    ya : numpy.ndarray, shape (NY,)
        y nodes (entropy) in SI units.
    za : numpy.ndarray, shape (NX, NY)
        Table values in SI units.
    """
    lines = Path(path).read_text().splitlines()
    head, nx, ny = (int(v) for v in lines[0].lstrip('#').split())
    sx, sy, sz = (float(v) for v in lines[head - 1].lstrip('#').split())
    rows = np.array([[float(v) for v in line.split()] for line in lines[head : head + nx * ny]])
    xa = rows[:nx, 0] * sx
    ya = rows[::nx, 1] * sy
    za = np.empty((nx, ny))
    for j in range(ny):
        za[:, j] = rows[j * nx : (j + 1) * nx, 2] * sz
    return xa, ya, za


def bilinear(xa: np.ndarray, ya: np.ndarray, za: np.ndarray, x: float, y: float) -> float:
    """Bilinear interpolation on an in-range query point.

    An independent evaluation of the same mathematical operation
    interp.c performs, written against numpy primitives so the two
    implementations share no code.
    """
    i = int(np.searchsorted(xa, x, side='right') - 1)
    j = int(np.searchsorted(ya, y, side='right') - 1)
    i = min(max(i, 0), len(xa) - 2)
    j = min(max(j, 0), len(ya) - 2)
    tx = (x - xa[i]) / (xa[i + 1] - xa[i])
    ty = (y - ya[j]) / (ya[j + 1] - ya[j])
    return float(
        za[i, j] * (1 - tx) * (1 - ty)
        + za[i + 1, j] * tx * (1 - ty)
        + za[i, j + 1] * (1 - tx) * ty
        + za[i + 1, j + 1] * tx * ty
    )
