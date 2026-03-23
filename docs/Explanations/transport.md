---
tags:
  - mass conservation
  - energy transport
---
# SPIDER: model overview

!!! note 
    This model overview is taken from the [notes](https://github.com/FormingWorlds/SPIDER/tree/main/notes/) and contains an extended description of the equations and derivations related to the SPIDER code. It is still **work in progress.** 

## Conservation of mass

### Eulerian form

$$
\frac{\partial \rho}{\partial t} + \nabla \cdot (\rho \vec{U}) = 0
$$

### Lagrangian form

For example, Eq. A1 in [^cite-ABE95]:

$$
\frac{D \rho}{Dt} + \rho \nabla \cdot \vec{U} = 0
$$

### Material derivative

$$
\frac{D}{Dt} \equiv \frac{\partial}{\partial t} + \vec{U} \cdot \nabla
$$

where $\rho$ is density, $\vec{U}$ is velocity, and $t$ is time. There are no sources or sinks of mass for global mass conservation.

---

## Barycentric velocity

The total number of moles in a unit volume, $n_t$, is obtained by summing the contributions of the **number of moles per unit volume** of each species, $n_i$:

$$
n_t = \sum_i n_i
$$

The density of the fluid is given by summing the partial densities of all species:

$$
\rho = \sum_i \rho_i
$$

where

$$
\rho_i = n_i \mathcal{M}_i
$$

and $\mathcal{M}_i$ is the molecular weight of species $i$.

The molecular weight of the mixture is

$$
\overline{\mathcal{M}} = \sum_i x_i \mathcal{M}_i
$$

where $x_i = n_i / n_t$ is the mole fraction of species $i$. Therefore the density of the mixture is

$$
\rho = n_t \overline{\mathcal{M}}
$$

The mass fraction of species $i$, $\omega_i$, is

$$
\omega_i = \frac{\rho_i}{\rho} = \frac{n_i \mathcal{M}_i}{\rho}
$$

The absolute molar flux of species $i$ with respect to a **fixed spatial coordinate** is

$$
n_i \vec{U}_i
$$

Hence the mass flux of species $i$ with respect to a **fixed spatial coordinate** is

$$
\vec{J}_i^\ast = n_i \mathcal{M}_i \vec{U}_i = \rho \omega_i \vec{U}_i = \rho_i \vec{U}_i
$$

The mass-weighted average velocity of the fluid, $\vec{U}$, also known as the stream velocity or **barycentric velocity**, is

$$
\rho \vec{U} = \sum_i \vec{J}_i^\ast = \sum_i \rho_i \vec{U}_i
$$

so that

$$
\vec{U}
= \frac{1}{\rho} \sum_i \rho_i \vec{U}_i
= \frac{1}{\rho} \sum_i n_i \mathcal{M}_i \vec{U}_i
= \sum_i \omega_i \vec{U}_i
$$

The velocity of species $i$ **relative to the barycentric velocity** (sometimes called the diffusion or streaming velocity) is

$$
\vec{u}_i = \vec{U}_i - \vec{U}
$$

We can now define the **relative** or **diffusion flux vector**:

$$
\vec{J}_i = \rho_i (\vec{U}_i - \vec{U}) = \rho_i \vec{u}_i
$$

Note that the mass-weighted average of the diffusion velocity is zero:

$$
\begin{aligned}
\frac{1}{\rho} \sum_i \rho_i \vec{u}_i
&= \frac{1}{\rho} \sum_i \rho_i \vec{U}_i
 - \frac{1}{\rho} \sum_i \rho_i \vec{U} \\
&= \frac{1}{\rho} (\rho \vec{U}) - \frac{\vec{U}}{\rho}(\rho) \\
&= 0
\end{aligned}
$$

Consequently,

$$
\sum_i \vec{J}_i = \sum_i \rho_i \vec{u}_i = 0
$$

---

## Eulerian description with barycentric velocity

Conservation of species $i$ in terms of moles per unit volume:

$$
\frac{\partial n_i}{\partial t} + \nabla \cdot (n_i \vec{U}_i) = \dot{M}_i
$$

where $\dot{M}_i$ is the net molar production of species $i$ per unit volume by chemical reaction.

Equivalently,

$$
\frac{\partial \rho_i}{\partial t} + \nabla \cdot \vec{J}_i^\ast = \rho \dot{w}_i
$$

where the chemical source function $\dot{w}_i$ represents the mass rate of production of species $i$ by chemical reaction **per unit mass** and may be determined from chemical kinetics. Here $\vec{J}_i^\ast$ is relative to a fixed reference frame.

Substitute for $\vec{J}_i^\ast$ using the definitions above to eliminate $\vec{U}_i$:

$$
\frac{\partial \rho_i}{\partial t} + \nabla \cdot \rho_i (\vec{U} + \vec{u}_i) = \rho \dot{w}_i
$$

Expand $\nabla$ and substitute $\rho_i = \rho \omega_i$:

$$
\frac{\partial (\rho \omega_i)}{\partial t}
+ \nabla \cdot (\rho \omega_i \vec{U})
+ \nabla \cdot (\rho_i \vec{u}_i)
= \rho \dot{w}_i
$$

Substitute $\vec{J}_i = \rho_i \vec{u}_i$:

$$
\begin{aligned}
\frac{\partial (\rho \omega_i)}{\partial t} + \nabla \cdot (\rho \omega_i \vec{U})
&= - \nabla \cdot \vec{J}_i + \rho \dot{w}_i \\
\rho \frac{\partial \omega_i}{\partial t}
+ \omega_i \frac{\partial \rho}{\partial t}
+ \rho \omega_i \nabla \cdot \vec{U}
+ \vec{U} \cdot \nabla (\rho \omega_i)
&= - \nabla \cdot \vec{J}_i + \rho \dot{w}_i
\end{aligned}
$$

Global mass conservation gives

$$
\frac{\partial \rho}{\partial t}
= - \nabla \cdot (\rho \vec{U})
= -\rho \nabla \cdot \vec{U} - \vec{U} \cdot \nabla \rho
$$

Substitute this into the previous equation:

$$
\rho \frac{\partial \omega_i}{\partial t}
- \omega_i \vec{U} \cdot \nabla \rho
+ \vec{U} \cdot \nabla (\rho \omega_i)
= - \nabla \cdot \vec{J}_i + \rho \dot{w}_i
$$

Expand the remaining gradient:

$$
\vec{U} \cdot \nabla(\rho \omega_i)
= \omega_i \vec{U} \cdot \nabla \rho + \rho \vec{U} \cdot \nabla \omega_i
$$

Therefore,

$$
\rho \frac{\partial \omega_i}{\partial t}
+ \rho \vec{U} \cdot \nabla \omega_i
= - \nabla \cdot \vec{J}_i + \rho \dot{w}_i
$$

---

## Lagrangian description with barycentric velocity

Use the material derivative, where $\vec{U}$ is the center-of-mass velocity, or equivalently the velocity of a fluid element moving with the local barycenter:

$$
\frac{D}{Dt} \equiv \frac{\partial}{\partial t} + \vec{U} \cdot \nabla
$$

Substituting into the previous equation gives

$$
\rho \frac{D \omega_i}{Dt} = - \nabla \cdot \vec{J}_i + \rho \dot{w}_i
$$

This agrees with Eq. A2 in [^cite-ABE95].

---

## Melt transport with barycentric velocity

Analogous to chemical species transport, we can consider the evolution of melt fraction $\phi$ (Eq. 2 in [^cite-ABE95]), where $\phi$ is melt fraction, $\vec{J}_m$ is the mass flux of melt **with respect to local barycentric motion** (the motion of the local barycenter of a fluid element composed of a melt--solid mixture), and $M$ is the melting rate per unit mass.

When we consider an $n$-component system, only $n-1$ equations are independent because the sum of mass fractions is unity. Therefore, for the simple case of a melt--solid mixture (two components), we only need one equation for melt fraction.

For a mixture of melt and solid, the **barycentric velocity** $\vec{U}$ is

$$
\vec{U} = \phi \vec{U}_m + (1-\phi)\vec{U}_s
$$

where $\vec{U}_m$ and $\vec{U}_s$ are the velocities of the melt and solid phases, respectively.

Now consider the fluxes:

$$
\begin{aligned}
\vec{J}_m &= \rho \phi (\vec{U}_m - \vec{U}) = -\vec{J}_s \\
\vec{J}_s &= \rho (1-\phi)(\vec{U}_s - \vec{U}) = -\vec{J}_m
\end{aligned}
$$

where $\vec{J}_m$ and $\vec{J}_s$ are the mass fluxes of melt and solid, respectively, **relative to the barycenter**.

Since the mass flux of melt or solid is caused by the differential motion of the solid and melt phases, the mass flux is given as a function of the relative velocity between the phases and melt fraction. Eliminating $\vec{U}$ using the barycentric-velocity expression:

$$
\vec{J}_m = -\vec{J}_s = \rho \phi (1-\phi)(\vec{U}_m - \vec{U}_s)
$$

---

## Melt and chemical species transport

Following [^cite-ABE95], introduce $i$ components, which are chemical species that we wish to track, and let each component exist in either the melt or solid phase. Then we have two equations describing the mass fraction of each component in the melt and solid phases:

$$
\rho \frac{D}{Dt}(\phi \omega_{mi}) = -\nabla \cdot \vec{J}_{mi} + \rho M_i,
\qquad i = 1,\dots,n
$$

$$
\rho \frac{D}{Dt}((1-\phi)\omega_{si}) = -\nabla \cdot \vec{J}_{si} - \rho M_i,
\qquad i = 1,\dots,n
$$

where $\omega_{mi}$, $\omega_{si}$, $\vec{J}_{mi}$, and $\vec{J}_{si}$ are the mass fraction and mass flux of component $i$ in the melt and solid phases, respectively, and $M_i$ is the mass melting rate of chemical component $i$ per unit mass.

From the definition of mass flux relative to the barycenter, $\vec{J}_{mi}$ and $\vec{J}_{si}$ are

$$
\begin{aligned}
\vec{J}_{mi}
&= \rho \phi \omega_{mi}(\vec{U}_{mi} - \vec{U}) \\
&= \rho \phi \omega_{mi}(\vec{U}_{mi} - \vec{U}_m + \vec{U}_m - \vec{U}) \\
&= \rho \phi \omega_{mi}(\vec{U}_{mi} - \vec{U}_m)
 + \rho \phi \omega_{mi}(\vec{U}_m - \vec{U}) \\
&= \vec{j}_{mi} + \omega_{mi}\vec{J}_m
\end{aligned}
$$

and

$$
\begin{aligned}
\vec{J}_{si}
&= \rho (1-\phi)\omega_{si}(\vec{U}_{si} - \vec{U}) \\
&= \rho (1-\phi)\omega_{si}(\vec{U}_{si} - \vec{U}_s + \vec{U}_s - \vec{U}) \\
&= \rho (1-\phi)\omega_{si}(\vec{U}_{si} - \vec{U}_s)
 + \rho (1-\phi)\omega_{si}(\vec{U}_s - \vec{U}) \\
&= \vec{j}_{si} + \omega_{si}\vec{J}_s \\
&= \vec{j}_{si} - \omega_{si}\vec{J}_m
\end{aligned}
$$

where

$$
\vec{j}_{mi} \equiv \rho \phi \omega_{mi}(\vec{U}_{mi} - \vec{U}_m),
\qquad
\vec{j}_{si} \equiv \rho (1-\phi)\omega_{si}(\vec{U}_{si} - \vec{U}_s)
$$

The quantities $\vec{j}_{mi}$ and $\vec{j}_{si}$ are the mass fluxes of component $i$ in the melt and solid phases, respectively, **caused by mechanisms other than melt--solid relative motion**.

Now add the two conservation equations above, use the expressions for $\vec{J}_{mi}$ and $\vec{J}_{si}$, and introduce the mass fraction of component $i$ in the mixture:

$$
\rho \frac{D\omega_i}{Dt}
= -\nabla \cdot \left[ (\omega_{mi} - \omega_{si})\vec{J}_m + \vec{j}_{mi} + \vec{j}_{si} \right]
$$

with

$$
\omega_i \equiv \phi \omega_{mi} + (1-\phi)\omega_{si},
\qquad i = 1,\dots,n
$$

Since the sum of mass fractions is unity, only $n-1$ equations are independent.

Next consider the case in which solid and melt phases are in chemical equilibrium:

$$
\left( \frac{\omega_{si}}{\omega_{mi}} \right)_{\text{at equilibrium}} = K_{ei}
$$

Then the previous equation can be rewritten as

$$
\rho \frac{D \omega_i}{Dt}
= - \nabla \cdot \left[
\frac{1-K_{ei}}{\phi_e + (1-\phi_e)K_{ei}} \omega_i \vec{J}_m
+ \vec{j}_{mi} + \vec{j}_{si}
\right]
$$

where $\phi_e$ is the melt fraction at equilibrium.

We can approximate the convective mass transport by turbulent diffusion in a vigorously convecting layer. Then the vertical mass flux of component $i$ due to convection is given by Fick's law:

$$
\vec{j}_{mi} = -\kappa_c \rho \frac{\partial (\phi \omega_{mi})}{\partial r},
\qquad
\vec{j}_{si} = -\kappa_c \rho \frac{\partial \bigl((1-\phi)\omega_{si}\bigr)}{\partial r}
$$

where $\omega_{mi}$, $\omega_{si}$, and $\kappa_c$ are the mass fraction of component $i$ within melt and solid phases, and the eddy diffusivity for convective mass transport, respectively.

Then the net convective transport is

$$
\vec{j}_{mi} + \vec{j}_{si}
= -\kappa_c \rho \frac{\partial \omega_i}{\partial r}
$$

So we can express the transport equation as having two right-hand-side contributions: the first due to melt--solid relative motion, and the second due to other mechanisms.

---

## Energy transport

Eq. 27 in [^cite-ABE95]:

$$
\rho T \frac{Ds}{Dt}
=
-\nabla \cdot \left[
\vec{J}_q
+ \Delta h \, \vec{J}_m
+ \sum_{i=1}^n \left(h_{mi}\vec{j}_{mi} + h_{si}\vec{j}_{si}\right)
\right]
$$

Now analyze the last term on the right-hand side:

$$
\begin{aligned}
\sum_{i=1}^n (h_{mi}\vec{j}_{mi} + h_{si}\vec{j}_{si})
&= -\kappa_c \rho \sum_{i=1}^n
\left(
h_{mi}\frac{\partial (\phi \omega_{mi})}{\partial r}
+
h_{si}\frac{\partial \bigl((1-\phi)\omega_{si}\bigr)}{\partial r}
\right) \\
&= -\kappa_c \rho \sum_{i=1}^n
\left[
(h_{mi}\omega_{mi} - h_{si}\omega_{si})\frac{\partial \phi}{\partial r}
+ h_{mi}\phi \frac{\partial \omega_{mi}}{\partial r}
+ h_{si}(1-\phi)\frac{\partial \omega_{si}}{\partial r}
\right] \\
&= -\kappa_c \rho \sum_{i=1}^n
\left[
(h_{mi}\omega_{mi} - h_{si}\omega_{si})\frac{\partial \phi}{\partial r}
\right] \\
&= -\kappa_c \rho \, \Delta h \, \frac{\partial \phi}{\partial r}
\equiv \Delta h \, \vec{J}_{cm}
\end{aligned}
$$

The convective (phase) mixing term can probably be incorporated into the heat flux if we modify the form of $\kappa_h$, or possibly if we decompose the velocities relative to the barycenter differently. Rather than considering one term associated with melt--solid separation and another separate term, both might be wrapped into a single formulation. Combining with the convective heat flux seems most sensible, since these are two terms, opposite in sign for $dS_{\text{liq}}/dr < 0$, that nearly cancel.

The precision issue arises because this cancellation disappears for $dS_{\text{liq}}/dr > 0$, and hence $dS/dr$ is driven to a tiny value.

[^cite-ABE95]: Yutaka Abe, *Basic equations for evolution of partially molten mantle and core*, The Earth's Central Part: Its Structure and Dynamics, 1995.
