# STG5 and BRAINSBoard GUI
### This will be a quick guide on how to use all the different tools developed for the STG5, BRAINSBoard, and more!

## Purpose

The board was created to electronically switch between electrodes (cathode, anode, and inactive) without physically interacting with the components during experiments. This enables:
- Stimulation in patterns.
- Grounding of every inactive pin to prevent noise.
- Use with a GUI designed for efficient pin switching.

## Components of the Board
![Top of the Board](images/BRAINSBoard_Top_Labelled.png)
### Connectors
- **Raspberry Pi/Arduino and Neuro Nexus:** Facilitates connections to control and process data.
- **Banana Connectors:** Connects to cathode and anode pulses from the Isolated Analog Power Stimulator and ground.

### Electronic Parts
1. **40-Pin Female Header:** Allows flexibility and attachment to various rigs.
2. **16 Pin Straight Box Header:** Direct connection to Raspberry Pi, facilitating easy connections to an Arduino.
3. **Octal Transparent D-Type Latch with 3-State Output:** Controls the logic of cathode, anode, and inactive pins with minimal physical pins.
4. **Analog SP3T Switch:** Allows selection between cathode, anode, or ground without risking electronic interference.
5. **Solid State Relays:** Provides electrical isolation and protection, ensuring that no current leaks between the components.
6. **Resistors/Capacitors:** Used to manage the internal LED's power to prevent burning out.

## How It Works

### $\text{\color{#FF69B4}Octal Transparent D-Type Latch}$
- Requires a VCC +5V and ground.
- Output Enable and Latch Enable controls, connected to Arduino/Raspberry Pi, to manage pin outputs.

### $\text{\color{orange}Analog SP3T Switch}$
- Two inputs determine the current path (cathode, anode, ground).
- Output directed through a connector managing pin outputs.

### $\text{\color{cyan}Solid State Relay}$
- Activated by a control switch, it powers an LED internally, which in turn activates a photosensitive diode to close the circuit.
