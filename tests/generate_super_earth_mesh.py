#!/usr/bin/env python
"""Generate a SPIDER external mesh file for a synthetic super-Earth profile.

Uses a polytropic density model (not Adams-Williamson) to create a
physically plausible but distinct density profile for testing that SPIDER
can run with non-AW mesh inputs.

The model assumes:
- 3 Earth masses, 1.3 Earth radii (mass-radius scaling)
- Linear density decrease from CMB to surface (simplified)
- Hydrostatic equilibrium: dP/dr = -rho * |g|
- Gravity computed from enclosed mass: g(r) = -G*M(r)/r^2

File format matches SPIDER expectations (SI units, surface to CMB ordering,
negative gravity).
"""

import argparse
import numpy as np


def compute_profile(R, R_core, rho_cmb, rho_surf, n_fine=5000):
    """Compute a self-consistent hydrostatic profile.

    Parameters
    ----------
    R : float
        Planet radius [m].
    R_core : float
        Core radius [m].
    rho_cmb : float
        Density at CMB [kg/m^3].
    rho_surf : float
        Density at surface [kg/m^3].
    n_fine : int
        Number of fine grid points for integration.

    Returns
    -------
    r : ndarray
        Radii from surface to CMB (descending).
    P : ndarray
        Pressure [Pa].
    rho : ndarray
        Density [kg/m^3].
    g : ndarray
        Gravity [m/s^2] (negative, pointing inward).
    """
    G = 6.674e-11  # gravitational constant

    # Fine grid from CMB to surface (ascending r)
    r_fine = np.linspace(R_core, R, n_fine)
    dr = r_fine[1] - r_fine[0]

    # Linear density profile (CMB to surface)
    rho_fine = rho_cmb + (rho_surf - rho_cmb) * (r_fine - R_core) / (R - R_core)

    # Compute enclosed mass and gravity (integrating outward from CMB)
    # Assume core mass from core density * core volume
    rho_core_avg = 12000.0  # typical iron core density
    M_core = (4.0 / 3.0) * np.pi * R_core**3 * rho_core_avg

    M_enclosed = np.zeros(n_fine)
    M_enclosed[0] = M_core
    for i in range(1, n_fine):
        dM = 4.0 * np.pi * r_fine[i - 1] ** 2 * rho_fine[i - 1] * dr
        M_enclosed[i] = M_enclosed[i - 1] + dM

    g_fine = -G * M_enclosed / r_fine**2  # negative (inward)

    # Integrate pressure from surface inward (P=0 at surface)
    # dP/dr = rho * g (both rho positive, g negative, so dP/dr < 0, P increases inward)
    P_fine = np.zeros(n_fine)
    # Integrate from surface (index -1) inward
    for i in range(n_fine - 2, -1, -1):
        dPdr = rho_fine[i] * g_fine[i]
        P_fine[i] = P_fine[i + 1] - dPdr * dr

    # Reverse to surface-first ordering (matching SPIDER convention)
    r_out = r_fine[::-1]
    P_out = P_fine[::-1]
    rho_out = rho_fine[::-1]
    g_out = g_fine[::-1]

    return r_out, P_out, rho_out, g_out


def interpolate_to_nodes(r_fine, P_fine, rho_fine, g_fine, r_nodes):
    """Interpolate fine profile onto node positions."""
    P_nodes = np.interp(r_nodes, r_fine[::-1], P_fine[::-1])
    rho_nodes = np.interp(r_nodes, r_fine[::-1], rho_fine[::-1])
    g_nodes = np.interp(r_nodes, r_fine[::-1], g_fine[::-1])
    return P_nodes, rho_nodes, g_nodes


def main():
    parser = argparse.ArgumentParser(
        description="Generate super-Earth external mesh file for SPIDER"
    )
    parser.add_argument("-n", type=int, default=50,
                        help="Number of basic nodes (default: 50)")
    parser.add_argument("-radius", type=float, default=8.28e6,
                        help="Planet radius [m] (default: 1.3 R_Earth)")
    parser.add_argument("-coresize", type=float, default=0.50,
                        help="Core size fraction (default: 0.50)")
    parser.add_argument("-o", "--output", type=str, required=True,
                        help="Output mesh file path")
    args = parser.parse_args()

    numpts_b = args.n
    numpts_s = numpts_b - 1
    R = args.radius
    R_core = args.coresize * R

    # Super-Earth mantle densities
    rho_cmb = 5500.0   # kg/m^3, density at CMB
    rho_surf = 3500.0  # kg/m^3, density at surface

    # Compute fine profile
    r_fine, P_fine, rho_fine, g_fine = compute_profile(
        R, R_core, rho_cmb, rho_surf
    )

    # Create node positions (surface to CMB, uniformly spaced in radius)
    r_b = np.linspace(R, R_core, numpts_b)
    r_s = 0.5 * (r_b[:-1] + r_b[1:])  # staggered midpoints

    # Interpolate onto nodes
    P_b, rho_b, g_b = interpolate_to_nodes(r_fine, P_fine, rho_fine, g_fine, r_b)
    P_s, rho_s, g_s = interpolate_to_nodes(r_fine, P_fine, rho_fine, g_fine, r_s)

    # Write output file
    with open(args.output, "w") as f:
        f.write(f"# {numpts_b} {numpts_s}\n")
        for i in range(numpts_b):
            f.write(f"{r_b[i]:.15e} {P_b[i]:.15e} {rho_b[i]:.15e} {g_b[i]:.15e}\n")
        for i in range(numpts_s):
            f.write(f"{r_s[i]:.15e} {P_s[i]:.15e} {rho_s[i]:.15e} {g_s[i]:.15e}\n")

    # Summary
    mantle_mass = 0.0
    for i in range(numpts_s):
        vol = (r_b[i] ** 3 - r_b[i + 1] ** 3) / 3.0
        mantle_mass += rho_s[i] * vol
    mantle_mass *= 4.0 * np.pi

    print(f"Wrote {args.output}: {numpts_b} basic + {numpts_s} staggered nodes")
    print(f"  R = {R:.0f} m, R_core = {R_core:.0f} m")
    print(f"  rho range: [{rho_surf:.0f}, {rho_cmb:.0f}] kg/m^3")
    print(f"  P range: [{P_b[0]:.3e}, {P_b[-1]:.3e}] Pa")
    print(f"  g range: [{g_b[0]:.3e}, {g_b[-1]:.3e}] m/s^2")
    print(f"  Mantle mass: {mantle_mass:.3e} kg")


if __name__ == "__main__":
    main()
