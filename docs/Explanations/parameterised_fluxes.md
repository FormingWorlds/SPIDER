---
tags:
  - mixing length theory
  - heat transport
  - convection
---

# SPIDER: model overview

Here you can find a detailed overview of the SPIDER formulation.

!!! note 
    This model overview is taken from the [notes](https://github.com/FormingWorlds/SPIDER/tree/main/notes/) and contains an extended description of the equations and derivations related to the SPIDER code. It is still **work in progress.** 

## Mixing length theory

Heat (and mass) transport for both the viscous (solid-state) and inviscid regime is parameterised using **mixing length theory**. The sensible heat flux is expressed as:

$$J_q = -\rho C_p \kappa \left( \frac{\partial T}{\partial r} \right)_S - \rho C_p \kappa_{\rm h}\Delta (\delta_r T)_S$$

where $\kappa$ is thermal diffusivity (conduction) and $\kappa_{\rm h}$ is eddy diffusivity (convection).

The heat-transport diffusivity is a piecewise function depending on the heat-transport regime:

$$\kappa_h= \begin{cases}
  \kappa & \text{if } \kappa_{\rm vis} \le \kappa \\
  \kappa_{\rm vis}  & \text{if } \kappa < \kappa_{\rm vis} < \nu \\
  \kappa_{\rm invis} & \text{if } \nu \leq \kappa_{\rm vis}
\end{cases}$$

In either regime, the appropriate diffusivity is:

$$\kappa_{\rm conv} \sim v_{\rm conv} l$$

where $l$ is the convective mixing length.

To remain consistent with the entropy-pressure formulation, we rewrite in terms of entropy gradients:

$$\Delta (\delta_r T)_S = \frac{T}{C_p} \frac{dS}{dr}$$

$$J_q =-\rho C_p \kappa \left( \frac{\partial T}{\partial P}\right)_S \frac{dP}{dr} - \rho \kappa_{\rm h} T \frac{dS}{dr}$$

## Velocity scalings

Convective velocities are given by:

$$v_{\rm vis} = \frac{\alpha |g| l^3}{18\nu}  \Delta(\delta_z T)_S$$

$$v_{\rm invis} = \sqrt{\frac{\alpha |g| l^2}{16}  \Delta(\delta_z T)_S}$$

### Viscous scaling

For the viscous case, we balance the buoyancy force on each fluid parcel against the viscous drag:

$$U = \frac{\alpha g l^3}{18 \nu} \left( \frac{dT}{dz} - \left( \frac{dT}{dz} \right)_{\rm s} \right)$$

### Inviscid scaling

For the inviscid case, kinetic energy of a fluid element is balanced by the work done by the buoyancy force:

$$v(x) = \sqrt{\alpha g x^2 \left( \frac{dT}{dz} - \left( \frac{dT}{dz} \right)_s \right)}$$

The average velocity is:

$$v_{\rm invis} = \sqrt{\frac{\alpha g l^2}{16} \left( \frac{dT}{dz} - \left( \frac{dT}{dz} \right)_s \right)}$$

## Kamata and Wagner profile

According to [^cite-K18] and [^cite-W19], the classical mixing length profile is not able to reproduce realistic results with deviations up to 60% from 3D simulations. The profile can be characterized by two parameters: depth $a$ and size $b$, for mantle thickness $D$.

### Kamata's results

[^cite-K18] finds that coefficients $a$ and $b$ depend on relative mantle size $f = R_{CMB}/R_{top}$ (about 0.55 for Earth) and viscosity contrast $\gamma = \ln (\eta_{top}/\eta_{bottom})$:

$$a,b = a_2,b_2 f^2 + a_1,b_1f + a_0,b_0$$

### Wagner et al.'s results

[^cite-W19] use a different parametrization in terms of $\alpha$ and $\beta$:

$$\alpha = \left( a_0 - a_1 \gamma - a_2 \log(\text{Ra}) \right) \tanh \left( a_3 \log (\text{Ra}/\text{Ra}_c) \right)$$

$$\beta = b_0 - b_1 \gamma - b_2 \log (\text{Ra})$$

for stagnant lid regime, or more complex expressions for mobile and sluggish lids. Values are given in their Table 4.

[^cite-W19]: Wang, Zaicong, *Earth’s volatile-element jigsaw*, Nat. Geosci., 2019.
[^cite-K18]: Shunichi Kamata, *One-dimensional convective thermal evolution calculation using a modified mixing length theory: Application to Saturnian icy satellites*, J. Geophys. Res., 2018.
