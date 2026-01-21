# Scripts to plot data obtained from the control the FLC-Hybrot by a living CPG
Data used in manuscript:

> Hybrot validation of a neural sequential dynamical principle for autonomous coordination. Rodrigo Amaducci, Irene Elices, Pablo Sanchez-Martin, Alicia Garrido-Peña, Manuel Reyes-Sanchez, Carlos Garcia-Saura, Rafael Levi, Francisco B. Rodriguez, Pablo Varona


Can be found at:



Please, download the files directly to a data path to run the scripts and generate the Figures 3, 4, 5 and 7 in the manuscript.

This data directory should look like:

    data/
    ├── legs_tracking/
    ├── recordings/
    ├── videos/
    ├── cpgbot.mp4
    ├── intervals_data.txt
    └── legs-tracking.txt


To generate Figure 3 and 7 run:

    cd invariants
    python3 plot_record_video.py

    
To generate Figure 4 run:

    cd invariants
    python3 plot_record_video_invariants.py

To generate Figure 5 run:
    
    cd speed_test
    python3 generate_figures.py


Video tracking data is already available but can also be obtained again by running:

    python3 invariants/tracking.py
    python3 speed_test/tracking_body_leg.py data/videos/experimentN.mp4

    
