#!/usr/bin/env python
"""Generate a SPIDER external mesh file using Adams-Williamson EOS parameters.

Replicates SPIDER's internal AW mesh computation in Python, writes the result
as an external mesh file. Used as a ground-truth test: SPIDER with
-MESH_SOURCE 1 reading this file should produce identical results to
SPIDER with -MESH_SOURCE 0 (default AW).

The Adams-Williamson density profile is:
    rho(r) = rhos * exp(beta * (R^2 - r^2) / 2)
simplified via pressure: rho = rhos - P * beta / g

The mass coordinate mapping uses a SNES solve in SPIDER; here we replicate
it with scipy.optimize.

File format (SI units):
    # <numpts_b> <numpts_s>
    r_b[0] P_b[0] rho_b[0] g_b[0]    (basic nodes, surface to CMB)
    ...
    r_s[0] P_s[0] rho_s[0] g_s[0]    (staggered nodes, surface to CMB)
    ...
"""

import argparse
import numpy as np


def aw_pressure(r, R, rhos, beta, g):
    """Adams-Williamson pressure at radius r.

    Parameters
    ----------
    r : float or array
        Radius [nondimensional or SI, must match R].
    R : float
        Planet radius.
    rhos : float
        Surface density.
    beta : float
        AW compressibility parameter [1/m in SI].
    g : float
        Surface gravity (negative).

    Returns
    -------
    P : float or array
        Pressure.
    """
    return -rhos * g / beta * (np.exp(beta * (R - r)) - 1.0)


def aw_density(P, rhos, beta, g):
    """Adams-Williamson density from pressure.

    Parameters
    ----------
    P : float or array
        Pressure.
    rhos : float
        Surface density.
    beta : float
        AW parameter.
    g : float
        Gravity (negative).

    Returns
    -------
    rho : float or array
        Density.
    """
    return rhos - P * beta / g


def aw_mass_within_radius(r, R, rhos, beta, g):
    """Mass integral from 0 to r (without 4*pi factor).

    This matches SPIDER's EOSAdamsWilliamson_GetMassWithinRadius.
    """
    P = aw_pressure(r, R, rhos, beta, g)
    rho = aw_density(P, rhos, beta, g)
    mass = (-2.0 / beta**3 - r**2 / beta - 2.0 * r / beta**2) * rho
    return mass


def aw_mass_within_shell(r_out, r_in, R, rhos, beta, g):
    """Mass within spherical shell (without 4*pi)."""
    return (aw_mass_within_radius(r_out, R, rhos, beta, g)
            - aw_mass_within_radius(r_in, R, rhos, beta, g))


def aw_average_density(R, R_core, rhos, beta, g):
    """Average density for mass coordinate mapping."""
    mass = aw_mass_within_shell(R, R_core, R, rhos, beta, g)
    return mass * 3.0 / (R**3 - R_core**3)


def radius_from_mass_coordinate(xi_targets, R, R_core, rhos, beta, g, rho_avg):
    """Solve for radius given mass coordinate targets.

    Replicates SPIDER's SNES solve for the xi -> r mapping.
    The mass coordinate definition is:
        xi^3 = R_core^3 + (3/rho_avg) * M(R_core, r)
    where M is mass within shell.

    Uses scalar Newton iteration (no scipy dependency). Each xi -> r
    equation is independent and monotonic, so convergence is guaranteed
    from the evenly-spaced initial guess.

    Parameters
    ----------
    xi_targets : array
        Target mass coordinates (surface to CMB).
    R, R_core : float
        Planet and core radii.
    rhos, beta, g : float
        AW parameters.
    rho_avg : float
        Average mantle density.

    Returns
    -------
    radii : array
        Corresponding physical radii.
    """
    n = len(xi_targets)
    radii = np.zeros(n)
    dx_init = (R - R_core) / max(n - 1, 1)

    for i in range(n):
        r = R - i * dx_init  # initial guess: evenly spaced
        for _ in range(100):
            mass = aw_mass_within_shell(r, R_core, R, rhos, beta, g)
            xi_comp = (mass * 3.0 / rho_avg + R_core**3) ** (1.0 / 3.0)
            residual = xi_comp - xi_targets[i]
            if abs(residual) < 1e-12:
                break
            # Numerical derivative via forward difference
            dr = max(abs(r) * 1e-8, 1e-2)
            mass_p = aw_mass_within_shell(r + dr, R_core, R, rhos, beta, g)
            xi_p = (mass_p * 3.0 / rho_avg + R_core**3) ** (1.0 / 3.0)
            dxi_dr = (xi_p - xi_comp) / dr
            if abs(dxi_dr) > 1e-30:
                r -= residual / dxi_dr
        radii[i] = r

    return radii


def main():
    parser = argparse.ArgumentParser(
        description="Generate SPIDER external mesh file from AW parameters"
    )
    parser.add_argument("-n", type=int, default=50,
                        help="Number of basic nodes (default: 50)")
    parser.add_argument("-radius", type=float, default=6371000.0,
                        help="Planet radius [m] (default: 6371000)")
    parser.add_argument("-coresize", type=float, default=0.55,
                        help="Core size fraction (default: 0.55)")
    parser.add_argument("-rhos", type=float, default=4078.95095544,
                        help="Surface density [kg/m^3]")
    parser.add_argument("-beta", type=float, default=1.1115348931000002e-07,
                        help="AW beta parameter [1/m]")
    parser.add_argument("-gravity", type=float, default=-10.0,
                        help="Surface gravity [m/s^2] (negative)")
    parser.add_argument("-o", "--output", type=str, required=True,
                        help="Output mesh file path")
    args = parser.parse_args()

    numpts_b = args.n
    numpts_s = numpts_b - 1
    R = args.radius
    R_core = args.coresize * R
    rhos = args.rhos
    beta = args.beta
    g = args.gravity

    rho_avg = aw_average_density(R, R_core, rhos, beta, g)

    # Build mass coordinate grid (surface to CMB, matching SPIDER's SetMeshRegular)
    # In SPIDER: xi goes from P->radius (surface) to P->radius*P->coresize (CMB)
    # dx_b = -R*(1-coresize)/(numpts_b-1) (negative)
    # xi_b[i] = R*coresize - (numpts_b-1-i)*dx_b = R*coresize + (numpts_b-1-i)*R*(1-coresize)/(numpts_b-1)
    # For i=0: xi_b[0] = R*coresize + (numpts_b-1)*R*(1-coresize)/(numpts_b-1) = R  (surface)
    # For i=numpts_b-1: xi_b[N-1] = R*coresize (CMB)
    dx = R * (1.0 - args.coresize) / (numpts_b - 1)
    xi_b = np.array([R - i * dx for i in range(numpts_b)])
    xi_s = np.array([R - 0.5 * dx - i * dx for i in range(numpts_s)])

    # Solve for radii from mass coordinates
    r_b = radius_from_mass_coordinate(xi_b, R, R_core, rhos, beta, g, rho_avg)
    r_s = radius_from_mass_coordinate(xi_s, R, R_core, rhos, beta, g, rho_avg)

    # Compute pressure, density, gravity at each node
    P_b = aw_pressure(r_b, R, rhos, beta, g)
    rho_b = aw_density(P_b, rhos, beta, g)
    # Gravity is uniform in AW (constant, negative)
    g_b = np.full(numpts_b, g)

    P_s = aw_pressure(r_s, R, rhos, beta, g)
    rho_s = aw_density(P_s, rhos, beta, g)
    g_s = np.full(numpts_s, g)

    # Write output file
    with open(args.output, "w") as f:
        f.write(f"# {numpts_b} {numpts_s}\n")
        for i in range(numpts_b):
            f.write(f"{r_b[i]:.15e} {P_b[i]:.15e} {rho_b[i]:.15e} {g_b[i]:.15e}\n")
        for i in range(numpts_s):
            f.write(f"{r_s[i]:.15e} {P_s[i]:.15e} {rho_s[i]:.15e} {g_s[i]:.15e}\n")

    print(f"Wrote {args.output}: {numpts_b} basic + {numpts_s} staggered nodes")
    print(f"  R = {R:.0f} m, R_core = {R_core:.0f} m")
    print(f"  rho_avg = {rho_avg:.6f} kg/m^3")
    print(f"  r_b range: [{r_b[-1]:.1f}, {r_b[0]:.1f}] m")
    print(f"  P_b range: [{P_b[0]:.3e}, {P_b[-1]:.3e}] Pa")


if __name__ == "__main__":
    main()
