"""Tests for mesh.c (static planetary structure and mesh geometry).

Invariants exercised: the closed-form Adams-Williamson pressure profile
at the basic nodes, monotonicity of radius and pressure with depth,
interleaving of staggered pressures between their bounding basic nodes,
per-shell mass consistency against the analytical Adams-Williamson
integral (with the 4*pi geometry factor), mantle mass closure, and the
external-mesh input pathway (-MESH_SOURCE 1) as the alternative to the
built-in profile. See docs/How-to/build_tests.md for the tier system.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tests._json_utils import atmosphere_si, data_si, read_output

pytestmark = [pytest.mark.smoke, pytest.mark.timeout(60)]

REPO_ROOT = Path(__file__).resolve().parent.parent

# Adams-Williamson parameters as configured in tests/opts/blackbody50.opts
# (a PREM lower-mantle fit). Gravity is negative by SPIDER convention.
RHOS = 4078.95095544  # kg/m^3, surface density
BETA = 1.1115348931000002e-07  # 1/m, compressibility parameter
GRAVITY = -10.0  # m/s^2, negative (pointing inward)
RADIUS = 6371000.0  # m, planetary radius


@pytest.mark.physics_invariant
@pytest.mark.reference_pinned
def test_pressure_profile_matches_adams_williamson_closed_form(blackbody_short):
    """Basic-node pressures reproduce the analytical Adams-Williamson profile.

    Analytical anchor: the hydrostatic Adams-Williamson solution
    P(r) = -rhos*g/beta * (exp(beta*(R - r)) - 1) with density
    rho(P) = rhos - P*beta/g, evaluated at the mesh's own radii.
    """
    doc = read_output(blackbody_short, 0)
    radius_b = data_si(doc, 'radius_b')  # m
    pressure_b = data_si(doc, 'pressure_b')  # Pa

    expected = -RHOS * GRAVITY / BETA * (np.exp(BETA * (RADIUS - radius_b)) - 1.0)
    # rtol=1e-12: mesh.c evaluates the same closed form, so agreement is
    # limited only by the nondimensional round-trip through the JSON
    # output (observed max rel 7e-15, so the pin has 100x headroom).
    np.testing.assert_allclose(pressure_b, expected, rtol=1e-12)

    # Limit input: the surface node sits at r = R where the profile
    # vanishes, so |P| stays within rounding of zero (observed 1e-3 Pa)
    # while the CMB carries ~1.4e11 Pa, fourteen decades away.
    assert abs(pressure_b[0]) < 1.0  # Pa
    # Sign guard: with g < 0 the pressure must increase with depth; a
    # sign slip on gravity would flip the whole gradient.
    assert np.all(np.diff(pressure_b) > 0)
    # Scale guard: the CMB pressure is of order 1.3e11 Pa for these
    # PREM-like parameters; a nondimensional leak would sit near unity.
    assert 5e10 < pressure_b.max() < 5e11  # Pa
    # Wrong-formula guards at the CMB: the constant-density (linear)
    # profile rhos*|g|*(R - r) is 15% low, and a sign-flipped beta is
    # 27% low, both vastly beyond the 1e-12 pin tolerance.
    p_cmb = pressure_b[-1]
    depth_cmb = RADIUS - radius_b[-1]
    linear = RHOS * abs(GRAVITY) * depth_cmb
    flipped_beta = RHOS * GRAVITY / BETA * (np.exp(-BETA * depth_cmb) - 1.0)
    assert abs(p_cmb - linear) > 0.1 * p_cmb
    assert abs(p_cmb - flipped_beta) > 0.1 * p_cmb


def _aw_mass_antiderivative(r: np.ndarray) -> np.ndarray:
    """Antiderivative of 4*pi*rho_AW(r)*r^2 for the shell-mass integral."""
    return (
        -4.0
        * np.pi
        * RHOS
        * np.exp(BETA * (RADIUS - r))
        * (r**2 / BETA + 2.0 * r / BETA**2 + 2.0 / BETA**3)
    )


@pytest.mark.physics_invariant
def test_mesh_orderings_interleave_and_shell_masses_close(blackbody_short):
    """Node orderings are consistent and shell masses close on the mantle mass.

    The arrays are surface first: radius falls and pressure rises along
    the index, each staggered pressure lies strictly between its two
    bounding basic nodes, and the staggered shell masses integrate the
    Adams-Williamson density analytically over each shell.
    """
    doc = read_output(blackbody_short, 0)
    radius_b = data_si(doc, 'radius_b')  # m
    pressure_b = data_si(doc, 'pressure_b')  # Pa
    pressure_s = data_si(doc, 'pressure_s')  # Pa
    mass_s = data_si(doc, 'mass_s')  # kg

    # Orientation contract: 50 basic nodes bracket 49 staggered nodes,
    # both counted from the surface inward.
    assert radius_b.shape == (50,)
    assert pressure_s.shape == (49,)
    assert np.all(np.diff(radius_b) < 0)
    assert np.all(np.diff(pressure_b) > 0)
    # The interleaving is strict at every interior interface; an
    # off-by-one node indexing slip would violate it immediately.
    assert np.all(pressure_s > pressure_b[:-1])
    assert np.all(pressure_s < pressure_b[1:])

    # Shell masses: mesh.c integrates the Adams-Williamson density
    # analytically, so the exact antiderivative of 4*pi*rho(r)*r^2
    # reproduces mass_s at rtol=1e-11 (observed max rel 1e-12; the
    # residual is float64 cancellation between the antiderivative
    # evaluations at the two shell edges). The midpoint approximation
    # rho(r_mid)*V agrees only to 2e-5, and the dynamic EOS density
    # rho_s from the JSON differs by up to 38%, so the tight tolerance
    # pins the quadrature scheme and the density source.
    expected_mass = _aw_mass_antiderivative(radius_b[:-1]) - _aw_mass_antiderivative(
        radius_b[1:]
    )
    np.testing.assert_allclose(mass_s, expected_mass, rtol=1e-11)
    # Geometry-factor guard: the SI mass_s values carry the 4*pi of true
    # spherical shells; dropping it leaves a 92% relative offset.
    assert abs(mass_s[0] - expected_mass[0] / (4.0 * np.pi)) > 0.5 * mass_s[0]

    # Conservation: the shell masses sum to the reported mantle mass.
    mantle_mass = atmosphere_si(doc, 'mass_mantle')  # kg
    assert mass_s.sum() == pytest.approx(mantle_mass, rel=1e-12)
    # Scale guard: an Earth-sized silicate mantle holds ~4e24 kg.
    assert 1e24 < mantle_mass < 1e25  # kg


def test_external_linear_density_mesh_replaces_the_aw_profile(
    blackbody_short, run_spider, tmp_path
):
    """The external-mesh pathway runs on a structure the AW model cannot produce.

    With -MESH_SOURCE 1 the radius, pressure, density, and gravity
    profiles come from a file; a linear-density super-Earth mantle
    exercises this alternative input route end to end, including one
    macro step of time integration on the foreign structure.
    """
    mesh_file = tmp_path / 'non_aw.dat'
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / 'tests' / 'generate_super_earth_mesh.py'),
            '-n',
            '50',
            '-radius',
            '6371000.0',
            '-coresize',
            '0.55',
            '-o',
            str(mesh_file),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    # 1 header line + 50 basic + 49 staggered rows.
    assert len(mesh_file.read_text().splitlines()) == 100

    outdir = run_spider(
        overrides=(
            '-MESH_SOURCE',
            '1',
            '-mesh_external_filename',
            str(mesh_file),
            '-nstepsmacro',
            '1',
        ),
        name='non_aw_mesh',
    )
    assert (outdir / '100.json').is_file()
    doc = read_output(outdir, 100)
    radius_b = data_si(doc, 'radius_b')  # m
    pressure_b = data_si(doc, 'pressure_b')  # Pa

    # The structural invariants must hold on the external mesh too.
    assert np.all(np.diff(radius_b) < 0)
    assert np.all(np.diff(pressure_b) > 0)
    # The solution evolved on the foreign mesh stays finite and physical.
    temp_s = data_si(doc, 'temp_s')  # K
    assert np.all(np.isfinite(temp_s))
    assert np.all(temp_s > 0)

    # Wrong-path guard: the linear-density pressures depart from the
    # native AW profile by up to 25% relative at mid-mantle, far beyond
    # the 2e-3 external-mesh regression tolerance, proving the file was
    # actually read instead of silently falling back to the AW pathway.
    # The surface node is excluded because both profiles vanish there.
    pressure_aw = data_si(read_output(blackbody_short, 0), 'pressure_b')
    rel_diff = np.abs(pressure_b[1:] - pressure_aw[1:]) / pressure_aw[1:]
    assert rel_diff.max() > 0.05
