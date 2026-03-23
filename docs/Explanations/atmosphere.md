---
tags:
  - volatiles
  - outgassing
  - atmospheric escape
---

# SPIDER: model overview

Here you can find a detailed overview of the SPIDER formulation.

!!! note 
    This model overview is taken from the [notes](https://github.com/FormingWorlds/SPIDER/tree/main/notes/) and contains an extended description of the equations and derivations related to the SPIDER code. It is still **work in progress.** 

## Volatile Mass Balance

The mass balance of a given volatile in the interior [^cite-LMC13] is:

$$X_v^s M^s + X_v^l M^l + X_v^g M^g + m_v^e + m_v^o + m_v^r = X_v^{\rm init} M^m$$

where superscripts $s$, $l$, $g$, $e$, $o$, $t$ denote solid, liquid (melt), gas, escaped, ocean, and total. **Only solid, liquid, and atmosphere are physical reservoirs.**

The partition coefficient relates volatile concentrations:

$$k_v = \frac{X_v^s}{X_v}$$

### Atmospheric mass

The total atmospheric mass of $q$ species composes as:

$$m_t^g = \frac{4 \pi R_p^2}{g} P_s$$

where $R_p$ is planetary radius and $P_s$ is surface pressure.

The mass of a given volatile species is:

$$m_v^g = 4 \pi R_p^2 \left( \frac{\mu_v^g}{\bar{\mu}} \right) \frac{p_v}{g}$$

Partial pressure follows a modified (power-law) Henry's law:

$$p_v ( X_v ) = \left( \frac{X_v}{\alpha_v} \right)^{\beta_v}$$

In SPIDER we use scaled mass (omitting the $4 \pi$ factor):

$$X_v (k_v M^s + M^l) + \frac{R_p^2}{g} \left( \frac{\mu_v^g}{\bar{\mu}} \right) p_v + m_v^e + m_v^o + m_v^r = X_v^{\rm init} M^m$$

We solve for volatile mass fraction in the liquid phase, from which we can compute volatile mass in solid and gas phases.

## Non-dimensionalisation

### Mass

Masses are non-dimensionalised as:

$$M = \rho_0 R_0^3 \hat{M}$$

### Volatile Concentration

Volatile concentration is expressed as scaled mass fraction:

$$X_v = V_0 \hat{X}_v$$

where $V_0=10^{-6}$ gives parts-per-million (ppm), $V_0=10^{-2}$ gives weight percent (wt%), and $V_0=1$ gives mass fraction.

### Power Law Solubility

Non-dimensional partial pressure:

$$\hat{p}_v ( \hat{X}_v ) = \left( \frac{\hat{X}_v}{\hat{\alpha}_v} \right)^{\beta_v}$$

where:

$$\hat{\alpha}_v = \frac{\alpha_v^{{\rm ppm/Pa}^{1/\beta_v}}}{10^6} \frac{P_0^\frac{1}{\beta_v}}{V_0}$$

## Sossi Solubility

For H$_2$O [^cite-SF17]:

$$X_v = A{f_{H_2O}}^\frac{1}{2}+B G f_{H_2O}$$

where fugacities are constrained by oxygen buffer, and $A=534$ ppm/bar$^{0.5}$ and $B=723$ ppm/bar.

## Initial Volatile Concentration

For an initial condition, we prescribe the total volatile concentration and solve the mass balance to obtain initial partial pressure consistent with chemical equilibrium criteria.

## Chemical Reactions

Reactions transfer mass between volatile species. For example:

$$[\rm{H}_2O]\leftrightarrow \frac{1}{2} [\rm{O}_2] + [\rm{H}_2]$$

with equilibrium constant:

$$K=\frac{p_{\rm H_2} f_{\rm O_2}^{1/2}}{p_{\rm H_2\rm O}}$$

Mass is conserved through stoichiometry:

$$m_{H_2O} = m_{O2} + m_{H_2}$$

## Atmospheric Escape

### Jeans escape

$$\frac{d m_v^e}{dt} = \left( \frac{d m_{\rm v}^{\rm g}}{dt} \right) \mathcal{R} (1 + \lambda_s) \exp(-\lambda_s) + \frac{\Phi}{4 \pi}$$

where Jeans parameter:

$$\lambda_s = \frac{g R_p \mu_{\rm v}}{k_b T_s N_A}$$

### Zahnle escape model

For H$_2$ [^cite-ZGC19]:

$$\phi_{H_2} \approx \Gamma \frac{(1 \times 10^{12}) f_{H_2} S}{\sqrt{1+0.006S^2}}$$

where $S$ is non-dimensional and $\Gamma$ is a scaling constant.

## Grey atmosphere model

### Optical depth

$$\tau^\ast = \frac{3 \kappa^\prime p(\tau^\ast)}{2g}$$

### Effective emissivity

Optical depths for each volatile are combined:

$$\epsilon = \frac{2}{\sum_j \tau_j^\ast +2}$$

### Atmosphere temperature structure

Temperature as function of optical depth [^cite-AM85]:

$$T(\tau^\ast) = \left( T_0^4 \frac{(\tau^\ast+1)}{2} +T_\infty^4 \right)^\frac{1}{4}$$

where:

$$T_0 = \left( \frac{F_{atm}}{\sigma} \right)^\frac{1}{4}$$

### Stellar flux

$$F_{sun} = \sigma T_{eqm}^4 = (1-\alpha) \frac{F_0^\prime}{D^2}$$

where $\alpha$ is bolometric albedo, $F_0'$ is averaged solar constant, and $D$ is planet-star distance.

[^cite-LMC13]: Lebrun, T.; Massol, H.; Chassefi\`ere, E.; Davaille, A.; Marcq, E.; Sarda, P.; Leblanc, F.; Brandeis, G., *Thermal evolution of an early magma ocean in interaction with the atmosphere*, J. Geophys. Res.-Planet., 2013.
[^cite-SF17]: Laura Schaefer; Bruce Fegley, *Redox States of Initial Atmospheres Outgassed on Rocky Planets and Planetesimals*, Astrophys. J., 2017.
[^cite-ZGC19]: Kevin J. Zahnle; Marko Gacesa; David C. Catling, *Strange messenger: A new history of hydrogen on Earth, as told by Xenon*, Geochim. Cosmochim. Acta, 2019.
[^cite-AM85]: Abe, Yutaka; Matsui, Takafumi, *The formation of an impact-generated H2O atmosphere and its implications for the early thermal history of the Earth*, J. Geophys. Res. Solid Earth, 1985.
