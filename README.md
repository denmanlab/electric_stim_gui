# STG5 and BRAINSBoard GUI
### This will be a quick guide on how to use all the different tools developed for the BRAINSBoard, STG5 and more!
![Top of the Board](images/BRAINSBoard_Side_Profile.png)
These are both useful tools used in conjunction with one another to easily allow for multi-channel stimulation of the NeuroNexus A1x16 16-Channel Electrode.

# BRAINSBoard:
## Purpose

The BRAINSBoard is a proprietary custom PCB that is designed to electronically switch between Cathode, Anode, Ground, and Floating states for 16 different electrode channels without physically interacting with the components during experiments. This enables:
- Stimulation at different loci in patterns.
- Grounding of every inactive pin to prevent noise.
- Use with a GUI designed for efficient pin switching during and between experiments.

## Components of the Board
![Top of the Board](images/BRAINSBoard_Top_Labelled.png)
### Connectors
- $\text{color{yellow}Raspberry Pi/Arduino 2x20 Female Header}$ facilitates connections to control and process data from Arduino/Raspberry Pi. 2x20 90º Male Header allows external connections to unused/useful pins
  - Raspberry Pi can be directly connected on top of the 2x20 Female Header. Connection Pinout as follows:


![Raspberry Pi to Brainsboard Connection](images/RPI_2_BB_Pinout.png)
  - An Arduino can be connected to those same pins with the following Pinout (demonstrated with Arduino Pro Mini):
 
![Arduino Pro Mini to Brainsboard Connection](images/BB2ProMicro_bb.png)
  - Other tools (ie. sensors, actuators, external triggers) can be accessed from the 2x20 90º Male Header with the following Pinout:


![Brainsboard Connection to External Pins](images/BB_2_external_pins_Pinout.png)
- $\text{\color{white}NeuroNexus}$ Standard 2x8 Box Connectors with grounding on all top pins to minimize noise. Pinout:



![Box Headers Pinout](images/eStim_CONNECTORS.png)
- $\text{\color{red}Banana Connectors:}$ Connects to cathode and anode pulses from an Isolated Analog Power Stimulator (preferred STG5) and a Signal Ground that can be connected to the same common ground as the electrode and stimulator.

### $\text{\color{#FF69B4}Octal Transparent D-Type Latch}$
- Requires a VCC +5V and ground.
- Output Enable and Latch Enable controls, connected to Arduino/Raspberry Pi, to manage pin outputs.

### $\text{\color{orange}Analog SP3T Switch}$
- Two inputs determine the current path (cathode, anode, ground, or floating).
- Output directed through a connector managing pin outputs.

### $\text{\color{cyan}Solid State Relay}$
- Activated by a control switch, it powers an LED internally, which in turn activates a photosensitive diode to close the circuit.

### $\text{\color{white}Solid State Relay}$
This work was supported by NIH NINDS project number 1R01NS120850
