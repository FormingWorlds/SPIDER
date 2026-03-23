---
tags:
  - mass coordinates
  - coordinate transformation
  - hydrostatic pressure
---

# SPIDER: model overview

Here you can find a detailed overview of the SPIDER formulation.

!!! note 
    This model overview is taken from the [notes](https://github.com/FormingWorlds/SPIDER/tree/main/notes/) and contains an extended description of the equations and derivations related to the SPIDER code. It is still **work in progress.** 

## Mass coordinate definition

 [^cite-ABE95] defines:

$$\frac{4 \pi}{3} \rho_0 \xi^3 \equiv 4 \pi \int_0^r \rho r^2 dr = m$$

We similarly define, since we only consider the mantle bounded between $r_{\rm cmb}$ and $r$:

$$\frac{4 \pi}{3} \rho_0 (\xi^3-\xi_{\rm cmb}^3) \equiv 4 \pi \int_{\rm cmb}^r \rho r^2 dr = m$$

Taking the derivative with respect to $r$:

$$\rho_0 \xi^2 \frac{d \xi}{d r} = \rho r ^2$$

Integrating:

$$r(\xi) = \left[ r_{\rm cmb}^3 + 3 \int_{\xi_{\rm cmb}}^\xi \frac{\rho_0}{\rho(\xi)} \xi^2 d\xi \right]^\frac{1}{3}$$

Note that $\xi$ is referred to as a "mass coordinate" and has **length dimension**. This equation is the inverse transformation, allowing conversion between radius $r$ and mass coordinate $\xi$.

### Implementation

Currently, using the Adams-Williamson EOS we compute $\rho_0$ analytically using the same integration limits for $\xi$ and $r$, i.e., $\xi_{\rm surf}=r_{\rm surf}$ and $\xi_{\rm cmb}=r_{\rm cmb}$. Hence $\rho_0$ is the 'actual' average density of the mantle. We then prescribe a mesh using $\xi$; each $\xi$ corresponds to a shell containing mass $m$.

For the non-linear solution, it is natural to set the $\xi$ coordinate as the initial guess for the $r$ coordinate. The Jacobian of the objective function is simply the infinitesimal mass segment in physical coordinates $r^2 \rho(r)$.

## Partial derivatives

We compute the partial derivatives under the coordinate transformation from $r \rightarrow \xi$, with time $t$ remaining as the second variable:

$$\left( \frac{\partial}{\partial r} \right)_t = \left( \frac{\partial \xi}{\partial r} \right)_t \left( \frac{\partial}{\partial \xi} \right)_t = \frac{\rho}{\rho_0} \left( \frac{r}{\xi} \right)^2 \left(\frac{\partial}{\partial \xi} \right)_t$$

$$\left( \frac{\partial}{\partial t} \right)_r  = \left( \frac{\partial}{\partial t} \right)_\xi - U  \left( \frac{\partial}{\partial r} \right)_t$$

where $U$ is the local barycentric velocity in the radial direction.

### Implementation

We time step the following equation in SPIDER:

$$\rho T \left( \frac{\partial s}{\partial t} \right)_\xi = - \frac{\rho}{\rho_0 \xi^2} \left(\frac{\partial}{\partial \xi} \right)_t \left( r^2 \left[ \vec{J}_q + \Delta h (\vec{J}_m + \vec{J}_{cm}) \right] \right)$$

This description is known as the "Lagrangian description" [^cite-KWW12] because we are following mass elements.

#### Integral form

[^cite-BSW18] instead solve the integral form:

$$\int_V \rho T \left( \frac{\partial s}{\partial t} \right)_\xi dV = - \int_A F \cdot n dA + \int_V \rho H dV$$

#### Fluxes

Heat flux becomes:

$$\vec{J}_q=-\rho T \kappa_h \frac{\partial S}{\partial r} = -\rho T \kappa_h \frac{\rho}{\rho_0} \left( \frac{r}{\xi} \right)^2 \left(\frac{\partial S}{\partial \xi} \right)_t$$

## Hydrostatic pressure

We use the Adams-Williamson equation of state to compute the hydrostatic pressure profile.

### Pressure

Adams-Williamson equation of state:

$$P = - \frac{\rho_r g}{\beta} (\exp( \beta z )-1)$$

where $\rho_r$ is reference surface density, $g$ gravity, $\beta$ compressibility, and $z$ is depth.

Pressure gradient:

$$\frac{dP}{dr} = \rho_s g \exp( \beta z )$$

Density is:

$$\rho(r) = \rho_s \exp( \beta (r_0 - r) )$$

For any such EOS with a simple relation between $\rho$ and $r$, we can integrate to directly compute the mass coordinate $\xi$ for a given $r$:

$$\xi = \left[ \xi_{\rm cmb}^3 + \frac{3}{\rho_0} \int_{\rm cmb}^r \rho r^2 dr \right] ^ {1/3}$$

An intuitive option is to set $\rho_0$ such that $\xi=1.0$ at the planetary surface, with $\xi=0$ at the innermost boundary.

### General formulation

$$\frac{dp(r)}{dr} = g(r) \rho(r) = -G \frac{M(r)}{r^2}\rho(r)$$

Multiply by $r^2/\rho$ and differentiate with respect to $r$:

$$\frac{1}{r^2} \frac{d}{dr} \left( \frac{r^2}{\rho}\frac{dp}{dr} \right) = -4 \pi G \rho$$

Combined with an EOS of the form $p=p(\rho)$, this is an ordinary second order differential equation for the density or pressure.

[^cite-ABE95]: Yutaka Abe, *Basic equations for evolution of partially molten mantle and core*, The Earth's Central Part: Its Structure and Dynamics, 1995.
[^cite-KWW12]: Rudolf Kippenhahn; Alfred Weigert; Achim Weiss, *Stellar Structure and Evolution*, Springer, 2012.
[^cite-BSW18]: Dan J. Bower; Patrick Sanan; Aaron S. Wolf, *Numerical solution of a non-linear conservation law applicable to the interior dynamics of partially molten planets*, Phys. Earth Planet. Inter., 2018.
