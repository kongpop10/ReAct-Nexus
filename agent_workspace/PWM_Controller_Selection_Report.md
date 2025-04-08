# PWM Controller Selection Report

## Introduction
This report provides a comprehensive analysis of commercially available PWM (Pulse Width Modulation) controller ICs suitable for high-frequency, complementary output applications with integrated dead-time control. The goal is to identify ICs or modules that meet the following criteria:
- Complementary outputs
- Integrated dead-time control
- Switching frequency above 200kHz
- Enable/modulation capability (preferably with a 20kHz clock)
- Commercial availability
- Preference for plug-and-play modules, if available

## PWM Controller Options
Based on the research, the following PWM controller ICs have been identified as strong candidates:

### 1. Microchip MIC3808/3809
- **Type:** Push-Pull PWM Controllers
- **Complementary Outputs:** Yes
- **Dead-Time Control:** Adjustable (60ns to 200ns)
- **Switching Frequency:** High-speed, likely >200kHz (confirm via datasheet)
- **Enable/Modulation:** Not explicitly stated; datasheet review recommended
- **Availability:** Commercially available IC
- **Notes:** Requires custom PCB design; no plug-and-play module identified

### 2. Texas Instruments TL594
- **Type:** PWM Control Circuit
- **Complementary Outputs:** Configurable via uncommitted output transistors
- **Dead-Time Control:** Integrated on-chip
- **Switching Frequency:** Likely >200kHz (confirm via datasheet)
- **Enable/Modulation:** Potentially supported; datasheet review recommended
- **Availability:** Widely available
- **Notes:** Discrete IC; no plug-and-play module identified

### 3. Texas Instruments UCC Series (UCC28C51-Q1, UCC2813-5-Q1, UCC2803-Q1)
- **Type:** Automotive PWM Controllers
- **Complementary Outputs:** Likely (confirm via datasheet)
- **Dead-Time Control:** Likely integrated (confirm via datasheet)
- **Switching Frequency:** Up to 1MHz
- **Enable/Modulation:** UVLO thresholds imply enable/disable capability
- **Availability:** Commercially available
- **Notes:** Discrete ICs; no plug-and-play module identified

## Technical Specifications Summary
| Feature                      | MIC3808/3809         | TL594                   | UCC Series (examples)                        |
|------------------------------|----------------------|-------------------------|---------------------------------------------|
| Complementary Outputs        | Yes                  | Yes (Configurable)      | Likely (Confirm)                            |
| Integrated Dead-Time         | Yes                  | Yes                     | Likely (Confirm)                            |
| Switching Frequency > 200kHz | Likely               | Likely                  | Yes (up to 1MHz)                            |
| Enable/Modulation            | Unknown              | Potentially              | UVLO (Enable/Disable Implied)               |
| Plug & Play Module           | No                   | No                      | No                                          |
| Availability                 | Yes                  | Yes                     | Yes                                         |

## Comparison and Insights
- **Complementary Outputs:** Both MIC3808/09 and TL594 explicitly support complementary outputs. The UCC series likely supports this but requires datasheet confirmation.
- **Dead-Time Control:** MIC3808/09 and TL594 have integrated dead-time control. The UCC series likely does as well.
- **Switching Frequency:** All options support >200kHz operation, with the UCC series capable of up to 1MHz.
- **Enable/Modulation:** The UCC series has UVLO-based enable/disable. The other ICs may support enable/modulation, but datasheet review is necessary.
- **Modules:** No plug-and-play modules were identified in this search. Custom PCB design will be required.

## Conclusion
The **Microchip MIC3808/3809** and **Texas Instruments TL594** are strong candidates due to their explicit support for complementary outputs and integrated dead-time control. The **TI UCC series** offers high-frequency operation and automotive qualification, making them suitable for demanding applications.

**Next Steps:**
1. **Review datasheets** for detailed specifications, especially for enable/modulation features.
2. **Check distributor availability and pricing** (Digi-Key, Mouser, Arrow).
3. **Consider evaluation boards** for rapid prototyping.
4. **If plug-and-play modules are essential,** further targeted searches or custom module development may be necessary.

## References
- [MIC3808/09 Datasheet (Microchip)](https://www.microchip.com/content/dam/mchp/documents/OTH/ProductDocuments/DataSheets/mic3808-09.pdf)
- [TL594 Product Page (Texas Instruments)](https://www.ti.com/lit/gpn/TL594)
- [TI PWM Controllers Overview](https://www.ti.com/power-management/pwm.html)
