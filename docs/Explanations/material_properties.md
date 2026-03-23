---
tags:
  - material properties
  - equation of state
  - viscosity
---

# SPIDER: model overview

!!! note 
    This model overview is taken from the [notes](https://github.com/FormingWorlds/SPIDER/tree/main/notes/) and contains an extended description of the equations and derivations related to the SPIDER code. It is still **work in progress.** 

## Material Properties

### Mantle EOS

A simple approximation is made to calculate the thermodynamic properties of the mantle silicates, representing them as a pseudo-single-component system.

We consider a mantle that is everywhere in local thermodynamic equilibrium, resulting in uniform compositional profiles.  Driven by buoyancy differences, crystals that form are displaced from their point of crystallization, instantaneously removing heat as they are resorbed by the magma ocean (according to Clausius Clapeyron).  Crystal-melt separation should cause chemical differentiation, however if the timescales for turbulent mixing are sufficiently fast, the mantle will remain homogenous.  Furthermore, persistent differentiation (which is expected for the later stages of crystallization as viscosity rises and timescales lengthen) represents a second-order correction on top of the first order energetics represented by convection, heat dissipation, and crystallization of a uniform composition magma ocean.

We represent the thermodynamics of mantle melting using a pseudo-one-component model, which retains the simplicity of a standard one-component model, while introducing the important multi-component characteristic of a finite temperature interval for melting.  We develop this model in response to the arguments of [^cite-SA07], which shows how many of the most important aspects of mantle melting can be reasonably-represented by a simple one-component model when viewed in pressure-entropy space.  Besides its lack of chemical evolution, the primary shortcoming of this approach is the absence of a thermal melting interval, which arises due to differential chemical partitioning between solid and melt phases, as demonstrated by simple systems with binary loops. 

 It is a useful first approximation to consider a crystallizing magma ocean as a chemically homogenous system, where the evolving chemistries of its constituent phases are assumed to remain in thermodynamic equilibrium maintaining constant bulk composition.  We can therefore approximate the energetics of this system by modifying a standard one-component system, replacing the univariant melting curve in P-T space $T_{\rm fus}(P)$ by a melting interval.

The single-component melting curve is given by $T_{\rm fus}(P)$ and $S_{\rm fus}(P)$, and is defined by the condition of equilibrium, where the solid and melt phases have equal Gibbs energies at the melting temperature for each pressure.

The modified melting interval is centered on the fusion curve, bounded by the liquidus above and solidus below:

$$T_{\rm liq}(P) = T_{\rm fus}(P) + \Delta T_{\rm fus}(P) / 2$$

$$T_{\rm sol}(P) = T_{\rm fus}(P) - \Delta T_{\rm fus}(P) / 2$$

where the melting interval width is defined by $\Delta T_{\rm fus}(P)=\delta T \cdot T_{\rm fus}(P)$ with $\delta T \approx 0.07$ throughout the mantle [^cite-SKS09].

### Solid EOS

For the Mosenfelder MgSiO3 model, we use the EOS for MgSiO3 melt and Mg-endmember bridgmanite as given by the global fit to shock wave and diamond anvil cell data in [^cite-M09].  Since this paper does not fully define all of the needed EOS parameters, we rely upon the estimated melting region (bounded by solidus and liquidus profiles) for the mantle given by [^cite-SKS09].  It is important to recognize that [^cite-M09] does not present a thermodynamically consistent model of this system, due to its use of the Mie-Grüneisen formulation, which assumes that the grüneisen parameter is independent of temperature together with its model for the heat capacity of the melt, which induces temperature dependence to the adiabatic compression curves.

The primary thermodynamic property controlling magma ocean evolution is the grüneisen parameter, $\gamma$, which controls the adiabatic thermal profile through a convecting system:

$$\frac{dT}{dP}\bigg|_S = \gamma \left( \frac{T}{K_S} \right)$$

The *thermodynamic* definition of the grüneisen parameter is given by:

$$\gamma \equiv -\frac{\partial \log_e{T}}{\partial \log_e{V}}\bigg|_S = \frac{\alpha K_S V}{C_P}$$

where $\alpha$ is the thermal expansion, $K_S$ is the adiabatic bulk modulus, and $C_P$ is the constant pressure heat capacity.  In the case of solids, the grüneisen parameter is approximately independent of temperature at low to moderate temperatures, as a consequence of nearly harmonic atomic vibrations for small vibrational amplitudes (as described by the quasi-harmonic approximation, QHA).  This allows us to integrate the equation above to obtain an expression for the temperature along the reference adiabat, $T_{0S}(V)$:

$$T_{0S}(V) = T_0 \exp \left[ -\int_{V_0}^{V} \frac{\gamma(V)}{V} dV \right]$$

where $T_0$ is the reference adiabatic temperature at 0 GPa.

The standard power-law expression gives a simple and reasonable representation over wide compression ranges:

$$\gamma(V) = \gamma_0 \left(\frac{V}{V_0}\right)^q$$

where $\gamma_0$ and $q$ give the value at the reference state and the compression dependence.
In this form, the reference adiabatic temperature simplifies to:

$$T_{0S}(V) = T_0 \exp \left[ -(\gamma - \gamma_0)/q \right]$$

Though this temperature-independent form of the grüneisen parameter is often used in shock wave experiments, the underlying assumptions of QHA are strongly violated at significant fractions of the melting temperature.
The most dramatic consequence of the strong anharmonicity present at high temperatures is that thermal expansions are overestimated by 30-100% near melting [^cite-WW09], challenging the ability to accurately model melting phase relations.

To maintain a physically reasonable model, we apply lowest-order perturbation theory to account for anharmonicity (e.g. [^cite-ZK71], [^cite-OD03]).
Under near-melting conditions, the grüneisen parameter is no longer independent of temperature, and thus we first describe the reference adiabat for the solid, $T_{0S}^{\rm sol}$ by defining the grüneisen parameter evolution along a reference adiabatic compression curve, $\gamma_{0S}^{\rm sol}$.
Since magma ocean modeling is concerned only with temperatures near or above the solidus, we are free to choose a zero-pressure reference temperature of $T_0^{\rm sol}$=1000 K to ensure that we are in the classical Dulong-Petit limit, yielding a constant heat capacity.
The lowest-order anharmonic correction yields a temperature-dependent heat capacity:

$$C_V^{\rm sol} = 3N k_B (1 - aT)$$

where $k_B$ is Boltzmann's constant, $N$ is the number of atoms per formula unit, $a$ is the volume-dependent anharmonic correction factor.
We assume a power-law dependence for the anharmonicity factor:

$$a(V) = a_0 \left( \frac{V}{V_0} \right)^m$$

where the reference value $a_0$ and its compression dependence $m$ must be determined empirically.
The entropy gain relative to the reference adiabat is obtained by integration:

$$\Delta S_0^{\rm sol}(V,T) = \int_{T_{0S}^{\rm sol}}^T  \frac{C_V^{\rm sol}}{T} dT = 3N k_B \left[ \log_e (T/T_{0S}^{\rm sol}) - a(T - T_{0S}^{\rm sol}) \right]$$

where $T_{0S}^{\rm sol}(V)$ is given by the adiabat equation above.
By taking partial derivatives with respect to $V$ and $T$, we obtain the total differential:

$$\frac{dS^{\rm sol}}{3N k_B} = \left[ \frac{1}{T} - a \right] dT + \left[ - \frac{1}{T_{0S}^{\rm sol}}\frac{d T_{0S}^{\rm sol}}{dV} -\frac{da}{dV}(T-T_{0S}^{\rm sol}) + a \frac{dT_{0S}^{\rm sol}}{dV}\right]dV$$

By setting $dS^{\rm sol}=0$ and rearranging, we obtain the expression for the grüneisen parameter allowing in the presence of anharmonic effects:

$$\gamma^{\rm sol}(V,T) = \frac{(1-a T_{0S}^{\rm sol})\gamma_{0S}^{\rm sol} - (T-T_{0S}^{\rm sol})ma}{1-aT}$$

where if we assume zero anharmonicity ($a=0$) or restrict ourselves to the reference adiabat ($T=T_{0S}^{\rm sol}$), we recover the reference grüneisen evolution given by $\gamma_{0S}^{\rm sol}(V)$.

The internal energy expression is similarly determined by integration along a pathway up the reference adiabat and then up to the target temperature $(V_0,T_0) \rightarrow (V,T_{0S}) \rightarrow (V,T)$:

$$\Delta E_0^{\rm sol}(V,T) = -\int_{V_0}^V  P_S^{\rm sol}(V) dV + \int_{T_{0S}}^{T} C_V^{\rm sol} dT$$

$$= -\int_{V_0}^V  P_S^{\rm sol}(V) dV + 3N k_B [ (T-T_{0S}^{\rm sol}) - a/2(T^2 - {T_{0S}^{\rm sol}}^2) ]$$

where $P_S^{\rm sol}(V)$ describes the compression curve of the reference adiabat, described using the Vinet EOS:

$$P_S(V) = 3K_{0S}(1-x)x^{-2}\exp\left[\nu(1-x)\right]$$

$$\text{where } x=(V/V_0)^{1/3} \text{ and } \nu=\frac{3}{2}(K'_{0S}-1)$$

where $V_0$, $K_{0S}$, and $K'_{0S}$, are the zero pressure volume, adiabatic bulk modulus, and its pressure derivative.
The total pressure is given by the volume derivative:

$$P^{\rm sol}(V,T) = P_S^{\rm sol} + 3N k_B\left[(1-aT)\frac{dT}{dV}\bigg|_S -  (1-aT_{0S}^{\rm sol})\frac{dT_{0S}^{\rm sol}}{dV} \right]$$

$$+ \frac{3}{2}N k_B \frac{da}{dV}(T^2 - {T_{0S}^{\rm sol}}^2)$$

### Liquid EOS

To represent the thermodynamics of mantle material in a simple and flexible way, we derive a new parameterization high pressure melt EOS which captures melt behavior while retaining physically meaningful parameters that are easily interpreted in the context of magma ocean crystallization [^cite-WB18].

### Solution

#### Density: Volume–mass proportionality

For each component $i$:

$$\rho_i = \frac{m_i}{v_i}$$

For solution:

$$\rho_{sol}=\frac{m_{sol}}{v_{sol}} = \frac{\sum_i m_i}{v_{sol}} = \sum_i \frac{m_i}{v_{sol}} = \sum_i \frac{m_i}{v_i} \frac{v_i}{v_{sol}} = \sum_i \rho_i \left( \frac{v_i}{v_{sol}} \right)$$

**Assume volume is proportional to mass**, for both the solution and the pure phase:

$$v \propto m$$

Now **assume proportionality constant $c$ is the same for both the solution and the pure phase**.  This means the two substances have similar pure densities:

$$v = c m$$

Therefore, continuing from above by substituting in the assumptions:

$$\rho_{sol}=\sum_i \rho_i \left( \frac{v_i}{v_{sol}} \right) = \sum_i \rho_i \left( \frac{c m_i}{c \sum_i m_i} \right) = \sum_i \rho_i \omega_i$$

where $\omega_i$ is mass fraction of component $i$:

$$\omega_i = \frac{m_i}{\sum_i m_i} = \frac{m_i}{M}$$

This is perhaps the most used and "intuitive" description of the density of a solution.  It conveniently means that the density of a solution is the addition of the mass-weighted (pure) densities of the components:

$$\rho_{sol}=\sum_i \rho_i \omega_i$$

#### Density: Volume additivity

$$\omega_i = \frac{m_i}{M}$$

$$\frac{\omega_i}{\rho_i} = \frac{m_i}{M} \frac{v_i}{m_i} = \frac{v_i}{M}$$

From above:

$$\therefore \sum_i \left( \frac{\omega_i}{\rho_i} \right) = \frac{1}{M} \sum_i v_i$$

Now **assume volumes are additive**.  Typically true for ideal solutions and immiscible, non-reacting mixtures:

$$\frac{1}{M} \sum_i v_i = \frac{V}{M} = \frac{1}{\rho} \implies \frac{1}{\rho} = \sum_i \left( \frac{\omega_i}{\rho_i} \right)$$

where, as before, $\omega$ is the mass fraction of component $i$ in the mixture.  This is what we currently use in SPIDER to calculate the density of the mixture based on the end-member densities of MgSiO₃ melt and solid.

#### Solution properties

We modify the single-component silicate (bridgmanite) model to accommodate a partially-molten (mixed-phase) region to reasonably approximate the behaviour of a multi-component mantle.  This relies on 2 approximations: 

1. Chemical differentiation is negligible (second order effect, at least energetically)
2. The thermal range of the partially molten region (~200 K) is small compared to the temperature difference across the mantle (~2500 K). Values from [^cite-SKS09].

This is achieved by fitting a single-component fusion curve to the 50% solidus line for a realistic mantle chemistry.  Then we define a melting interval centred about the fusion curve to ensure solidus and liquidus enthalpy/entropy bounds that match the "true" mantle system:

$$S_{\rm liq}(P) = S_{\rm fus}(P) + \Delta S_{\rm fus}(P) / 2$$
$$S_{\rm sol}(P) = S_{\rm fus}(P) - \Delta S_{\rm fus}(P) / 2$$

where $S$ is entropy, $P$ pressure, and $S_{\rm fus}$ is the fusion curve.  Subscripts "liq" and "sol" denote that the quantity is determined at the liquidus and solidus, respectively.  The entropy of fusion, $\Delta S_{\rm fus}$ is computed to ensure the liquidus and solidus approximate those for a multi-component mantle.

!!! note "Side note"
    The melting curve used by [^cite-ABE93] is from Ohtani (1983), although it may be slightly adjusted. Ohtani appears to assume a constant entropy change on melting (fairly reasonable assumption) of 8.03 cal/mol/K for MgSiO3 melt.  The enthalpy change in [^cite-ABE93] is likely calculated from this value, $\Delta h = T \Delta S$.

To obtain the properties of the two phase aggregate, we represent the entropy of the system as a linear mixture of the solid and liquid values, thus providing a simple estimate of the melt fraction as a function of total entropy:

$$\phi=
\begin{cases}
  1 & \text{for } S>S_{\rm liq} \\
  (S-S_{\rm sol}) / \Delta S_{\rm fus} & \text{for } S_{\rm sol}<S<S_{\rm liq} \\  
  0 & \text{for }  S<S_{\rm sol}
\end{cases}$$

An advantage of expressing melt fraction in terms of entropy, rather than temperature, is that heat capacity is self-consistently calculated in the mixed-phase region rather than implicitly assuming that the heat capacity is equal for coexisting melt and solid.  The properties of the melt-solid aggregate are dominantly determined by melt fraction so we approximate temperature, $T$ in the mixed-phase region as a linearly weighted mixture of melt and solid endmembers:

$$T=
\begin{cases}
  T_m & \text{for } S>S_{\rm liq} \\
  \phi T_{\rm liq} + (1-\phi) T_{\rm sol} & \text{for } S_{\rm sol}<S<S_{\rm liq} \\  
  T_s & \text{for } S<S_{\rm sol}
\end{cases}$$

Herein subscripts "m" and "s" denote that the quantity is determined exclusively by the melt or solid equation of state, respectively.  Density $\rho$, following volume additivity, is:

$$\frac{1}{\rho} = \frac{1-\phi}{\rho_{\rm sol}} + \frac{\phi}{\rho_{\rm liq}}$$

Heat capacity, $c_p$ [^cite-SOLO07], [^cite-SS293] is:

$$c_p = \frac{\Delta H_{\rm fus}}{\Delta T} = T_{\rm fus} \frac{\Delta S_{\rm fus}}{\Delta T_{\rm fus}}$$

where $T_{\rm fus}$ is temperature of the fusion curve and $\Delta T_{\rm fus} = T_{\rm liq}-T_{\rm sol}$ is the temperature difference between the liquidus and solidus.  Recall that $\Delta H _{\rm fus} = T_{\rm fus} \Delta S_{\rm fus}$ from application of $\Delta S = q_{\rm rev}/T$.  

Thermal expansion coefficient $\alpha$ [^cite-SOLO07], [^cite-SS293] is:

$$\alpha = -\frac{\Delta \rho_{\rm fus}}{\rho \Delta T_{\rm fus}}$$

where $\Delta \rho_{\rm fus} = \rho_{\rm liq} - \rho_{\rm sol}$.  

The adiabatic temperature gradient $dT/dP|_S$ is derived by noting that an upward parcel of fluid "solidifies an amount sufficient to release heat of fusion equal to the heat required to make up the difference between the adiabatic gradient and the melting point gradient" (quoting from [^cite-HK71]):

$$c_p \left( \frac{dT_{\rm fus}}{dP} - \frac{dT}{dP}\bigg|_S \right) = \frac{\Delta H_{\rm fus}}{dP} = T_{\rm fus} \frac{d S_{\rm fus}}{dP}$$

Rearranging and substituting in the heat capacity equation:

$$\frac{dT}{dP}\bigg|_S = \frac{dT_{\rm fus}}{dP} - \frac{\Delta T_{\rm fus}}{\Delta S_{\rm fus}} \frac{d S_{\rm fus}}{dP}$$

Alternatively:

$$\frac{dT}{dP}\bigg|_S = \frac{\alpha T}{\rho c_p}$$

In [^cite-BSW18], [^cite-BKW19] we used the first equation to compute the adiabatic gradient in the mixed phase region, but this involves calculating the gradient of the fusion curve, which is a hypothetical melting curve between the solidus and liquidus.  This is not as convenient, nor as exact, as using the alternative equation which is an exact thermodynamic representation.  Therefore, the preference would be to switch to a formulation akin to the alternative equation.  Tests with SPIDER show that the two equations return different results for $dT/dP|_S$ in the mixed phase region, but the overall cooling trends are often near indistinguishable.

Together, these expressions represent a thermodynamically consistent metastable combination of solid and melt phases, chosen to best mimic the behavior of the multicomponent mantle over the melting interval.  Outside of the mixed-phase region the quantities are equal to their melt and solid values exclusively, as for temperature.  This model provides thermodynamic properties as a function of pressure and entropy for the melt, solid, and mixed phase that are input to the evolution model i.e., $\phi$, $T$, $\rho$, $c_p$, $\alpha$, and $dT/dP|_S$.

### Viscosity

Currently, the standard Arrhenius law is implemented.  To pin the viscosity to a reference viscosity $\eta_0$ at pressure $P_0$ and temperature $T_0$, we use:

$$\log_{10} ( \eta (P,T)) = \log_{10} \eta_0 + \frac{E_a + V_aP}{RT} - \frac{E_a + V_a P_0}{R T_0}$$

for activation energy $E_a$ and activation volume $V_a$.  This can be rewritten as:

$$\log_{10} ( \eta (P,T)) = \log_{10} \eta_0 + \frac{(E_a + V_a(P_0 + \Delta P))T_0 - (E_a + V_aP_0)(T_0 + \Delta T)}{R T_0 (\Delta T + T_0)}$$

for $\Delta P = P - P_0$ and $\Delta T = T - T_0$. If we write $\Delta T' = \Delta T/T_0$, we get:

$$\log_{10} ( \eta (P,T)) = \log_{10} \eta_0 + \frac{V_a \Delta P - (E_a + V_a P_0)\Delta T'}{R T_0 (1 + \Delta T')}$$

$$\log_{10} ( \eta (P,T)) = \log_{10} \eta_0 + \frac{-E_a \Delta T' + V_a (\Delta P - P_0 \Delta T')}{R T}$$

Now the form is similar to the first equation if the last term was ignored (i.e., no assumed pinning).
Values can be specified in the input file, where $\eta_0$ is the reference viscosity at P–T conditions given by $P_0$ and $T_0$.  Recommended CMB values are $\eta_0 = 10^{22}$, $T_0 = T_{CMB} \approx 4000$ K and $P_0 = P_{CMB} \approx 138$ GPa.  Another option is to adopt the convention used in StagYY, where $P_0 = 0$, $T_0 = 1600$ and $\eta_0 = 10^{19}$.  In this later case, the viscosity structure is pinned to the top of the 1600 K adiabat.

#### Compositionally dependent viscosity

Viscosity is strongly dependent on the Si-abundance in the mantle. Very Si-rich mantles are much more viscous than very Mg-rich mantles. The compositional dependency is applied simply by adding a term to the viscosity, $\ln \eta_{new} = \ln \eta + \Delta \eta_c$. It depends on the Mg/Si-ratio, which is specified in the input file with `-Mg_Si`, where you can enter 0.0 to switch it off. Usually, it is set to 1.08, the value for Earth. It is linearly dependent on Mg/Si in several steps:

$$\Delta \eta_c = 
\begin{cases}
2 & \text{Mg/Si} < 0.5 \\
\log(3.3) + (2 - \log(3.3))\frac{0.7 - \text{Mg/Si}}{0.2} & 0.5 \leq \text{Mg/Si} < 0.7 \\
\log(3.3)\frac{1 - \text{Mg/Si}}{0.3} & 0.7 \leq \text{Mg/Si} < 1.0 \\
\log(0.033)\frac{\text{Mg/Si}-1}{0.25} & 1.0 \leq \text{Mg/Si} < 1.25 \\
-2 + (\log(0.033) + 2)\frac{1.5 - \text{Mg/Si}}{0.25} & 1.25 \leq \text{Mg/Si} < 1.5 \\
-2 & \text{Mg/Si} \geq 1.5
\end{cases}$$

The correction above is centered around Mg/Si = 1.0. If the reference viscosity profile is not for a planet with Mg/Si=1.0, then the compositional correction should be altered to compensate for the difference. This is done by subtracting the compositional correction of the composition for which the reference viscosity profile is calculated (usually Earth-like composition). The composition for which the reference viscosity profile has been calculated can be given in the options file as `-Mg_Si_ref`. This should be set to Earth-like composition as default, since most reference viscosity profiles are calculated for Earth. The compositional correction is stored in `P visc_ref_comp`.

#### Depth-dependent activation volume

Activation volume $V_a$ changes with depth. This change is already implemented in StagYY, and now also in SPIDER. The implementation and numbers are based on Antoine Rozel's paper, "Continental crust formation on early Earth controlled by intrusive magmatism" (Nature, 2017). It is described by:

$$V_a(P) = V_0 \exp(- P/P_i)$$

where $V_0$ is the same as the value for $V_a$ used before, and pressure scaling $P_i$ is given by Rozel et al. at $P_i=200$ GPa in the lower mantle, and zero in the upper mantle. Currently, in SPIDER it is not possible yet to vary this value between UM and LM (or between layers), but that should not be difficult to implement. Currently, this part is controlled by two input parameters: `-activation_volume_pressure_dependency` is used to switch this formula on or off (1 is on, any other integer is off), while `-activation_volume_pressure_scaling` gives the scaling pressure $P_i$ for if the dependency is switched on. Currently it is set to 200e9 Pa (200 GPa).

Using this description for $V_a$ changes the equation for viscosity, since the $V_a$ multiplied with $P$ is not the same as the one multiplied with $P_0$. Starting from the Arrhenius equation, we get:

$$\ln ( \eta (P,T)) = \ln \eta_0 + \frac{( V_a(P)*(P_0 + \Delta P))*T_0 -  V_a(P_0)*P_0*(T_0 + \Delta T) + E_a (T_0 - (T_0 + \Delta T))}{R T_0 (\Delta T + T_0)}$$

which can be slightly rewritten to the form which is implemented in SPIDER:

$$\ln ( \eta (P,T)) = \ln \eta_0 + \frac{V_a(P) \Delta P + P_0 \left( V_a(P) - V_a(P_0) (1 + \Delta T' ) \right) - E_a \Delta T' }{R T}$$

since $T = T_0(1 + \Delta T' )$. Also, $V_a(P_0) =\exp(-P_0/P_i)$ is a constant throughout the simulation.

[^cite-SA07]: Edward Stolper; Paul Asimow, *Insights into mantle melting from graphical analysis of one-component systems*, Am. J. Sci., 2007.
[^cite-SKS09]: Lars Stixrude; Nico de Koker; Ni Sun; Mainak Mookherjee; Bijaya B. Karki, *Thermodynamics of silicate liquids in the deep Earth*, Earth Planet. Sci. Lett., 2009.
[^cite-M09]: Mosenfelder, Jed L.; Asimow, Paul D.; Frost, Daniel J.; Rubie, David C.; Ahrens, Thomas J., *The MgSiO3 system at high pressure: Thermodynamic properties of perovskite, postperovskite, and melt from global inversion of shock and static compression data*, J. Geophys. Res. Solid Earth, 2009.
[^cite-WW09]: Wu, Zhongqing; Wentzcovitch, Renata M., *Effective semiempirical ansatz for computing anharmonic free energies*, Phys. Rev. B, 2009.
[^cite-ZK71]: V. N. Zharkov; V. A. Kalinin, *Equations of State for Solids at High Pressures and Temperatures*, Springer, Boston, MA, 1971.
[^cite-OD03]: Oganov, Artem R.; Dorogokupets, Peter I., *All-electron and pseudopotential study of MgO: Equation of state, anharmonicity, and stability*, Phys. Rev. B, 2003.
[^cite-WB18]: Aaron S. Wolf; Dan J. Bower, *An equation of state for high pressure-temperature liquids (RTpress) with application to MgSiO$_3$ melt*, Phys. Earth Planet. Inter., 2018.
[^cite-ABE93]: Yutaka Abe, *Thermal Evolution and Chemical Differentiation of the Terrestrial Magma Ocean*, Evolution of the Earth and Planets, 1993.
[^cite-SOLO07]: V. S. Solomatov, *Magma Oceans and Primordial Mantle Differentiation*, Treatise on Geophysics, 2007.
[^cite-SS293]: Solomatov, Viatcheslav S.; Stevenson, David J., *Nonfractional crystallization of a terrestrial magma ocean*, J. Geophys. Res.-Planet., 1993.
[^cite-HK71]: Higgins, G.; Kennedy, G. C., *The adiabatic gradient and the melting point gradient in the core of the Earth*, J. Geophys. Res., 1971.
[^cite-BSW18]: Dan J. Bower; Patrick Sanan; Aaron S. Wolf, *Numerical solution of a non-linear conservation law applicable to the interior dynamics of partially molten planets*, Phys. Earth Planet. Inter., 2018.
[^cite-BKW19]: Dan J. Bower; Daniel Kitzmann; Aaron S. Wolf; Patrick Sanan; Caroline Dorn; Apurva V. Oza, *Linking the evolution of terrestrial interiors and an early outgassed atmosphere to astrophysical observations*, A&A, 2019.
