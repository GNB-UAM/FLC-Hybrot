#include "types.h"

#define SINGLE_NEURON_V 2
#define SINGLE_NEURON_PERIOD 3
#define SINGLE_COUNTER 4
#define SINGLE_LAST_PERIOD 5


int init_params_single (Params ** params, int duration, SerialStream * serial_stream, double th_lo_per_pd, double th_up_per_pd, double th_lo_per_lp, double th_up_per_lp);

void free_params_single (Params ** params);

void update_min_max_window_single (Params * params, double * input_values);

void update_min_max_window_single_first (Params * params, double * input_values);

void burst_detection_single (Params * params, double * input_values, int i);

void write_to_file_single (Params * params, int duration, char * filename);