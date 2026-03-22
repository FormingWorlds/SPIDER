---
tags:
  - radiogenic heating
  - radionuclides
  - internal heat
---

# SPIDER: model overview

Here you can find a detailed overview of the SPIDER formulation.

!!! note 
    This model overview is taken from the [notes](https://github.com/FormingWorlds/SPIDER/tree/main/notes/) and contains an extended description of the equations and derivations related to the SPIDER code. It is still **work in progress.** 

## Radioactive heating

The concentration $X_i$ of a given isotope $i$ is [^cite-TS14]:

$$X_i(t_\mathrm{age})= X_{i0} \exp{\left( \frac{t_\mathrm{age} \ln2}{T_{i1/2}} \right)}$$

where $X_{i0}$ is present-day concentration, $t_\mathrm{age}$ is age (time before present), and $T_{i1/2}$ is half-life.

With $t_{i0}$ as the time at which the concentration is known (e.g., 4.54 Gyrs for present-day):

$$X_i(t) = X_{i0} \exp{\left( \frac{(t_{i0}-t) \ln2}{T_{i1/2}} \right)}$$

The heat production rate for isotope $i$ is:

$$H_i(t)=H_i x_{i0} C_0 \exp{\left( \frac{(t_{i0}-t) \ln2}{T_{i1/2}} \right)}$$

where $x_{i0}$ is the fractional isotopic abundance and $C_0$ is the elemental concentration.

### Radionuclides

Key radionuclides relevant for planetary heating:

| Isotope | T$_{1/2}$ (Myr) | $x_{i0}$ | $H_i$ (W/kg) |
|---------|-----------------|---------|-------------|
| $^{26}$Al | 0.717 | 0 | 0.3583 |
| $^{40}$K | 1248 | $1.1668\times10^{-4}$ | $2.8761\times10^{-5}$ |
| $^{60}$Fe | 2.62 | 0 | $3.6579\times10^{-2}$ |
| $^{232}$Th | 14000 | 1 | $2.6368\times10^{-5}$ |
| $^{235}$U | 704 | 0.0072045 | $5.68402\times10^{-4}$ |
| $^{238}$U | 4468 | 0.9927955 | $9.4946\times10^{-5}$ |

Total heating rate is the sum:

$$H(t) = \sum_i H_i(t)$$

Note that [^cite-RUE17] computes bulk element power ensuring internal consistency.

[^cite-TS14]: Turcotte, D.; Schubert, G., *Geodynamics*, Cambridge University Press, 2014.
[^cite-RUE17]: Thomas Ruedas, *Radioactive heat production of six geologically important nuclides*, Geochem. Geophy. Geosys., 2017.
