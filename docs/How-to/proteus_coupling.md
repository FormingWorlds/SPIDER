# Coupling to PROTEUS

SPIDER is the C, PETSc-based interior module of the [PROTEUS](https://proteus-framework.org/PROTEUS) framework. PROTEUS does not link SPIDER as a library: it runs the compiled `spider` binary as a subprocess once per interior sub-step and exchanges data through the command-line options it passes in and the JSON files SPIDER writes out. The whole contract is therefore the runtime options (documented on the [options reference](../Reference/options.md)) and the JSON output layout described below. Keeping that contract stable is what lets PROTEUS pin a specific SPIDER commit and evolve the two codes independently.

The PROTEUS side lives in `src/proteus/interior_energetics/spider.py`.

## How PROTEUS invokes SPIDER

Each interior step, `RunSPIDER` assembles an argument list and calls `spider` with `subprocess.run`. The binary is located at `<spider_checkout>/spider`; output is written to the run's `output/data/` directory. The options set on every call include:

| Option | Source | Meaning |
|---|---|---|
| `-outputDirectory` | run directory | where SPIDER writes its per-step JSON files |
| `-IC_INTERIOR` | `1` fresh, `2` restart | fresh start, or continue from the previous step's JSON |
| `-surface_bc_value` | atmosphere module | surface heat flux `F_atm` (the upper boundary condition) |
| `-teqm` | orbit / star | equilibrium temperature |
| `-OXYGEN_FUGACITY_offset` | config | fO<sub>2</sub> shift relative to the buffer, for the redox reactions |
| `-n`, `-nstepsmacro`, `-dtmacro` | config | mesh resolution and the macro-step schedule for this sub-step |
| `-radius`, `-gravity`, `-coresize`, `-grain` | structure | planet geometry and grain size |
| `-tsurf_poststep_change` | config tolerance | stop the sub-step once the surface temperature has moved by this much |

On a restart (`-IC_INTERIOR 2`) PROTEUS additionally passes `-ic_interior_filename` (the most recent JSON), `-activate_poststep`, and `-activate_rollback` so SPIDER resumes from the archived state and can roll a failed macro step back.

### The retry ladder

A single interior sub-step can fail if the solver cannot make progress at the requested tolerance and step size. `RunSPIDER` retries up to eight times, shrinking the step-size factor (times 0.3) and loosening the absolute tolerance (times 5) on each attempt, and only raises an error once every attempt is exhausted. A non-zero binary exit code, a timeout, or an unreadable output file each count as a failed attempt.

## The JSON output contract

SPIDER writes one JSON file per macro step to `<outputDirectory>/<time_years>.json`. Physical fields are stored as *dimensionalisable* objects carrying three keys:

- `values`: the non-dimensional number(s);
- `scaling`: the multiplier that returns SI units;
- `units`: the SI unit string.

PROTEUS reconstructs the SI value by multiplying `values` by `scaling`; the same convention is used by the test suite's SI reconstruction helpers. Node-centred arrays follow SPIDER's staggered mesh: fields suffixed `_b` live on the basic (cell-boundary) nodes and fields suffixed `_s` on the staggered (cell-centre) nodes.

At the end of a sub-step, `ReadSPIDER` loads the last JSON file and takes:

- the full-precision `time_years` (not the rounded filename, which would lose sub-year precision and desynchronise the coupled clock);
- scalars: liquid, solid, mantle, and core masses; the surface temperature; the global melt fraction and rheological-front depth; and the interior heat flux `Fatm`;
- arrays for the radiogenic and tidal heating integrals (`Hradio_s`, `Htidal_s`, `mass_s`, `area_b`) and for the interior profiles PROTEUS carries forward (`phi_s`, `rho_s`, `radius_b`, `visc_b`, `temp_s`, `pressure_s`, `S_s`, `volume_s`).

Any change to these field names, their units, or their scalings is a breaking change for the coupling and warrants a SPIDER release (see [Releasing](releasing.md)).

## External structural mesh

By default SPIDER builds its own mesh from the Adams-Williamson equation of state. When PROTEUS runs the [Zalmoxis](https://proteus-framework.org/Zalmoxis/) structure solver, it instead supplies a precomputed radial mesh and passes `-MESH_SOURCE 1 -mesh_external_filename <path>`. PROTEUS derives the core size from the mesh itself, and, when the structure is recomputed mid-run, blends successive meshes and remaps the entropy field onto the new nodes so the restart stays consistent. The mesh file format is described on the [external mesh input](external_mesh_input.md) page.

## Version pinning

PROTEUS pins SPIDER by commit, not by release tag. The pin lives in the PROTEUS `pyproject.toml`:

```toml
[tool.proteus.modules.spider]
url = "https://github.com/FormingWorlds/SPIDER.git"
ref = "<commit sha>"
```

`tools/get_spider.sh` in PROTEUS clones and builds that commit. To adopt a new SPIDER version on the PROTEUS side, cut a SPIDER release, then open a PROTEUS pull request that bumps `ref` and run the PROTEUS interior smoke tests against it. Because the exchange is entirely through the command-line options and the JSON contract above, a pin bump is safe whenever those are unchanged.
