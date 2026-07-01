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
    *Warning: This software only works in a Real-time operative system, it was designed and tested in Debian 9 with kernel 4.9.0-6 and Preempt-RT* 
  - Visualization utils:
      `plot_controller.py`
      `plot_record_video.py`
### Data Analysis
  - Scripts for analysis in Python for invariants translation and for the speed stability in the robot's movement. This scripts where used for the Figures in the published work associated to this repository.

**Follow the instructions in [data-analysis/data/README.md](data-analysis/data/README.md) to reproduce them or generate new Figures based on your own data.**
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


## How to run the controller
Once the realtime system is ready, open a terminal and change to FLC-Hybrot directory. For example:
    
    cd Desktop/FLC-Hybrot/

Then follow this steps:

  1. Compile the code with make

    make

  2. Run the controller command with sudo, you can include a safety make in case you do any changes in the code before running:
    
     make; sudo ./controller -i 4,2 -o 0 -p /dev/rfcomm0 -l 20 -F 1 -c -0.3 -L 0.3 -U 0.7 -t 90


Note: you can see a description of the parameters by runnning:

    ./controller -h

To display the results first activate the environment:

    conda activate hybrot

and then run the plotter to display last file result

    python plot_controller.py data/2026y_6m_23d/16h_55m_56s.txt

You can find the filename at the end of the experiment, you will see something like:

  > Ended experiment. Saving data to file...
Filename: data/2026y_6m_25d/13h_6m_35s.txt
Data saved!



