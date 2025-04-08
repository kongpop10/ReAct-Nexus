Below is an in‐depth discussion on how to optimize the number of turns in a helical winding—taking into account the torus geometry (its major radius, R, and minor radius, r)—to maximize the net vertical (uplifting) force, and an explanation regarding the nature of the current in the winding.

---

## 1. Optimizing the Helical Winding Turns

When using a helical (or toroidal‐helical) winding in a lifter device, the goal is to maximize the upward force that arises from the interaction between the current in the winding and the magnetic field it produces (or an externally imposed magnetic field). In many designs, the upward force accumulated from the winding is related to the vertical component of the local Lorentz force produced along the winding. Two competing effects play a role:

- **Increasing the Number of Turns (N):**  
  More turns result in a longer total conductor length. That is beneficial because the net force is (roughly) proportional to the length of the current‐carrying conductor where the magnetic field can interact with it. However, when you pack more turns in a fixed toroidal envelope (a fixed torus geometry), the **pitch**—the vertical separation between successive turns—tends to decrease.

- **Pitch (p) and the Helix Angle (α):**  
  For a helical winding, the vertical component of each infinitesimal force element is scaled by the sine of the helix angle, α. If the helix is too “tight” (i.e. has too many turns) the pitch becomes small, and although you have more conduction length, each turn’s upward contribution (proportional to sin α) is reduced. The helix angle for a winding arranged on a torus can be approximated (in a simplified model) as

\[
\alpha \;=\; \arctan\!\left(\frac{p}{L_\mathrm{circ}/N}\right)
\]

where:
- \(p\) is the pitch (vertical displacement per full toroidal revolution), and  
- \(L_\mathrm{circ}\) is an effective “circumferential length” available for the winding (roughly on the order of \(2\pi\,(R + r)\) if the winding wraps around the full torus).

Thus, one can write

\[
\alpha \;\approx\; \arctan\!\left(\frac{pN}{2\pi\,(R+r)}\right).
\]

Accordingly, the **vertical projection** of each small segment along the winding is \(d\ell \, \sin\alpha\), and the net upward contribution (assuming the force per length is roughly uniform) becomes proportional to

\[
F_z \;\propto\; I\,B\,\bigl[N \,L_\mathrm{turn}\bigr]\,\sin\alpha,
\]

where \(L_\mathrm{turn}\) is the length of one helical turn and \(I\) and \(B\) are the current and magnetic field levels, respectively.

### Finding an Optimum

At one extreme, if you have very few turns, the pitch is large and \(\sin\alpha\) can be high. However, the total conductor length (and hence the integrated force) is low. At the other extreme, packing in too many turns reduces the pitch so much that—even though the total conductor length increases—the vertical contribution per turn (multiplied by \(\sin\alpha\)) drops.

A simplified optimization may be done by writing the net vertical thrust contribution (for one toroidal revolution) as a function of N. For example, if we assume that each turn contributes a vertical length roughly equal to its pitch, and if we further assume that the available vertical “space” within the minor diameter is constrained (say, the maximum feasible pitch is on the order of \(2r\)), a reasonable working hypothesis is that the optimum occurs when the product

\[
N \cdot p \quad\text{(net vertical projection)}
\]

is maximized. Under certain assumptions (for example, if the helical pitch is forced by structural constraints so that

\[
p \,\propto\, \frac{1}{N}\quad\text{or} \quad p = \frac{2\pi\,(R+r)}{N_\mathrm{opt}},
\]

then a balance can be found when

\[
N_\mathrm{opt} \;\approx\; \frac{2\pi\,(R+r)}{p}.
\]

If one chooses a pitch \(p\) close to the maximum available vertical space (for instance, on the order of \(2r\) or a fraction of it), then an approximate optimum number of turns is

\[
N_\mathrm{opt} \;\approx\; \frac{2\pi\,(R+r)}{2r} \;=\; \frac{\pi\,(R+r)}{r}.
\]

It is important to emphasize that this relationship is based on an idealized geometry and assumes that the magnetic field and current distribution along the winding yield a relatively uniform Lorentz force per unit length. In practice, additional factors such as current distribution, resistive and dielectric losses, mechanical limitations, and the precise relationship between the toroidal envelope and the effective pitch come into play. Thus, designers typically use iterative numerical simulations—employing the equations for the helix geometry, the Lorentz force (\( \mathbf{F} = q \bigl(\mathbf{E} + \mathbf{v} \times \mathbf{B}\bigr) \)), and the Biot–Savart law—to fine-tune N for a given set of parameters. For further details on winding design principles, transformer winding theory (which shares similarities with toroidal coil designs) provides deeper insights.[(Electric Power Transformer Engineering)](https://uodiyala.edu.iq/uploads/PDF%20ELIBRARY%20UODIYALA/EL23/Electric%20Power%20Transformer%20Engineering%20(James%20H.%20Harlow)2.pdf) [(ARRL Antenna Compendium Volume 1)](https://dn790005.ca.archive.org/0/items/arrlacv3/ARRL_AC_v1.pdf)

---

## 2. On the Nature of the Current in the Helical Winding

For ion wind lifter devices, the generation of corona discharge—and hence the production of the ionic wind—typically depends on a high-voltage DC supply. In such configurations, the current used in the helical winding (whether it is used to generate a magnetic field or to couple to another part of the circuit) is generally **static (DC)** rather than an AC or pulsed current. There are several reasons for this:

- **Steady Force Production:**  
  A DC current produces a static magnetic field. A steady magnetic field is crucial if you wish to have a net, unidirectional Lorentz force that consistently projects an upward component. Fluctuating fields (from AC) can lead to oscillatory forces that, on average, cancel out or create instability.

- **Electrohydrodynamic Considerations:**  
  The ionic wind produced by corona discharge benefits from a stable high-voltage DC field. Since the same supply is often used (or is closely related) for the operation of the lifter, it is practical to work with DC current throughout the system.

- **Simplification of the Design:**  
  Maintaining a static (DC) current simplifies both the electrical design and the mathematical modeling of the system. AC currents would force you to account for time-dependent effects (such as eddy currents and reactive components) that complicate the device behavior.

Thus, unless there is a particular design goal that calls for modulation (for instance, for controlled pulsing of the thrust), the standard and most practical implementation is to use a **static DC current** in the helical winding.

---

## Summary

- **Optimization Approach:**  
  The optimum number of turns in the helical winding is a balance between increasing the total conductor length (which tends to increase the net force) and maintaining a sufficient helix pitch (to maximize the vertical force component \( \sin\alpha \)). A simplified model yields an optimum when
  \[
  N_\mathrm{opt} \;\approx\; \frac{2\pi\,(R+r)}{p},
  \]
  which, if \(p\) is chosen on the order of \(2r\), provides
  \[
  N_\mathrm{opt} \;\approx\; \frac{\pi\,(R+r)}{r}.
  \]
  This derivation is idealized; real‐world optimization generally requires numerical simulation incorporating the full Lorentz force integral along the winding.

- **Nature of the Current:**  
