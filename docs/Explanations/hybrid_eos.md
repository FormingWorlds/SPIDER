---
tags:
  - equation of state
  - EOS
  - thermodynamic consistency
---

# SPIDER: model overview

Here you can find a detailed overview of the SPIDER formulation.

!!! note 
    This model overview is taken from the [notes](https://github.com/FormingWorlds/SPIDER/tree/main/notes/) and contains an extended description of the equations and derivations related to the SPIDER code. It is still **work in progress.** 

## Hybrid equation of state from multiple data sources

We construct a pseudo self-consistent thermodynamic model using data from different sources. Typically data is expressed as functions of pressure $P$ only: $\rho(P)$, $\alpha(P)$, $c_p(P)$ for solid and melt phases, with constant $k$ and $\eta$. We also require liquidus and solidus curves and reference entropy of fusion $\Delta S_{\rm fus}$.

## General outline of approach

### Reference liquid adiabat

At reference pressure $P_0$, determine the liquidus temperature. Compute a reference liquid adiabat by integrating:

$$\left( \frac{dT}{dP} \right)_S = \frac{\alpha T}{c_p \rho}$$

where $S=S_0$ by definition. This is our reference liquid adiabat.

### Liquidus to entropy space

Map the liquidus from temperature to entropy space by measuring departure from the reference adiabat:

$$dS = \left( \frac{c_P}{T} \right) dT$$

$$\Delta S = \int_{T_1}^{T_{2}} \frac{c_P}{T} dT$$

where $T_1$ is temperature along reference adiabat and $T_2$ is liquidus temperature.

### Solidus curve

Repeat above steps for the solidus to obtain a solidus curve as entropy perturbation from a solid reference adiabat.

### Entropy of fusion

The entropy difference between liquidus and solidus is constrained by entropy of melting. For MgSiO3, entropy of melting is constant to within ~3% across Earth's mantle pressure range [^cite-SKS09].

Approaches:
1. Modeler prescribes $\Delta S_{\rm fus}$ directly at $P_0$
2. Modeler provides enthalpy $\Delta h$ at $P_0$: $\Delta S_{\rm fus} = \Delta h / T_0$
3. Integrate heat capacity in mixed phase region (complex, requires feedback from $\Delta S_{\rm fus}$)

### Mixed phase properties

Pin entropy difference between liquidus and solidus at reference pressure, assuming relatively constant with pressure. Compute all necessary quantities in mixed phase region:

$$T(P) = \frac{T_s + T_l}{2}$$

$$\rho(P) = \frac{1}{(1-\phi)/\rho_s + \phi/\rho_m}$$

$$C_P = C_{s,P}(1-\phi) + C_{m,P}\phi + \Delta S_{\rm fus} T$$

$$\alpha = (1-\phi)\alpha_s + \phi \alpha_m$$

$$\left( \frac{dT}{dP} \right)_S = \frac{\alpha T}{C_p \rho}$$

### Thermodynamic consistency

**Important issue**: Liquidus and solidus computed independently may not maintain constant entropy of fusion across pressure ranges. Liquidus can drop below solidus, which is nonsensical.

To enforce thermodynamic consistency, we must "tweak something":

1. **Adjust material properties** to get reasonable entropy of fusion while keeping liquidus/solidus fixed in temperature space
2. **Adjust melting curves** in entropy space while keeping material properties fixed, accepting mismatch to original temperature curves
3. **Combine both approaches** with systematic inversion

**Recommendation**: Request user specify only one melting curve bound (liquidus OR solidus) plus entropy of melting and temperature change at reference pressure. Calculate the other curve fully self-consistently.

### Temperature from entropy

For final use, our code requires temperature as function of entropy:

$$T(P) = T_{\rm ad}(P) \exp{ \left( \frac{\Delta S(P)}{c_P(P)} \right) }$$

where $T_{\rm ad}$ is reference adiabat temperature and $\Delta S$ is entropy perturbation from adiabat.

[^cite-SKS09]: Lars Stixrude; Nico de Koker; Ni Sun; Mainak Mookherjee; Bijaya B. Karki, *Thermodynamics of silicate liquids in the deep Earth*, Earth Planet. Sci. Lett., 2009.
