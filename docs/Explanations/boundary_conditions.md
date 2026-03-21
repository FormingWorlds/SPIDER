---
tags:
  - boundary conditions
  - surface flux
  - core-mantle boundary
---

# SPIDER: model overview

Here you can find a detailed overview of the SPIDER formulation.

!!! note 
    This model overview is taken from the [notes](https://github.com/FormingWorlds/SPIDER/tree/main/notes/) and contains an extended description of the equations and derivations related to the SPIDER code. It is still **work in progress.** 

## Surface radiative-interior flux balance

### Algebraic approach (preferred, implemented)

From energy balance, we balance the interior and geothermal heat flux at the surface:

$$J_{rad} = \epsilon \sigma (T_0^4 - T_{eqm}^4) = J_{tot} = J_{conv} + J_{cond}$$

where $T_0$ is surface temperature determined from surface entropy $S_0$.

The surface energy balance becomes:

$$\epsilon \sigma (T_0^4 - T_{eqm}^4) = -\rho_1 \kappa_{h1} T_0 \left. \left( \frac{\partial S}{\partial r} \right|_0 \right)$$

At each time step, we construct the entropy profile using the current solution and solve iteratively to determine the surface entropy gradient and surface entropy satisfying this boundary condition. This approach allows $J_{rad}$ to be imposed through any arbitrary relation since we do not require derivatives.

### Ultra-thin thermal boundary layer parameterisation

The thermal boundary layer at a magma ocean surface is expected to be very thin with large temperature drops. High resolution mesh is impractical for 2-D models. Therefore, we parameterise the temperature drop across the ultra-thin boundary layer.

From mixing length theory, heat flux is:

$$J_q = \rho c_p \kappa_{\rm h} \left[ \frac{\partial T}{\partial z}-\left( \frac{\partial T}{\partial z} \right)_s \right] + \rho c_p \kappa \frac{\partial T}{\partial z}$$

For viscous case [^cite-ABE93]:

$$\kappa_h = \frac{\alpha g l^4}{18 \nu} \left[ \frac{\partial T}{\partial z}-\left( \frac{\partial T}{\partial z} \right)_s \right]$$

We can rearrange to solve for $\partial T / \partial z$ with a root-finding algorithm:

$$\frac{J_q}{\rho c_p} - \kappa \frac{\partial T}{\partial z} - \kappa_h \left[ \frac{\partial T}{\partial z} - \left( \frac{\partial T}{\partial z} \right)_s \right] = 0$$

Integrating from a surface temperature downward gives the temperature profile. Plotting $\Delta T$ (temperature drop) versus $F_{\rm top}$ (surface heat flux) in log-log space yields a straight line:

$$\log(\Delta T) = A \log( F_{\rm top} ) + B$$

with $A \approx 3/4$. This gives:

$$\Delta T = c T_s^3$$

with constant $c=8.05154344{\rm E-08}$, providing a temperature drop estimate as a function of surface temperature.

### Lid formation

In 1-D, a high viscosity lid can form at the surface with thickness comparable to smallest mesh spacing. Since surface temperature falls through mixed phase region before interior regions, a thin impermeable lid develops that insulates the magma ocean. This behavior is unphysical and computationally expensive.

**Solution**: Use a constant mixing length (rather than distance-to-boundary definition) to allow more transport near surface, mitigating thin viscous lid formation.

### Foundering upper boundary layer

As magma ocean cools through the mixed phase, the rheological transition creates an insulating blanket at the surface. This introduces unphysical oscillations in total heat content as the stiff upper boundary layer alternately locks up, releases, and locks up again.

Standard mixing length theory successfully captures continuous foundering of cool material at the upper boundary. However, it fails for a solidified crust where phase contrast and rheological difference with underlying mantle create coherent structures that persist and remelt at depth.

## Core-mantle boundary

### Universal boundary condition

The core energy balance is:

$$\frac{dQ_c}{dt} = m_c c_c \frac{dT_{core}}{dt} = -A_{cmb} J_{cmb} + E_{in}$$

where $E_{in}$ is heat flux from core (including internal heating):

$$E_{in} = H_c m_c = J_{in} A_{cmb}$$

The time update for entropy gradient at CMB:

$$\frac{\Delta r}{2} \frac{d}{dt} \left( \left. \frac{dS}{dr} \right |_{cmb} \right) = (-E_{cmb}+E_{in}) \left( \frac{c_{cmb}}{c_c} \right) \left( \frac{1}{m_c \hat{T}_{core} T_{cmb}} \right) - \frac{dS_{-1}}{dt}$$

This enables three boundary conditions via choice of $E_{in}$:

1. **$E_{in}=0$**: CMB cools entirely by flux removed by magma ocean
2. **$E_{in}=\text{constant}$**: Constant heat flux from core buffers CMB cooling
3. **$E_{in}=E_{cmb}$**: Isothermal boundary condition (flux from core balances ocean cooling)

[^cite-ABE93]: Yutaka Abe, *Thermal Evolution and Chemical Differentiation of the Terrestrial Magma Ocean*, Evolution of the Earth and Planets, 1993.
