---
tags:
  - numerical methods
  - finite element
  - well-balanced schemes
---

# SPIDER: model overview

Here you can find a detailed overview of the SPIDER formulation.

!!! note 
    This model overview is taken from the [notes](https://github.com/FormingWorlds/SPIDER/tree/main/notes/) and contains an extended description of the equations and derivations related to the SPIDER code. It is still **work in progress.** 

## Finite element method representation of toy model

### Analytical form

Following [^cite-BSW18], the weak form of the toy model. Energy conservation is:

$$- \nabla \cdot \vec{F} = 0$$

Flux is:

$$\vec{F} = - \kappa_h (2 \nabla S - \nabla S_{\rm liq})$$

where $\nabla S_{\rm liq}$ is the gradient of the melting curve (liquidus). The eddy diffusivity for 1-D geometry is:

$$\kappa_h= \begin{cases}
  \frac{1}{64}\sqrt{-\nabla S \cdot \hat{r}} & \text{for } \nabla S \cdot \hat{r}<0 \\
  0 & \text{for } \nabla S \cdot \hat{r} \ge 0
\end{cases}$$

Objective: determine $S$ (or $\nabla S$) for prescribed non-zero $F$.

### Weak form

Multiply energy equation by test function $v$ and integrate over domain $\Omega$:

$$\int_\Omega \vec{F} \cdot \nabla v dx = \int_\Omega f v dx - \int_{\partial \Omega} \vec{F} \cdot \hat{n} v ds$$

For nonlinear Poisson equation form with $q(u) = -\kappa_h$:

$$\int_\Omega \left( -\kappa_h \nabla \tilde{S} \right) \cdot \nabla v dx = \int_\Omega f v dx - \int_{\Gamma_N} g v ds$$

where Neumann boundary condition is:

$$\kappa_h \nabla \tilde{S} \cdot \hat{n} = g$$

Standard form $a(u,v)=L(v)$:

$$a(u,v) = \int_\Omega -\kappa_h \nabla u \cdot \nabla v dx$$

$$L(v) = \int_\Omega f v dx - \int_{\Gamma_N} g v ds$$

## Variable substitution approach

The convective and mixing fluxes often nearly cancel. Define adjusted variable:

$$S = (1/2)S^{\rm liq} + \bar S + C$$

where $C$ is chosen to shift entropy closer to liquidus. By construction:

$$2S_r - S^{\rm liq}_r = 2\bar S_r$$

Then:

$$F = \kappa_h((1/2)S^{\rm liq}_r + \bar S_r) (2 \bar S_r)$$

This eliminates the obvious cancellation. Additionally:

$$\frac{\partial S}{\partial t} = \frac{\partial \bar S}{\partial t}$$

However, this approach requires $\frac{d S_{liq}}{dr} = \frac{d S_{sol}}{dr}$ in the full model, which may be overly restrictive.

## Well-balanced scheme approach

A well-balanced scheme defines an equilibrium state that is exactly recovered to machine precision. Define and solve for equilibrium entropy profile that gives constant heat flux from surface boundary condition:

$$F_{eqm} = F(S_{eqm}(r)) = F_{top}$$

Decompose entropy into equilibrium plus perturbation:

$$S(r,t) = S_{eqm}(r) + \delta S(r,t)$$

By construction, when $\delta S=0$:

$$F(r,t) = F(S_{eqm}(r)) = F_{top}$$

The evolution equation for the toy model [^cite-BSW18]:

$$\frac{\partial S}{\partial t} = - \frac{\partial F}{\partial r}$$

becomes:

$$\frac{\partial (\delta S)}{\partial t} = - \frac{\partial (\delta F)}{\partial r}$$

where flux perturbation is:

$$\delta F(S(r,t)) = F(S(r,t)) - F(S_{eqm}(r))$$

By construction, $-\partial F(S_{eqm})/\partial r = 0$, simplifying to:

$$\frac{\partial (\delta S)}{\partial t} = -\frac{\partial (\delta F)}{\partial r}$$

### Key features of well-balanced approach

- **Equilibrium state**: Entropy profile giving constant flux is exactly recovered to machine precision when perturbations vanish
- **Flexibility**: Can remesh equilibrium state periodically as surface flux decays with time
- **Nonlinearity retained**: RHS preserves full nonlinear flux form; equilibrium only ensures gradient is zero
- **Recovery**: Total entropy $S$ and flux $F$ trivially recovered by addition

### Comparison: variable substitution vs well-balanced

**Variable substitution**: 
- Simpler conceptually but requires $dS_{liq}/dr = dS_{sol}/dr$ (restrictive)
- Implicitly includes mixing flux always

**Well-balanced scheme**:
- More complex but more flexible
- No restrictive conditions on melting curves
- Emphasis on perturbations may improve numerical stability

[^cite-BSW18]: Dan J. Bower; Patrick Sanan; Aaron S. Wolf, *Numerical solution of a non-linear conservation law applicable to the interior dynamics of partially molten planets*, Phys. Earth Planet. Inter., 2018.
