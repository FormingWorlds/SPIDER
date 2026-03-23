# External mesh input

SPIDER can accept a pre-computed mesh from an external file instead of computing one internally from the Adams-Williamson equation of state. This enables coupling with structure solvers like [Zalmoxis](https://proteus-framework.org/Zalmoxis) that provide more accurate density profiles for non-Earth-like compositions.

## 1. Enable external mesh mode

Set these options when running SPIDER:

| Option | Type | Description |
|--------|------|-------------|
| `-MESH_SOURCE` | `int` | `0` (default): internal AW mesh. `1`: read from external file. |
| `-mesh_external_filename` | `string` | Path to external mesh file (required when `MESH_SOURCE=1`). |

## 2. Prepare the mesh file

The mesh file is plain text (SI units), ordered from surface to CMB.

```text
# <num_basic_nodes> <num_staggered_nodes>
r_b[0] P_b[0] rho_b[0] g_b[0]      (surface)
r_b[1] P_b[1] rho_b[1] g_b[1]
...
r_b[nb-1] P_b[nb-1] rho_b[nb-1] g_b[nb-1]  (CMB)
r_s[0] P_s[0] rho_s[0] g_s[0]      (staggered)
...
r_s[ns-1] P_s[ns-1] rho_s[ns-1] g_s[ns-1]
```

!!! note "Rules"
    - Columns are: radius [m], pressure [Pa], density [kg/m$^3$], gravity [m/s$^2$]
    - Ordering is surface (largest radius) to CMB (smallest radius)
    - Gravity should be negative (inward)
    - `ns = nb - 1`
    - First line starts with `#` and contains `nb` and `ns`

## 3. Quick example

```bash
# From SPIDER root
python tests/generate_aw_mesh.py -n 50 -o mesh.dat
./spider -options_file tests/opts/blackbody50.opts -MESH_SOURCE 1 -mesh_external_filename mesh.dat
```

!!! info "EOS out-of-range"
    With EOS lookup tables such as WolfBower2018, SPIDER issues a **one-time warning per table and direction** when pressure or entropy lies outside the tabulated range; subsequent out-of-range queries are silently clamped.

    If the thermal expansion coefficient alpha becomes negative near table boundaries, it is reset to zero with a warning to prevent NaNs in the mixing length theory.

