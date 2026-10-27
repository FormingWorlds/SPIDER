"""Display rounding for validation plots that draw values of a SPIDER run."""

from __future__ import annotations

import numpy as np


def shown(value, digits=3):
    """Round to significant digits, so that round-off between builds does not move a mark.

    The plot check compares the committed plot to about 1e-6 of a coordinate's range,
    while run output moves by up to a few 1e-6 between PETSc builds and platforms.

    Parameters
    ----------
    value : float or array_like
        Value or values from the run.
    digits : int
        Significant digits kept.

    Returns
    -------
    float or numpy.ndarray
        The rounded value, a float for a scalar input.
    """
    a = np.asarray(value, dtype=float)
    out = np.array([float(f'{v:.{digits}g}') for v in a.ravel()]).reshape(a.shape)
    return float(out) if out.ndim == 0 else out
