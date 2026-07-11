"""Tests for rheologicalfront.c (rheological front location and tracking).

Driven through the cached 12-macro-step blackbody50 run (blackbody_full),
which forms a detached front by 1200 years. Invariants exercised:
self-consistency between the reported front location and the melt
fraction profile in the same output, the front rising from the
core-mantle boundary as the mantle solidifies bottom-up, monotone decay
and boundedness of the global melt fraction, integer-valued mesh
indices, and the documented convention for the un-formed front at the
fully molten initial condition (the limit-input contract). See
docs/How-to/build_tests.md for the tier system.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests._json_utils import data_si, field_si, read_output

pytestmark = [pytest.mark.smoke, pytest.mark.timeout(60)]

PHI_CRITICAL = 0.4  # blackbody50 -phi_critical
# blackbody50 geometry: radius 6371000 m, coresize 0.55.
MANTLE_DEPTH = 2866950.0  # m
N_BASIC = 50  # blackbody50 -n (basic nodes; 49 staggered nodes)


def _front_scalars(doc: dict) -> dict:
    """SI scalars of the melt-fraction rheological front block."""
    front = doc['rheological_front_phi']
    keys = ('mesh_index', 'depth', 'pressure', 'temperature', 'phi_global')
    return {k: float(field_si(front[k])[0]) for k in keys}


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_front_location_is_consistent_with_melt_fraction_profile(blackbody_full):
    """The reported front sits where phi_s crosses phi_critical.

    Anchor: analytical self-consistency with the melt-fraction profile
    in the same output document. The detector scans the staggered melt
    fraction downward from below the surface and stops at the first
    node with phi_s < phi_critical (0.4); depth and pressure are then
    read off the basic-node arrays at that index, with depth measured
    from the planetary surface.
    """
    doc = read_output(blackbody_full, 1200)
    phi_s = data_si(doc, 'phi_s')  # dimensionless, surface first
    radius_b = data_si(doc, 'radius_b')  # m, surface first
    pressure_b = data_si(doc, 'pressure_b')  # Pa, surface first
    front = _front_scalars(doc)

    # Recompute the crossing: first staggered node below phi_critical,
    # scanning from node 1 because the detector skips the surface node.
    crossing = len(phi_s)
    for i in range(1, len(phi_s)):
        if phi_s[i] < PHI_CRITICAL:
            crossing = i
            break
    mesh_index = int(front['mesh_index'])
    assert front['mesh_index'] == pytest.approx(mesh_index, abs=1e-9)
    # +-1 node: a discrete-crossing re-derivation may land on the
    # first-below or the last-above node depending on convention.
    assert abs(mesh_index - crossing) <= 1

    # Depth is the planetary surface radius minus the basic-node radius
    # at the front index; radius_b[0] equals the configured planetary
    # radius, so the relation holds to machine precision (rel=1e-6
    # leaves headroom for the scaling round trip only).
    assert front['depth'] == pytest.approx(radius_b[0] - radius_b[mesh_index], rel=1e-6)
    assert front['pressure'] == pytest.approx(pressure_b[mesh_index], rel=1e-6)
    # Sign and scale guards: a detached front lies strictly inside the
    # mantle shell and its pressure inside the mantle pressure range.
    assert 0 < front['depth'] < MANTLE_DEPTH
    assert 0 < front['pressure'] < pressure_b.max()


@pytest.mark.physics_invariant
def test_front_rises_from_the_cmb_as_the_mantle_solidifies(blackbody_full):
    """Bottom-up solidification moves the front toward the surface.

    The blackbody50 mantle crystallises from the core-mantle boundary
    upward, so the front depth is non-increasing in time: it stays
    pinned at the CMB while even the deepest node is above phi_critical
    (2866950 m at 400 and 800 years) and has risen to 2668370 m by 1200
    years. The global melt fraction decays monotonically from the fully
    molten value of one and stays inside [0, 1]; mesh indices are
    integer-valued node counters within the mesh.
    """
    fronts = [_front_scalars(read_output(blackbody_full, t)) for t in (0, 400, 800, 1200)]
    depths = [f['depth'] for f in fronts]
    phis = [f['phi_global'] for f in fronts]

    # Non-increasing depth (front never sinks), strictly shallower once
    # the front detaches from the CMB by 1200 years.
    assert depths[3] <= depths[2] <= depths[1] <= depths[0]
    assert depths[3] < depths[0]
    # Secular cooling: strictly decreasing global melt fraction from
    # the fully molten edge value of one.
    assert phis[0] == pytest.approx(1.0, abs=1e-12)
    assert phis[0] > phis[1] > phis[2] > phis[3]
    for phi in phis:
        # abs=1e-12 headroom on the closed upper bound: the mass
        # average of phi_s = 1 everywhere reproduces one to rounding.
        assert 0.0 <= phi <= 1.0 + 1e-12
    for f in fronts:
        assert float(f['mesh_index']).is_integer()
        assert 0 <= f['mesh_index'] <= N_BASIC


@pytest.mark.physics_invariant
def test_unformed_front_reports_the_cmb_at_the_fully_molten_start(blackbody_full):
    """With no phi crossing the detector reports the CMB node.

    Limit-input contract: at t = 0 every staggered node is fully molten
    (phi_s = 1 everywhere), no node sits below phi_critical, and the
    detector returns the staggered node count (49), which is also the
    CMB basic-node index. Depth and pressure therefore land on the CMB:
    the full mantle depth and the maximum mantle pressure.
    """
    doc = read_output(blackbody_full, 0)
    phi_s = data_si(doc, 'phi_s')
    pressure_b = data_si(doc, 'pressure_b')
    front = _front_scalars(doc)

    # Precondition: the fully molten initial condition admits no
    # crossing, phi_s pinned at the upper boundary of [0, 1].
    assert np.all(phi_s >= PHI_CRITICAL)
    assert phi_s.min() == pytest.approx(1.0, abs=1e-12)
    # Un-formed-front convention: mesh_index = 49 = number of staggered
    # nodes = CMB basic-node index for the 50-node mesh.
    assert front['mesh_index'] == pytest.approx(N_BASIC - 1, abs=1e-9)
    # rel=1e-9: the CMB radius is a configuration constant, so only
    # scaling round-trip error separates depth from the mantle depth.
    assert front['depth'] == pytest.approx(MANTLE_DEPTH, rel=1e-9)
    assert front['pressure'] == pytest.approx(pressure_b.max(), rel=1e-9)
