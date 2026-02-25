#!/usr/bin/env python
"""Validate SPIDER mesh fields populated from an external mesh file.

Reads SPIDER JSON output and the input external mesh file, then verifies:
1. radius_b matches file values (after scaling)
2. pressure_b matches file values
3. dPdr_b = rho_b * g_b from file (hydrostatic relation)
4. mass_s[i] = rho_s[i] * (r_b[i]^3 - r_b[i+1]^3) / 3  (with 4*pi)
5. mantle_mass = sum(mass_s) * 4*pi
6. dxidr_b satisfies mass coordinate relation

SPIDER JSON format: fields are in the "data" section with names like
"radius_b", "pressure_b", etc. Each is {"scaling": X, "values": [...]}.
The "atmosphere" section contains "mass_mantle".

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


def get_json_field(section, name):
    """Extract a dimensionalized array from SPIDER JSON.

    Parameters
    ----------
    section : dict
        A JSON sub-object (e.g. data["data"]).
    name : str
        Field name (e.g. "radius_b").

    Returns
    -------
    ndarray or None
        Values multiplied by scaling factor, or None if field absent.
    """
    field = section.get(name)
    if field is None:
        return None
    scaling = float(field["scaling"])
    values = np.array(field["values"], dtype=float)
    return values * scaling


def load_spider_json(filename):
    """Extract mesh data from SPIDER output JSON.

    Returns
    -------
    mesh : dict
        Keys: radius_b, pressure_b, dPdr_b, mass_s, mantle_mass, dxidr_b, xi_b
        Values are SI (scaling applied).
    """
    with open(filename) as f:
        raw = json.load(f)

    data_section = raw["data"]
    atmos_section = raw["atmosphere"]

    mesh = {}
    mesh["radius_b"] = get_json_field(data_section, "radius_b")
    mesh["pressure_b"] = get_json_field(data_section, "pressure_b")
    mesh["dPdr_b"] = get_json_field(data_section, "dPdr_b")
    mesh["xi_b"] = get_json_field(data_section, "xi_b")
    mesh["dxidr_b"] = get_json_field(data_section, "dxidr_b")
    mesh["radius_s"] = get_json_field(data_section, "radius_s")
    mesh["mass_s"] = get_json_field(data_section, "mass_s")

    # mantle_mass is a scalar in the atmosphere section
    mm = get_json_field(atmos_section, "mass_mantle")
    mesh["mantle_mass"] = float(mm[0]) if mm is not None else None

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

    rho_s_file = staggered[:, 2]

    # Expected dPdr from hydrostatic relation: dP/dr = rho * g
    # (gravity is already negative in the file, so dPdr < 0)
    dpdr_b_expected = rho_b_file * g_b_file

    # Expected shell masses: mass_s[i] = 4*pi * rho_s[i] * (r_b[i]^3 - r_b[i+1]^3)/3
    mass_s_expected = np.zeros(ns)
    for i in range(ns):
        vol = (r_b_file[i] ** 3 - r_b_file[i + 1] ** 3) / 3.0
        mass_s_expected[i] = rho_s_file[i] * vol * 4.0 * np.pi

    mantle_mass_expected = np.sum(mass_s_expected)

    # Load SPIDER JSON output
    mesh = load_spider_json(json_file)

    print("Validation results:")
    all_ok = True

    # 1. Radius matches input file
    all_ok &= check_field("radius_b", mesh["radius_b"], r_b_file)

    # 2. Pressure matches input file
    all_ok &= check_field("pressure_b", mesh["pressure_b"], p_b_file)

    # 3. dPdr matches hydrostatic relation (rho * g from file)
    all_ok &= check_field("dPdr_b = rho*g", mesh["dPdr_b"], dpdr_b_expected)

    # 4. Shell masses match expected
    all_ok &= check_field("mass_s", mesh["mass_s"], mass_s_expected)

    # 5. Mantle mass matches sum of shell masses
    if mesh["mantle_mass"] is not None:
        mm_ok = np.isclose(mesh["mantle_mass"], mantle_mass_expected,
                           rtol=RTOL, atol=ATOL)
        status = "PASS" if mm_ok else "FAIL"
        rel = abs(mesh["mantle_mass"] - mantle_mass_expected) / mantle_mass_expected
        print(f"  {status} mantle_mass: json={mesh['mantle_mass']:.6e}, "
              f"expected={mantle_mass_expected:.6e}, rel={rel:.3e}")
        all_ok &= mm_ok
    else:
        print("  SKIP mantle_mass: not found in JSON")

    # 6. dxidr satisfies mass coordinate relation:
    #    dxi/dr = (rho / rho_avg) * (r / xi)^2
    if (mesh["dxidr_b"] is not None and mesh["xi_b"] is not None
            and mesh["radius_b"] is not None):
        r_b = mesh["radius_b"]
        xi_b = mesh["xi_b"]
        # rho_avg = mantle_mass / (4/3 * pi * (r_surface^3 - r_cmb^3))
        vol_mantle = 4.0 / 3.0 * np.pi * (r_b[0] ** 3 - r_b[-1] ** 3)
        if mesh["mantle_mass"] is not None and vol_mantle > 0:
            rho_avg = mesh["mantle_mass"] / vol_mantle
            # Avoid division by zero at boundaries where xi might be 0
            valid = xi_b > 0
            dxidr_expected = np.where(
                valid,
                (rho_b_file / rho_avg) * (r_b / xi_b) ** 2,
                mesh["dxidr_b"]  # use actual value where xi=0
            )
            all_ok &= check_field("dxidr_b (mass coord)", mesh["dxidr_b"],
                                  dxidr_expected, rtol=1e-4)
        else:
            print("  SKIP dxidr_b: cannot compute rho_avg")
    else:
        print("  SKIP dxidr_b: fields not available")

    print()
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
