"""Tests for dimensionalisablefield.c (the scaled-field wrapper).

Driven through the C test executable tests/c/test_dimensionalisablefield,
which builds a five-node field with scaling 2.5, fills it with 1..5, and
exercises scale, unscale, duplicate, the local-vector factory, and the
scaling query. Contract clauses exercised: scaling multiplies by the
stored factor, unscaling inverts it exactly, the duplicate carries the
scaling and domain count, and the serial local vector matches the mesh
size. See docs/How-to/build_tests.md for the tier system.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]

# Values hard-coded in the C executable.
SCALING = 2.5
FIRST_VALUE = 1.0
MESH_SIZE = 5


def test_scale_unscale_round_trip_is_exact(c_test):
    """Scaling multiplies by the stored factor and unscaling inverts it.

    The field starts unscaled with first value 1.0; after Scale the
    stored entry is 2.5, and after Unscale it returns to 1.0 exactly
    (a multiply and divide by the same factor, no accumulation). The
    unit scaling factor is the edge the wrapper must not special-case:
    with 2.5 the scaled and raw values differ by 150 percent, so a
    no-op Scale cannot pass.
    """
    out = c_test('test_dimensionalisablefield')

    # rel=1e-15: one multiplication, roundoff only.
    assert out['scaled0'] == pytest.approx(SCALING * FIRST_VALUE, rel=1e-15)
    # No-op guard: scaling must actually change the stored values.
    assert abs(out['scaled0'] - out['original0']) > 1.0
    # Round trip: unscale exactly inverts scale.
    assert out['roundtrip0'] == pytest.approx(out['original0'], rel=1e-15)
    assert out['original0'] == pytest.approx(FIRST_VALUE, rel=1e-15)


def test_duplicate_carries_scaling_and_layout(c_test):
    """A duplicated field reports the parent's scaling and domain count.

    The duplicate is created over the same serial DMDA, so it has one
    domain, the parent's 2.5 scaling, and a local vector of the mesh
    size (the limit input: a single-domain, single-rank layout with no
    ghost points).
    """
    out = c_test('test_dimensionalisablefield')

    assert out['dup_scaling0'] == pytest.approx(SCALING, rel=1e-15)
    # Scaling discrimination: the duplicate must carry 2.5, not the
    # unit scaling a fresh field would default to.
    assert abs(out['dup_scaling0'] - 1.0) > 1.0
    assert int(out['num_domains']) == 1
    assert int(out['nlocal']) == MESH_SIZE
