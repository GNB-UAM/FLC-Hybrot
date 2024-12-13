# FLC-Hybrot
This repository contains all the code necessary to run the FunctionalLivingCircuit(FLC)-Hybrot. The oscillation ranges of the motors of this hexapod robot are controlled online in **real-time** by the neural activity of a functional living circuit and includes a external light input from the context modifying the activity by a closed-loop connection.

This repository is associated to the following pulication:
Robotic motion controlled by neural sequential dynamical invariants of a living CPG with sensory feedback from the robot. 


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
  - Scripts for analysis in Python for the speed stability in the robot's movement
  - Folder: `speed_tests`
