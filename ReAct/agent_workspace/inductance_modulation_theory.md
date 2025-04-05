## Theoretical Modeling of Inductance Modulation

This response addresses your query regarding the theoretical modeling of inductance modulation in a resonator winding using an external pump field. We develop a mathematical relationship between the external pump field and the inductance of the resonator winding, considering the KMAC-320 B-H curve, core geometry, and an amplitude-modulated external pump at $2f_0$.

### 1. Field Addition within the Core

The magnetic field inside the core is the vector sum of the resonator winding magnetic field $H_{res}$ and the external pump field $H_{pump}$. The orientation affects how they combine:

- **Inline Orientation:**
  - Parallel: $H_{total} = H_{res} + H_{pump}$
  - Anti-parallel: $H_{total} = H_{res} - H_{pump}$

- **Orthogonal Orientation:**
  
  $H_{total} = \sqrt{H_{res}^2 + H_{pump}^2}$

### 2. Permeability Variation with $H_{total}$

The relative permeability is:

$$
\mu_r = \frac{B}{\mu_0 H_{total}}
$$

where $\mu_0$ is the permeability of free space.

- At low $H_{total}$: high $\mu_r$
- Increasing $H_{total}$: $\mu_r$ decreases as the core saturates
- Saturation: $\mu_r \approx 1$

### 3. Inductance Dependence on Permeability

The inductance is:

$$
L = N^2 \mu_0 \mu_r \frac{A_e}{L_m}
$$

where:

- $N$ = number of turns
- $A_e$ = effective cross-sectional area
- $L_m$ = magnetic path length

Since $\mu_r$ depends on $H_{total}$, $L$ is modulated by the external pump.

### 4. Time-Varying Inductance $L(t)$

Assuming:

- Resonator field:

$$
H_{res}(t) = H_{r0} \cos(2\pi f_0 t)
$$

- Pump field (AM at $2f_0$):

$$
H_{pump}(t) = H_{p0} [1 + m \cos(2\pi f_{mod} t)] \cos(4\pi f_0 t)
$$

where:

- $H_{r0}$, $H_{p0}$ = amplitudes
- $m$ = modulation index ($0 \leq m \leq 1$)
- $f_{mod} = 2f_0$

- **Inline total field:**

$$
H_{total}(t) = H_{r0} \cos(2\pi f_0 t) + H_{p0} [1 + m \cos(2\pi f_{mod} t)] \cos(4\pi f_0 t)
$$

- **Orthogonal total field:**

$$
H_{total}(t) = \sqrt{\big(H_{r0} \cos(2\pi f_0 t)\big)^2 + \big(H_{p0} [1 + m \cos(2\pi f_{mod} t)] \cos(4\pi f_0 t)\big)^2}
$$

- **Inductance:**

$$
L(t) = N^2 \mu_0 \mu_r(H_{total}(t)) \frac{A_e}{L_m}
$$

where $\mu_r(H)$ is derived from the KMAC-320 B-H curve.

### 5. Assumptions

- Quasi-static fields, linear superposition
- Neglect hysteresis, phase lag
- Homogeneous, isotropic core
- Lumped element model

### 6. Orientation Effectiveness

- **Inline:** More effective, larger $H_{total}$ swing, stronger $\mu_r$ and $L$ modulation
- **Orthogonal:** Less effective, smaller change in $H_{total}$ magnitude

### **Summary**

- Inductance modulation depends on non-linear $\mu_r(H_{total}(t))$
- Inline pump orientation yields stronger modulation
- Precise $L(t)$ requires numerical B-H data

### **Sources**

- [SMAG Handbook](https://www.magweb.us/wp-content/uploads/2021/08/SMAG-Handook-Version-7.pdf)
- [COMSOL B-H Curve Blog](https://www.comsol.com/blogs/how-the-b-h-curve-affects-a-magnetic-analysis-and-how-to-improve-it)
- [Coil32 Ferrite Core Calculator](https://coil32.net/ferrite-e-core.html)
- [DigiKey Ferrite Core Guide](https://forum.digikey.com/t/ferrite-cores/33022)
- [LinkedIn Magnetic Core Parameters](https://www.linkedin.com/pulse/what-meant-effective-parameters-magnetic-core-how-calculate-p)
