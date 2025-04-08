Based on the web search results provided, here's an analysis of commercially available PWM controller ICs that meet your specified criteria.  It's important to note that the initial search results are snippets and may not provide the complete picture. For a definitive assessment, consulting the full datasheets is recommended.

Here's a breakdown of the identified ICs and how they align with your requirements:

# 1. Microchip MIC3808/3809 Push-Pull PWM Controllers

* **Source:** [MIC3808/09 Datasheet (PDF)](https://www.microchip.com/content/dam/mchp/documents/OTH/ProductDocuments/DataSheets/mic3808-09.pdf)
* **Complementary Outputs:** Yes, explicitly described as "complementary output push-pull PWM control ICs." This is a primary feature.
* **Integrated Dead-Time Control:** Yes, features adjustable dead-time between 60ns to 200ns. This is a key requirement and is met.
* **Switching Frequency > 200kHz:** While the snippet doesn't explicitly state the maximum switching frequency, it's described as "high speed" and "ideal for telecom." Telecom applications often require switching frequencies in the hundreds of kHz range and sometimes MHz. Therefore, it's highly likely these ICs can operate above 200kHz. *To confirm, the datasheet should be consulted for the exact frequency range.*
* **Enable/Modulation:** The snippet doesn't explicitly mention an enable/disable input or modulation capability with a 20kHz clock. *The datasheet needs to be reviewed to determine if such features exist. However, PWM controllers often have shutdown or enable pins, and modulation might be achievable through external circuitry or pin configurations.*
* **Availability:** These are ICs from Microchip, a major semiconductor manufacturer, suggesting they are commercially available. You can check distributor websites like Digi-Key, Mouser, or Arrow to confirm stock and pricing.
* **Plug and Play Modules:** These are discrete ICs, not plug-and-play modules. To use them, you would need to design a circuit board and implement the necessary external components.

# 2. Texas Instruments TL594 Pulse-Width-Modulation Control Circuit

* **Source:** [TL594 Product Page (TI.com)](https://www.ti.com/lit/gpn/TL594)
* **Complementary Outputs:** Yes, it has "uncommitted output transistors" that can be configured for "common-emitter or emitter-follower output capability." This allows for creating complementary outputs.
* **Integrated Dead-Time Control:** Yes, explicitly includes an "on-chip dead-time control (DTC) comparator" for adjustable dead-time. This meets the requirement.
* **Switching Frequency > 200kHz:** The TL594 has an "on-chip adjustable oscillator." While the snippet doesn't specify the maximum frequency, the TL594 is a versatile and widely used PWM controller. *It is likely capable of exceeding 200kHz, but the datasheet should be checked for the oscillator frequency range to confirm.*
* **Enable/Modulation:** It includes a "pulse-steering control flip-flop" and "output control circuitry." This suggests flexibility in controlling and potentially modulating the PWM output. *The datasheet would be crucial to understand the modulation capabilities and if a direct enable/disable pin exists or how to implement it.*
* **Availability:** The TL594 is a very popular and long-standing PWM controller from Texas Instruments. It is highly likely to be readily available from various distributors.
* **Plug and Play Modules:** Similar to the MIC3808/3809, the TL594 is a discrete IC. Plug-and-play modules based on the TL594 might exist from third-party vendors, but the search results don't directly point to them. You would typically need to design a circuit around the TL594 IC.

# 3. Texas Instruments Automotive PWM Controllers (UCC Series - UCC28C51-Q1, UCC2813-5-Q1, UCC2803-Q1)

* **Source:** [Pulse-width modulation | TI.com](https://www.ti.com/power-management/pwm.html) (General PWM overview page, listing examples)
* **Complementary Outputs:** The snippet doesn't explicitly state "complementary outputs" for these specific UCC series controllers. However, PWM controllers in general, and especially those used in power conversion, often support push-pull or half-bridge/full-bridge topologies which require complementary drive. *Datasheets for these specific UCC models would need to be consulted to confirm complementary output capability.*
* **Integrated Dead-Time Control:** Not specified in the snippet. *Again, datasheets are needed to confirm if integrated dead-time control is present in these specific UCC series controllers.*
* **Switching Frequency > 200kHz:** Yes, the snippet mentions "1MHz current mode PWM controller" for UCC2813-5-Q1 and UCC2803-Q1. UCC28C51-Q1 is also likely to operate at frequencies above 200kHz. This requirement is met.
* **Enable/Modulation:** The snippet mentions "UVLO (Undervoltage Lockout) thresholds," which implies an enable/disable functionality based on the input voltage. *Datasheets would detail the UVLO and any other enable/disable or modulation features.*
* **Availability:** These are automotive-qualified ICs from Texas Instruments, indicating commercial availability. Check distributor websites for stock.
* **Plug and Play Modules:** These are also discrete ICs, not plug-and-play modules.

# Summary and Best Matching Options

| Feature                      | MIC3808/3809         | TL594                   | UCC28C51-Q1, UCC2813-5-Q1, UCC2803-Q1          |
|------------------------------|----------------------|-------------------------|-----------------------------------------------|
| Complementary Outputs        | Yes                  | Yes (Configurable)      | Likely (Needs Datasheet Confirmation)         |
| Integrated Dead-Time         | Yes                  | Yes                     | Likely (Needs Datasheet Confirmation)         |
| Switching Frequency > 200kHz | Likely               | Likely                  | Yes (Up to 1MHz)                              |
| Enable/Modulation            | Unknown              | Potentially              | UVLO (Enable/Disable Implied)                 |
| Plug & Play Module           | No                   | No                      | No                                            |
| Availability                 | Likely               | Likely                  | Likely                                        |

# Recommendations and Next Steps

1. **Prioritize ICs over Modules:** The search results primarily point to ICs, and plug-and-play modules meeting all your specific criteria were not readily identified in this initial search. If modules are absolutely essential, you might need to broaden your search terms or look for custom module manufacturers.
2. **Download and Review Datasheets:** For the MIC3808/3809, TL594, and the UCC series (especially UCC28C51-Q1, UCC2813-5-Q1, UCC2803-Q1), download the full datasheets from the manufacturer websites (Microchip and Texas Instruments). *Pay close attention to:*
   * Maximum switching frequency and how to set it.
   * Detailed specifications of the dead-time control and adjustment.
   * Presence of enable/disable pins or methods.
   * Modulation capabilities and how to implement modulation with a 20kHz signal (if needed).
   * Output drive capabilities and suitability for your load.
3. **Check Distributor Availability and Pricing:** Once you have narrowed down your choices based on the datasheets, check the availability and pricing of the ICs at major distributors like Digi-Key, Mouser, Arrow, etc. This will confirm commercial availability and help you compare costs.
4. **Consider Evaluation Boards:** For easier prototyping and testing, check if evaluation boards are available for the selected ICs. These boards often provide a basic circuit implementation and test points, which can speed up your development process.

# Conclusion

The **Microchip MIC3808/3809** and **Texas Instruments TL594** appear to be strong candidates based on the initial search results, as they explicitly mention complementary outputs and dead-time control. The **Texas Instruments UCC series** (especially the 1MHz versions) also meets the frequency requirement and offers potential enable/disable via UVLO, but requires datasheet verification for complementary outputs and dead-time control.

For all options, **reviewing the datasheets is crucial** to confirm all specifications and features, especially the enable/modulation capabilities and the achievable switching frequency in your specific application. If plug-and-play modules are a strict requirement, further targeted searching for modules incorporating these ICs or similar controllers might be necessary, or you may need to consider designing your own module based on a suitable IC.

# Sources

* [MIC3808/09 Datasheet (PDF)](https://www.microchip.com/content/dam/mchp/documents/OTH/ProductDocuments/DataSheets/mic3808-09.pdf)
* [TL594 Product Page (TI.com)](https://www.ti.com/lit/gpn/TL594)
* [Pulse-width modulation | TI.com](https://www.ti.com/power-management/pwm.html)
