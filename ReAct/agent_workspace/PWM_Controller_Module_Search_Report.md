Based on the web search and analysis, finding a readily available, plug-and-play module that perfectly matches all your specified criteria – complementary outputs, integrated dead-time control, switching frequency exceeding 200kHz per output, and an enable/disable or 20kHz modulation input – appears to be challenging.  The search results primarily point towards discrete IC solutions and microcontroller-based implementations rather than pre-built modules.

Let's break down the findings and explore potential solutions, focusing on discrete ICs as plug-and-play modules are less apparent for these specific requirements:

**Analysis of Search Results:**

* **Electronics Stack Exchange Question:** This link ([https://electronics.stackexchange.com/questions/295938/how-to-generate-complementary-pwm-signal-using-an-ic-integrated-circuit](https://electronics.stackexchange.com/questions/295938/how-to-generate-complementary-pwm-signal-using-an-ic-integrated-circuit)) directly addresses the need for generating complementary PWM with dead-time using an IC.  While it doesn't recommend specific ICs, it confirms the existence of such devices and hints at basic implementation methods using logic gates and delay circuits. This suggests that dedicated ICs for this purpose are available, but might require component-level design rather than plug-and-play modules.

* **STM32 Complementary PWM Example:** The STM32 tutorial ([https://deepbluembedded.com/stm32-complementary-pwm-dead-time-code-examples/](https://deepbluembedded.com/stm32-complementary-pwm-dead-time-code-examples/)) demonstrates how to achieve complementary PWM with dead-time using an STM32 microcontroller.  While STM32s are powerful and versatile, they are not plug-and-play PWM controller *modules*. They are programmable microcontrollers that *can be configured* to generate the desired PWM signals. This is a chip-level solution requiring firmware development and potentially additional external components for signal conditioning.  It meets the technical requirements but not the "plug-and-play module" preference.

* **Texas Instruments PWM Overview:** The TI PWM page ([https://www.ti.com/power-management/pwm.html](https://www.ti.com/power-management/pwm.html)) is a broad overview of TI's PWM controller offerings. It highlights various applications and features of their PWM controllers, including high-performance and automotive-grade options.  This page is a starting point for exploring TI's product catalog but doesn't directly list specific ICs meeting *all* your criteria in a readily searchable format.

**Potential Discrete IC Solutions (Based on Analysis and General Knowledge):**

Considering the criteria and the nature of PWM controllers, here are potential directions for finding suitable discrete ICs, even though plug-and-play modules are not readily identified:

1. **Dedicated PWM Controller ICs for Power Conversion:**  ICs designed for synchronous rectification, motor control, and power supply applications are highly likely to include complementary PWM outputs and dead-time control.  These are often optimized for efficiency and high switching frequencies.

    * **Texas Instruments (TI) LM5045:** As mentioned in the analysis, the LM5045 is a strong candidate. It's a Push-Pull PWM controller designed for high-frequency operation and includes adjustable dead-time and complementary outputs.  Datasheet verification is crucial to confirm it meets the >200kHz frequency and enable/modulation input requirements.  You can find information and purchase options on TI's website and distributors like Digi-Key, Mouser, and Arrow Electronics.

    * **Other TI PWM Controllers:** Explore TI's portfolio further using their parametric search tools on their website. Filter for "PWM Controllers," "Complementary Outputs," "Dead-Time Control," and frequency capabilities. Look at families like UCC28xxx, UCC38xxx, and similar series focusing on power management.

    * **Analog Devices (formerly Linear Technology) and Infineon:**  These manufacturers also produce high-performance PWM controller ICs. Explore their websites using similar parametric search strategies. Look for ICs targeting synchronous rectification, full-bridge converters, and motor drivers.

2. **Gate Driver ICs with Integrated PWM Control:** Some advanced gate driver ICs incorporate PWM generation capabilities, including complementary outputs and dead-time. These might be suitable if you need to drive external MOSFETs or IGBTs.

3. **Microcontrollers with Advanced PWM Peripherals:** While not a dedicated PWM controller IC, high-performance microcontrollers (like STM32 Advanced Timers mentioned in the STM32 link, or those from NXP, Microchip, etc.) offer highly configurable PWM generation capabilities, including complementary outputs, dead-time, and high frequencies.  If you need flexibility and are comfortable with microcontroller programming, this can be a powerful solution. However, it's not a plug-and-play module and requires firmware development.

**Regarding Enable/Disable or 20kHz Modulation:**

* **Enable/Disable Input:** Most dedicated PWM controller ICs and even gate driver ICs will have an Enable (EN) or Shutdown (SD) pin. This can be used for basic on/off control.

* **20kHz Modulation:**  Modulating the PWM output with a 20kHz clock signal is less standard for dedicated PWM controller ICs.  You might need to implement this externally.  Possible approaches include:
    * **Using the Enable/Disable pin with a 20kHz signal:** If the enable pin has a fast enough response time, you could directly modulate it with a 20kHz square wave. This would effectively gate the PWM output at 20kHz.
    * **Voltage Controlled Oscillator (VCO) or Frequency Modulation (FM) input (if available):** Some advanced PWM controllers might have inputs to modulate the frequency or duty cycle. You could potentially use a 20kHz signal to modulate the duty cycle or frequency, although this might be more complex to implement precisely.
    * **External Logic Gating:** You could generate the PWM signal from a controller IC that meets the other criteria and then use external logic gates (like AND gates) to gate the PWM output with a 20kHz signal. This adds external components but provides the desired modulation.

**Plug-and-Play Modules vs. Discrete ICs:**

The search suggests that for your specific combination of high frequency, complementary outputs, dead-time, and modulation/enable requirements, readily available plug-and-play modules are less common.  You are more likely to find discrete IC solutions that meet these specifications.  Using discrete ICs will require designing a circuit board and integrating the IC into your system, but it offers more flexibility and potentially better performance for specialized applications.

**Recommendations and Next Steps:**

1. **Focus on Discrete ICs:** Shift your primary focus to identifying suitable discrete PWM controller ICs from manufacturers like Texas Instruments, Analog Devices, and Infineon.

2. **Utilize Parametric Search Tools:** Use the parametric search tools on the websites of these manufacturers.  Specifically filter for:
    * Category: PWM Controllers, Power Management ICs, Gate Drivers
    * Features: Complementary Outputs, Dead-Time Control (Adjustable Dead-Time is preferable)
    * Switching Frequency:  > 200kHz (or specify a range like 200kHz - 1MHz or higher)
    * Enable/Disable Input: Look for ICs with EN, SD, or similar control pins.

3. **Review Datasheets Carefully:** Once you identify potential ICs, download and thoroughly review their datasheets.  Pay close attention to:
    * Maximum Switching Frequency
    * Dead-Time Adjustment Range and Method
    * Complementary Output Specifications
    * Enable/Disable Pin Functionality and Response Time
    * Application Examples and Recommended Circuitry

4. **Check Distributor Availability:** After identifying suitable ICs, check their availability and pricing at major distributors like Digi-Key, Mouser, Arrow Electronics, and Farnell.  Look for "in-stock" or short lead times for readily available options.

5. **Consider Evaluation Boards (if available):** Some manufacturers offer evaluation boards for their PWM controller ICs. These can be helpful for prototyping and testing the IC's functionality before designing your own PCB.

6. **For Modulation, Consider External Circuitry:** If direct 20kHz modulation is critical and not readily available within a single IC, be prepared to implement the modulation externally using logic gates or by utilizing the enable pin strategically.

**In conclusion, while plug-and-play modules meeting all your stringent criteria are not immediately apparent from the search, dedicated PWM controller ICs, particularly from manufacturers specializing in power management, are the most promising avenue. Focus your search on discrete ICs and utilize parametric search tools and datasheets to find the best fit for your application.**

**Sources:**

- [How to generate complementary PWM signal using an IC (integrated circuit)? - Electrical Engineering Stack Exchange] (https://electronics.stackexchange.com/questions/295938/how-to-generate-complementary-pwm-signal-using-an-ic-integrated-circuit)
- [STM32 Complementary PWM & Dead-Time (Code Examples) - Deepbluembedded] (https://deepbluembedded.com/stm32-complementary-pwm-dead-time-code-examples/)
- [Pulse-width modulation | TI.com - Texas Instruments] (https://www.ti.com/power-management/pwm.html)