---
tags:
  - thermodynamics
  - entropy
  - multi-component
---

# SPIDER: model overview

Here you can find a detailed overview of the SPIDER formulation.

>**Note:** This model overview is taken from the [notes](https://github.com/FormingWorlds/SPIDER/notes) and contains an extended description of the equations and derivations related to the SPIDER code [@BSW18]. It is still **work in progress.** 

## Thermodynamic energy transport and enthalpy fluxes {#sect:thermodynamic}

**Goal:** Understand the origin of the energy transport associated with the enthalpy of chemical/phase components. This derives the energy equation for a multi-component system that appears in the appendix of [@ABE95].

In the following section, I combine the notation from [@DM62] and [@ABE95] so beware of notation changes compared to the original papers. Where a choice can be made, I typically stick to the notation of [@ABE95].

## Conservation and entropy balance

Conservation of mass fraction ([@DM62 Eq. II.13], also [@ABE95 Eq. A2]), *where $i$ is a thermodynamic (chemical) component and $j$ refers to a reaction*:

$$
\rho \frac{D \omega_i}{Dt} = -\nabla \cdot \vec{J}_i + \rho \sum_{j=1}^r \nu_{ij} \mathcal{J}_j \qquad (i=1,\ n)
\tag{1}\label{eq:ABE95_A2}
$$

Here I define $\mathcal{J}_j$ as the rate of reaction $j$ per unit mass (same as $w_j$ in [@ABE95] but this notation may be confused with mass fraction $\omega$ which is why I change the symbol). [@ABE95] defines $\nu_{ij}$ as the mass of component $i$ formed by reaction $j$. Note that [@DM62] use slightly different definitions of these quantities, since they define $\mathcal{J}$ as a mass per unit volume and unit time and omit the leading $\rho$ term.

Entropy balance ([@DM62 Eq. III.12], also [@ABE95 Eq. A4]):

$$
\rho \frac{Ds}{Dt} = - \nabla \cdot \vec{J}_s + \sigma
\tag{2}\label{eq:DM62_ch3_eq12}
$$

where the entropy flux $\vec{J}_s$ is the difference between the total entropy flux $\vec{J}_{s,\ tot}$ and a convective term $\rho s v$ ([@DM62 Eq. III.13]):

$$
\vec{J}_s = \vec{J}_{s,\ tot} - \rho s v
\tag{3}
$$

The entropy balance, *excluding viscous dissipation and external forces*, is ([@DM62 Eq. III.19]):

$$
\rho \frac{Ds}{Dt} = - \nabla \cdot \left( \frac{\vec{J}_q - \sum_i \mu_i \vec{J}_i}{T} \right)
- \frac{1}{T^2} \vec{J}_q \cdot \nabla T
- \frac{1}{T} \sum_{i=1}^n \vec{J}_i \cdot T \nabla \left( \frac{\mu_i}{T} \right)
- \frac{\rho}{T} \sum_{i=1}^n \sum_{j=1}^r \nu_{ij} \mu_i \mathcal{J}_j
\tag{4}
$$

Where entropy flux is ([@DM62 Eq. III.20]):

$$
\vec{J}_s = \frac{1}{T} \left( \vec{J}_q - \sum_{i=1}^n \mu_i \vec{J}_i \right)
\tag{5}
$$

and entropy production is ([@DM62 Eq. III.21]):

$$
\sigma =
- \frac{1}{T^2} \vec{J}_q \cdot \nabla T
- \frac{1}{T} \sum_{i=1}^n \vec{J}_i \cdot T \nabla \left( \frac{\mu_i}{T} \right)
- \frac{\rho}{T} \sum_{i=1}^n \sum_{j=1}^r \nu_{ij} \mu_i \mathcal{J}_j
\tag{6}
$$

By using the thermodynamic relation ([@DM62 Eq. III.23]):

$$
T d \left( \frac{\mu_i}{T} \right) = \left( d \mu_i \right)_T - \frac{h_i}{T} dT
\tag{7}
$$

we can define a new flux as ([@DM62 Eq. III.24]):

$$
\vec{J}_q^\prime = \vec{J}_q - \sum_{i=1}^n h_i \vec{J}_i
\tag{8}\label{eq:Jqprime}
$$

*Eq. $\ref{eq:Jqprime}$ is the definition of heat flux used by [@ABE95] and therefore it removes the energetic contribution associated with the transport of enthalpy by the components. This term then reappears as an entropy source term, since of course the physics must remain the same!*

Then entropy flow is ([@DM62 Eq. III.26], also [@ABE95 Eq. A5]):

$$
\vec{J}_s = \frac{1}{T} \vec{J}_q^\prime + \sum_{i=1}^n s_i \vec{J}_i
\tag{9}\label{eq:DM62_ch3_eq26}
$$

where $s_i = -(\mu_i-h_i)/T$ is the partial specific entropy of component $i$. Written in this way the entropy flux contains the heat flow $\vec{J}_q^\prime$ and a transport of partial entropies with respect to the barycentric velocity $v$.

The entropy production associated with this definition can be written as ([@DM62 Eq. III.25], also [@ABE95 Eq. A6]):

$$
\sigma =
- \frac{1}{T^2} \vec{J}_q^\prime \cdot \nabla T
- \frac{1}{T} \sum_{i=1}^n \vec{J}_i \cdot \left( \nabla \mu_i \right)_T
- \frac{\rho}{T} \sum_{i=1}^n \sum_{j=1}^r \nu_{ij} \mu_i \mathcal{J}_j
\tag{10}\label{eq:DM62_ch3_eq25}
$$

### Quoted from [@DM62]

> “It is clear that the difference between $\vec{J}_q$ and $\vec{J}_q^\prime$ (Eq. $\ref{eq:Jqprime}$) represents a transfer of heat due to diffusion. Therefore the quantity $\vec{J}_q^\prime$ also represents an irreversible heat flow. In fact in diffusing mixtures the concept of heat flow can be defined in different ways. Obviously a different definition of the notion of heat flux leaves all physical results unchanged. But to any particular choice corresponds a special form of the entropy production $\sigma$. It is a matter of expediency which choice is the most suitable in a particular application of the theory. The freedom of defining the heat flow in various ways, of which the possibility was indicated here in the framework of a macroscopic treatment, exists also in the microscopic theories of transport phenomena in mixtures.”

Abe chooses to model $J_q^\prime$ as a convective heat flux using mixing length theory. In this regard, [@ABE95 Eq. 47] excludes the energetic contribution of the enthalpy transport of the components (but remember it appears later in Abe's formulation). Now, using the above equations we can derive [@ABE95 Eq. A10] using several vector identities:

$$
\begin{aligned}
\rho \frac{Ds}{Dt}
&= -\nabla \cdot \left(  \frac{1}{T} \vec{J}_q^\prime + \sum_{i=1}^n s_i \vec{J_i} \right) + \sigma \\
&= - \frac{1}{T} \nabla \cdot \vec{J}_q^\prime
+ \frac{1}{T^2} \vec{J}_q^\prime \cdot \nabla T
- \sum_{i=1}^n \nabla s_i \cdot \vec{J}_i
- \sum_{i=1}^n s_i \nabla \cdot \vec{J}_i
+ \sigma
\end{aligned}
\tag{11}
$$

Sub in $\sigma$ (Eq. $\ref{eq:DM62_ch3_eq25}$) and immediately see that the $1/T^2$ term cancels leaving:

$$
\rho \frac{Ds}{Dt}
= - \frac{1}{T} \nabla \cdot \vec{J}_q^\prime
- \sum_{i=1}^n \nabla s_i \cdot \vec{J}_i
- \sum_{i=1}^n s_i \nabla \cdot \vec{J}_i
- \frac{1}{T} \sum_{i=1}^n \vec{J}_i \cdot (\nabla \mu_i)_T
- \frac{\rho}{T} \sum_{i=1}^n \sum_{j=1}^r \nu_{ij} \mu_i \mathcal{J}_j
\tag{12}
$$

Now use Eq. $\ref{eq:ABE95_A2}$ to eliminate the chemical reaction term:

$$
\rho \frac{Ds}{Dt}
= - \frac{1}{T} \nabla \cdot \vec{J}_q^\prime
- \sum_{i=1}^n \nabla s_i \cdot \vec{J}_i
- \sum_{i=1}^n s_i \nabla \cdot \vec{J}_i
- \frac{1}{T} \sum_{i=1}^n \vec{J}_i \cdot (\nabla \mu_i)_T
- \frac{1}{T} \sum_{i=1}^n \left( \mu_i \rho \frac{D\omega_i}{Dt} +\mu_i \nabla \cdot \vec{J}_i \right)
\tag{13}
$$

Collect terms. *[@ABE95] missing $\rho$ on the RHS*:

$$
\rho \frac{Ds}{Dt}
= - \frac{1}{T} \nabla \cdot \vec{J}_q^\prime
- \sum_{i=1}^n \nabla \cdot (s_i \vec{J}_i )
- \frac{1}{T} \sum_{i=1}^n \nabla \cdot (\mu_i \vec{J}_i)
- \frac{\rho}{T} \sum_{i=1}^n \mu_i  \frac{D\omega_i}{Dt}
\tag{14}
$$

Now use $h_i = \mu_i + T s_i$:

$$
\rho \frac{Ds}{Dt}
= - \frac{1}{T} \nabla \cdot \vec{J}_q^\prime
- \frac{1}{T} \sum_{i=1}^n \nabla \cdot (h_i \vec{J}_i )
- \frac{\rho}{T} \sum_{i=1}^n \mu_i  \frac{D\omega_i}{Dt}
\tag{15}
$$

Leading to [@ABE95 Eq. A10], *[@ABE95 Eq. A10] missing $\rho$*:

$$
\boxed{
\rho \frac{Ds}{Dt}
= - \frac{1}{T} \nabla \cdot \left( \vec{J}_q^\prime + \sum_{i=1}^n h_i \vec{J}_i \right)
- \frac{\rho}{T} \sum_{i=1}^n \mu_i  \frac{D\omega_i}{Dt}
}
\tag{16}
$$

How [@ABE95 Eq. 4] is derived from this point is confusing. It appears that if you literally swap out components and replace them with phases, where the two phases are melt and solid, you can reproduce [@ABE95 Eq. 4]. But then later, [@ABE95] states that this equation must be “modified for multi-component systems, because energy transport due to mass transport must be taken into account”. He then goes onto to derive the following equation, which makes sense based on [@ABE95 Eq. A10]. The transport of thermodynamic components can be divided between a melt and solid phase. *This is how the notion of phases is introduced into the formulation.*

## Introducing phases (melt / solid)

The transport of thermodynamic components can be divided between a melt and solid phase:

$$
\sum_{i=1}^n h_i\vec{J}_i
= \sum_{i=1}^n h_i^m \vec{J}_i^m + h_i^s \vec{J}_i^s
\tag{17}
$$

where $h_i^m$ and $h_i^s$ are the partial specific enthalpy of component $i$ in melt and solid phases, respectively.

Now recognise that the following holds, since we can split the flux into a part relative to the velocity of the melt:

$$
\begin{aligned}
\vec{J}_i^m
&= \rho \phi \omega_i^m (\vec{U}_i^m - \vec{U} )\\
&= \rho \phi \omega_i^m (\vec{U}_i^m - \vec{U}_{m} + \vec{U}_m - \vec{U} )\\
&= \rho \phi \omega_i^m (\vec{U}_i^m - \vec{U}_{m} ) + \rho \phi \omega_i^m ( \vec{U}_m - \vec{U} )\\
&= \vec{j}_i^m + \omega_i^m \vec{J}_m
\end{aligned}
\tag{18}\label{eq:J_mi}
$$

and similarly:

$$
\begin{aligned}
\vec{J}_i^s
&= \rho (1-\phi) \omega_i^s (\vec{U}_i^s - \vec{U} )\\
&= \rho (1-\phi) \omega_i^s (\vec{U}_i^s - \vec{U}_s + \vec{U}_s - \vec{U} )\\
&= \rho (1-\phi) \omega_i^s (\vec{U}_i^s - \vec{U}_s) + \rho (1-\phi) \omega_i^s (\vec{U}_{s} - \vec{U})\\
&= \vec{j}_i^s + \omega_i^s \vec{J}_s\\
&= \vec{j}_i^s - \omega_i^s \vec{J}_m
\end{aligned}
\tag{19}\label{eq:J_si}
$$

where $\omega_i^m$, $\omega_i^s$, $\vec{J}_i^m$, and $\vec{J}_i^s$ are the mass fraction and mass flux of component $i$ in melt and solid phases, respectively. $\vec{j}_i^m$ and $\vec{j}_i^s$ are the mass fluxes of component $i$ in melt and solid phases, respectively, caused by mechanisms other than melt–solid relative motion.

Substitute in Eqs. $\ref{eq:J_mi}$ and $\ref{eq:J_si}$:

$$
\sum_{i=1}^n h_i\vec{J}_i
= \sum_{i=1}^n h_i^m \vec{J}_i^m + h_i^s \vec{J}_i^s
= \sum_{i=1}^n h_i^m \left( \vec{j}_i^m + \omega_i^m \vec{J}_m \right)
+ h_i^s \left( \vec{j}_i^s - \omega_i^s \vec{J}_m \right)
\tag{20}
$$

and collect terms:

$$
\begin{aligned}
\sum_{i=1}^n h_i\vec{J}_i
&= \vec{J}_m \sum_{i=1}^n \left( h_i^m \omega_i^m - h_i^s \omega_i^s \right)
+ \sum_{i=1}^n h_i^m \vec{j}_i^m + h_i^s \vec{j}_i^s\\
&= \vec{J}_m \left( h^m - h^s \right)
+ \sum_{i=1}^n h_i^m \vec{j}_i^m + h_i^s \vec{j}_i^s\\
&= \Delta h \vec{J}_m
+ \sum_{i=1}^n h_i^m \vec{j}_i^m + h_i^s \vec{j}_i^s
\end{aligned}
\tag{21}
$$

This is helpful because the gravitational separation term (first term) can be parameterised simply based on Stokes' law. The second term within the summation ultimately becomes the “mixing term” (see below), which represents energy transport due to mechanisms other than relative melt–solid separation.

## Two-phase entropy equation

For two phases ($n=2$) and $J_m=-J_s$, *[@ABE95 Eq. 4] missing $\rho$*:

$$
\boxed{
\rho \frac{Ds}{Dt}
= - \frac{1}{T} \nabla \cdot \left( \vec{J}_q^\prime + (h_m-h_s) \vec{J}_m \right)
- \frac{\rho}{T} (\mu_m-\mu_s) \frac{D\phi}{Dt}
}
\tag{22}\label{eq:entropy_twophase}
$$

Note this contains a latent heat ($\Delta h$) associated with melt–solid separation ($\vec{J}_m$). At chemical equilibrium, which we always assume, $\mu_m=\mu_s$ and hence the last term is zero.

Now, for multi-component systems, energy transport due to mass transport must be taken into account (*[@ABE95 Eq. 20] missing $\rho$*):

$$
\begin{aligned}
\rho \frac{Ds}{Dt}
&= -\frac{1}{T} \nabla \cdot \left[ \vec{J}_q^\prime + \Delta h \vec{J}_m + \sum_{i=1}^n (h_{mi} \vec{j}_{mi} + h_{si} \vec{j}_{si} ) \right]\\
&\quad -\frac{\rho}{T} \left[ \Delta \mu \frac{D\phi}{Dt} + \sum_{i=1}^n \left( \phi \mu_{mi}\frac{D\omega_{mi}}{Dt} + (1-\phi) \mu_{si} \frac{D\omega_{si}}{Dt} \right) \right]
\end{aligned}
\tag{23}
$$

Under the assumption of chemical equilibrium, the final term of Eq. $\ref{eq:entropy_twophase}$ is zero. We then arrive at the fundamental equation that we solve in the SPIDER code:

$$
\boxed{
\rho \frac{Ds}{Dt}
= - \frac{1}{T} \nabla \cdot \left( \vec{J}_q^\prime + (h_m-h_s) \vec{J}_m \right)
}
\tag{24}\label{eq:entropy_twophase_chemeq}
$$

The two major steps that we now need to perform are:

1. Recast the velocities in terms of relative velocities, often relative to the centre of mass (barycentric velocity).
2. Parameterise the resulting fluxes that originate from considering relative velocities.

\bibliography