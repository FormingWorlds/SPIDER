# SPIDER

<p align="center">
  <img src="docs/assets/spider.png" style="max-width:40%; height:auto;" alt="SPIDER logo">
</p>

<p align="center">
  <a href="https://www.gnu.org/licenses/gpl-3.0"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="License"></a>
  <a href="https://proteus-framework.org/SPIDER/"><img src="https://img.shields.io/github/actions/workflow/status/FormingWorlds/SPIDER/docs.yaml?branch=main&label=Docs" alt="Docs"></a>
  <a href="https://app.codecov.io/gh/FormingWorlds/SPIDER"><img src="https://img.shields.io/codecov/c/github/FormingWorlds/SPIDER/main?label=coverage&logo=codecov" alt="codecov"></a>
  <a href="https://github.com/FormingWorlds/SPIDER/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/FormingWorlds/SPIDER/ci.yml?branch=main&label=Unit%20Tests" alt="Unit Tests"></a>
  <a href="https://github.com/FormingWorlds/SPIDER/actions/workflows/nightly.yml"><img src="https://img.shields.io/github/actions/workflow/status/FormingWorlds/SPIDER/nightly.yml?branch=main&label=Integration%20Tests" alt="Integration Tests"></a>
</p>

**Simulating Planetary Interior Dynamics with Extreme Rheology.**

SPIDER is an interior thermal-evolution module of the [PROTEUS](https://proteus-framework.org/PROTEUS) coupled atmosphere-interior framework. It is a 1-D parameterised interior dynamics code that solves the entropy evolution (Bower et al. 2018) of a rocky planet's mantle on a staggered finite-difference mesh, integrated in time with SUNDIALS through PETSc. It handles coexisting melt and solid across the whole mantle, volatile cycling, redox reactions, and a parameterised coupling to an outgassed atmosphere.

SPIDER runs standalone for magma-ocean studies, or as a subprocess of PROTEUS, where each coupling step it reads the surface boundary condition from the atmosphere module and returns the interior state through a JSON output contract.

## Quick start

```bash
git clone https://github.com/FormingWorlds/SPIDER.git
cd SPIDER
./tools/get_spider.sh                                # installs a pinned PETSc, then builds the spider binary
./spider -options_file tests/opts/blackbody50.opts   # a first run
```

See the [installation guide](https://proteus-framework.org/SPIDER/How-to/installation.html) for the manual PETSc route, quadruple-precision builds, and cluster setup, and the [first-run tutorial](https://proteus-framework.org/SPIDER/Tutorials/first_run.html) for a walkthrough with plots.

## Documentation

Full documentation is at **[proteus-framework.org/SPIDER](https://proteus-framework.org/SPIDER/)**, including:

- [Getting started](https://proteus-framework.org/SPIDER/getting_started.html): the quickest path from a clone to a first model.
- [How-to guides](https://proteus-framework.org/SPIDER/How-to/installation.html): install, test, build robust tests, supply an [external mesh](https://proteus-framework.org/SPIDER/How-to/external_mesh_input.html), [couple to PROTEUS](https://proteus-framework.org/SPIDER/How-to/proteus_coupling.html), and release.
- [Reference](https://proteus-framework.org/SPIDER/Reference/options.html): the runtime options generated from the source, and the publication list.
- [Explanations](https://proteus-framework.org/SPIDER/Explanations/basic_thermodynamics.html): thermodynamics, mass and energy transport, material properties, boundary conditions, the hybrid equation of state, and the numerical schemes.
- [Validation anchors](https://proteus-framework.org/SPIDER/Validation/index.html): the per-source inventory of reference-pinned tests, each tied to a published benchmark, an analytical limit, or an independent cross-check.

## Part of PROTEUS

SPIDER is the C, PETSc-based interior module of the [PROTEUS](https://proteus-framework.org/PROTEUS) framework for coupled atmosphere-interior evolution of rocky planets and exoplanets. Its sibling interior module, [ARAGOG](https://proteus-framework.org/aragog/), solves the same entropy evolution in a Python and JAX implementation and serves as an independent cross-check; [Zalmoxis](https://proteus-framework.org/Zalmoxis/) can supply SPIDER with an external structural mesh for non-Earth-like compositions.

## Citation

If you use SPIDER in published work, please cite the methods papers below; the metadata is in [CITATION.cff](CITATION.cff) and the full list is on the [Publications page](https://proteus-framework.org/SPIDER/Reference/publications.html).

- Bower, D.J., Sanan, P., & Wolf, A.S. (2018). *Numerical solution of a non-linear conservation law applicable to the interior dynamics of partially molten planets.* **Phys. Earth Planet. Inter.** 274, 49-62. [\[DOI\]](https://doi.org/10.1016/j.pepi.2017.11.004) [\[arXiv\]](https://arxiv.org/abs/1711.07303)
- Wolf, A.S., & Bower, D.J. (2018). *An equation of state for high pressure-temperature liquids (RTpress) with application to MgSiO3 melt.* **Phys. Earth Planet. Inter.** 278, 59-74. [\[DOI\]](https://doi.org/10.1016/j.pepi.2018.02.004)
- Bower, D.J., Kitzmann, D., Wolf, A.S., Sanan, P., Dorn, C., & Oza, A.V. (2019). *Linking the evolution of terrestrial interiors and an early outgassed atmosphere to astrophysical observations.* **Astron. Astrophys.** 631, A103. [\[DOI\]](https://doi.org/10.1051/0004-6361/201935710) [\[arXiv\]](https://arxiv.org/abs/1904.08300)
- Bower, D.J., Hakim, K., Sossi, P.A., & Sanan, P. (2022). *Retention of water in terrestrial magma oceans and carbon-rich early atmospheres.* **Planet. Sci. J.** 3, 93. [\[DOI\]](https://doi.org/10.3847/PSJ/ac5fb1) [\[arXiv\]](https://arxiv.org/abs/2110.08029)

If your configuration uses the PALEOS equation-of-state tables (for example an external structural mesh from [Zalmoxis](https://proteus-framework.org/Zalmoxis/) built on them), please also cite:

- Attia, M., Lichtenberg, T., Jungová, E., & Sastre, M. (2026). *PALEOS: Multiphase Equations of State and Mass-Radius Relations for Exoplanet Interiors.* [\[ADS\]](https://ui.adsabs.harvard.edu/abs/2026arXiv260503741A/abstract) [\[arXiv\]](https://arxiv.org/abs/2605.03741)

## License

[GNU General Public License v3.0](COPYING). SPIDER is part of the [PROTEUS framework](https://proteus-framework.org/).
