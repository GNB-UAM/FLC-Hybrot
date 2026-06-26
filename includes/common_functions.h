#include "single_functions.h"
#include "invariant_functions.h"
#include "stimulation_functions.h"

int init_params (Params ** params, SerialStream * serial_stream, int experiment_type, int stimulation_type, 
	int n_in_chan, int duration, int freq, double max_current, double th_lo_per, double th_up_per);

void free_params (Params ** params);

void update_min_max_window (Params * params, double * input_values);

void update_min_max_window_first (Params * params, double * input_values);

void update_amplitude (Params * params);

void burst_detection (Params * params, double * input_values, int i);

void select_stimulus(Params * params, double * output_values, double target_current, float current_factor);

char * write_to_file (Params * params, int duration);
