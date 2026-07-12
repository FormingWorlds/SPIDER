"""Tests for ic.c (initial condition of the entropy profile).

Driven through cached blackbody50 runs of the spider binary, including
a zero-macro-step run that emits only the initial condition (the
limit-input configuration). Invariants exercised: the prescribed
adiabat entropy is recovered exactly at the top staggered node, the
initial profile is flat up to the small prescribed ic_dsdr gradient,
entropy positivity, discrimination between different ic_adiabat_entropy
values, and the loss of initial flatness once grey-body cooling has
acted. See docs/How-to/build_tests.md for the tier system.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests._json_utils import data_si, read_output, solution_entries

pytestmark = [pytest.mark.smoke, pytest.mark.timeout(120)]

# blackbody50 geometry: radius 6371000 m, coresize 0.55, so the mantle
# shell spans 6371000 * 0.45 m from surface to core-mantle boundary.
MANTLE_DEPTH = 2866950.0  # m
IC_ENTROPY = 2600.0  # J/kg/K, blackbody50 ic_adiabat_entropy
IC_DSDR = -1.0e-5  # J/kg/K/m, blackbody50 ic_dsdr


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_prescribed_adiabat_entropy_sets_the_initial_profile(
    blackbody_short, cached_spider_run
):
    """The IC recovers ic_adiabat_entropy at the top staggered node.

    Anchor: analytical limit. The initial condition prescribes
    S = ic_adiabat_entropy (2600 J/kg/K in blackbody50) at the top
    staggered node and integrates the small ic_dsdr gradient inward, so
    the top node carries the option value exactly and the profile mean
    sits slightly above it (the gradient raises entropy with depth).
    """
    doc = read_output(blackbody_short, 0)
    s_s = data_si(doc, 'S_s')  # J/kg/K, surface first
    entries = {e['description']: e for e in solution_entries(doc)}
    top = entries['S at top staggered node']
    s_top = float(top['values'][0]) * float(top['scaling'])  # J/kg/K

    # rel=1e-3 (2.6 J/kg/K) is generous against the observed exact
    # recovery but still rejects any competing entropy value by far.
    assert s_top == pytest.approx(IC_ENTROPY, rel=1e-3)
    assert s_s[0] == pytest.approx(IC_ENTROPY, rel=1e-3)
    # The ic_dsdr ramp bounds the mean from above: the mean must lie
    # between the top value and top + |ic_dsdr| * mantle depth
    # (2600 to 2628.7 J/kg/K; observed offset ~14.7 J/kg/K).
    assert IC_ENTROPY < s_s.mean() < IC_ENTROPY + abs(IC_DSDR) * MANTLE_DEPTH

    # Wrong-value discrimination: rerunning the IC with
    # -ic_adiabat_entropy 2400 shifts every staggered node by exactly
    # the 200 J/kg/K offset (the ramp term is identical), far beyond
    # the 2.6 J/kg/K pin tolerance.
    outdir = cached_spider_run(
        overrides=('-nstepsmacro', '0', '-ic_adiabat_entropy', '2400.0'), name='ic_2400'
    )
    s_24 = data_si(read_output(outdir, 0), 'S_s')
    assert s_24.mean() == pytest.approx(s_s.mean() - 200.0, rel=1e-9)
    assert abs(s_s.mean() - s_24.mean()) > 10 * (1e-3 * IC_ENTROPY)
    # Sign and scale guards: silicate specific entropies sit at a few
    # thousand J/kg/K; a nondimensional leak would sit near unity.
    assert np.all(s_s > 0)
    assert 1e3 < s_s.mean() < 1e4


@pytest.mark.physics_invariant
def test_initial_adiabat_is_nearly_flat_until_cooling_imprints_structure(blackbody_short):
    """The IC profile is flat up to the ic_dsdr ramp; cooling breaks it.

    The only structure the initial condition imprints is the prescribed
    ic_dsdr gradient, so the profile spread is bounded by
    |ic_dsdr| * mantle depth (28.7 J/kg/K, about 1.1 percent of the
    mean). After 200 years of grey-body cooling the top staggered node
    (the node exposed to the surface boundary) has lost entropy, so the
    near-flatness of the t = 0 edge state does not persist.
    """
    doc_0 = read_output(blackbody_short, 0)
    s_0 = data_si(doc_0, 'S_s')  # J/kg/K, surface first

    # Spread bounded by the prescribed gradient across the mantle:
    # 1e-5 J/kg/K/m * 2866950 m = 28.7 J/kg/K (observed 28.1).
    spread = s_0.max() - s_0.min()
    assert spread < abs(IC_DSDR) * MANTLE_DEPTH
    # The relative spread stays around one percent of the mean.
    assert spread / s_0.mean() < 0.02
    assert np.all(s_0 > 0)

    # Cooling imprint: the top staggered node has lost entropy by 200
    # years, and the drop (~160 J/kg/K observed) is resolved far above
    # the CVODE tolerance floor, so the inequality is strict by margin.
    s_200 = data_si(read_output(blackbody_short, 200), 'S_s')
    assert s_200[0] < s_0[0]
    assert s_0[0] - s_200[0] > 10.0  # J/kg/K
