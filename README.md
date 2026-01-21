# FLC-Hybrot
This repository contains all the code necessary to run the FunctionalLivingCircuit(FLC)-Hybrot. The oscillation ranges of the motors of this hexapod robot are controlled online in **real-time** by the neural activity of a functional living circuit and includes a external light input from the context modifying the activity by a closed-loop connection.

This repository is associated to the following pulication:

> Hybrot validation of a neural sequential dynamical principle for autonomous coordination. Rodrigo Amaducci, Irene Elices, Pablo Sanchez-Martin, Alicia Garrido-Peña, Manuel Reyes-Sanchez, Carlos Garcia-Saura, Rafael Levi, Francisco B. Rodriguez, Pablo Varona

## Code structure
### Arduino controller
  - Contains code necessary to operate the oscillators, connect to the bluetooth and handle the photoreceptor.
  - Folder `photoreceptor`

### Real-time controller
  - Handles:
    1. Real-time recording of the neural activity
    2. Events detection
    3. Bi-directional bluetooth connection to the robot
  - Folders:
      `src`
      `lib`
  - Runs with: `Makefile`
    *Warning: This software only works in a Real-time operative system, it was designed and tested in Debian 9 with kernel 4.9.0-4 and Preempt-RT* 
  - Visualization utils:
      `plot_controller.py`
      `plot_record_video.py`
### Data Analysis
  - Scripts for analysis in Python for invariants translation and for the speed stability in the robot's movement. This scripts where used for the Figures in the published work associated to this repository. Follow the instructions in data-analysis/data/README.md to reproduce them. 
  - Folder: `data-analysis`

## System versions

- Computer: 4-core Intel Core i7-6700 3.40 GHz processor and 16 GB RAM. 
- Operating system: Debian 9 with kernel 4.9.0-4 and Preempt-RT real-time patch.
- Bluetooth device: external USB Nano Stick v4.0 antenna.
- Bluetooth protocol: BlueZ 5.43, the open-source official Linux Bluetooth protocol stack.
- Control software: C++ and compiled with G++ 6.3.
- Communication with National Instruments board: Comedi 0.7.76 drivers.
- Data transfer to the robot: the open-source LibSerial 1.0.0 library.

## Robot printing
The model for the robot can be found at: Micro-Hexapod by Ijon https://www.thingiverse.com/thing:5156

Printed using a Prusa i3 3D printer.

List of periferical devices attatch to Arduiono BQ Zum Core:
- Photoresistor for light detection
- Atmel ATMEGA328P
- LEDs
