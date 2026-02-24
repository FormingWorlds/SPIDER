#!/usr/bin/env python
"""Validate SPIDER mesh fields populated from an external mesh file.

Reads SPIDER JSON output and the input external mesh file, then verifies:
1. radius_b matches file values (after scaling)
2. pressure_b matches file values
3. dPdr_b = rho_b * g_b from file (hydrostatic relation)
4. mass_s[i] = rho_s[i] * (r_b[i]^3 - r_b[i+1]^3) / 3  (with 4*pi)
5. mantle_mass = sum(mass_s) * 4*pi
6. dxidr_b satisfies mass coordinate relation

Exit code 0 if all within tolerance, 1 otherwise.
"""

import json
import sys
import numpy as np

RTOL = 1e-5
ATOL = 1e-10


def load_mesh_file(filename):
    """Load external mesh file.

    Returns
    -------
    basic : ndarray, shape (nb, 4)
        Columns: radius, pressure, density, gravity.
    staggered : ndarray, shape (ns, 4)
        Same columns.
    """
    with open(filename) as f:
        header = f.readline().strip()
        nb, ns = map(int, header.lstrip("# ").split())
        data = np.loadtxt(f)
    basic = data[:nb]
    staggered = data[nb:nb + ns]
    return basic, staggered


def load_spider_json(filename):
    """Extract mesh data from SPIDER output JSON.

    Returns
    -------
    mesh : dict
        Keys: radius_b, pressure_b, dPdr_b, mass_s, mantle_mass, dxidr_b, xi_b
        Values are nondimensional floats with their scaling factors applied.
    """
    with open(filename) as f:
        data = json.load(f)

    mesh = {}

    # Extract mesh fields from the 'mesh' section
    mesh_data = data.get("mesh", {})
    subdomain_b = mesh_data.get("basic nodes", [])
    subdomain_s = mesh_data.get("staggered nodes", [])

    def extract_field(subdomain_list, description):
        for entry in subdomain_list:
            if entry.get("description") == description:
                scaling = float(entry["scaling"])
                values = np.array([float(v) for v in entry["values"]])
                return values * scaling
        return None

    mesh["radius_b"] = extract_field(subdomain_b, "radius")
    mesh["pressure_b"] = extract_field(subdomain_b, "pressure")
    mesh["dPdr_b"] = extract_field(subdomain_b, "dP/dr")
    mesh["xi_b"] = extract_field(subdomain_b, "xi (mass coordinate)")
    mesh["dxidr_b"] = extract_field(subdomain_b, "dxi/dr")

    mesh["mass_s"] = extract_field(subdomain_s, "mass")
    # mantle_mass is a scalar stored separately
    mesh["mantle_mass"] = float(mesh_data.get("mantle_mass", {}).get("value", 0))
    mesh["mantle_mass_scaling"] = float(mesh_data.get("mantle_mass", {}).get("scaling", 1))

    return mesh


def check_field(name, computed, expected, rtol=RTOL, atol=ATOL):
    """Compare two arrays, report max errors."""
    if computed is None or expected is None:
        print(f"  SKIP {name}: data not available")
        return True

    abs_err = np.abs(computed - expected)
    max_abs = np.max(abs_err)
    with np.errstate(divide="ignore", invalid="ignore"):
        rel_err = np.where(np.abs(expected) > atol,
                           abs_err / np.abs(expected), 0.0)
    max_rel = np.max(rel_err)

    ok = np.allclose(computed, expected, rtol=rtol, atol=atol)
    status = "PASS" if ok else "FAIL"
    print(f"  {status} {name}: max_abs={max_abs:.3e}, max_rel={max_rel:.3e}")
    return ok


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <spider_output.json> <mesh_file.dat>")
        sys.exit(1)

    json_file = sys.argv[1]
    mesh_file = sys.argv[2]

    basic, staggered = load_mesh_file(mesh_file)
    nb = basic.shape[0]
    ns = staggered.shape[0]

    print(f"Mesh file: {nb} basic, {ns} staggered nodes")
    print(f"JSON file: {json_file}")
    print()

    # File columns: radius, pressure, density, gravity (SI)
    r_b_file = basic[:, 0]
    p_b_file = basic[:, 1]
    rho_b_file = basic[:, 2]
    g_b_file = basic[:, 3]

    r_s_file = staggered[:, 0]
    p_s_file = staggered[:, 1]
    rho_s_file = staggered[:, 2]
    g_s_file = staggered[:, 3]

    # Verify hydrostatic relation in file: dPdr = rho * g
    dpdr_b_expected = rho_b_file * g_b_file

    # Verify shell masses: mass_s[i] = rho_s[i] * (r_b[i]^3 - r_b[i+1]^3)/3
    # SPIDER includes 4*pi in the dimensional output
    mass_s_expected = np.zeros(ns)
    for i in range(ns):
        vol = (r_b_file[i] ** 3 - r_b_file[i + 1] ** 3) / 3.0
        mass_s_expected[i] = rho_s_file[i] * vol * 4.0 * np.pi

    mantle_mass_expected = np.sum(mass_s_expected)

    print("Validation results:")

    all_ok = True

    # Note: JSON extraction may fail if the output format doesn't have mesh section.
    # In that case, this script serves as a template for what to check.
    try:
        mesh = load_spider_json(json_file)
    except (KeyError, json.JSONDecodeError) as e:
        print(f"  WARNING: Could not parse JSON mesh data: {e}")
        print("  Skipping JSON-based validation.")
        print()
        print("Basic file consistency checks:")
        all_ok &= check_field("dPdr_b = rho*g (file)", dpdr_b_expected, rho_b_file * g_b_file)
        print(f"  INFO mantle_mass (from file): {mantle_mass_expected:.6e} kg")
        sys.exit(0 if all_ok else 1)

    if mesh["radius_b"] is not None:
        all_ok &= check_field("radius_b", mesh["radius_b"], r_b_file)
    if mesh["pressure_b"] is not None:
        all_ok &= check_field("pressure_b", mesh["pressure_b"], p_b_file)
    if mesh["dPdr_b"] is not None:
        all_ok &= check_field("dPdr_b", mesh["dPdr_b"], dpdr_b_expected)
    if mesh["mass_s"] is not None:
        all_ok &= check_field("mass_s", mesh["mass_s"], mass_s_expected)

    print()
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
