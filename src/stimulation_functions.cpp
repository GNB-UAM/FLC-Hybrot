#include "../includes/stimulation_functions.h"


void gradual_current (Params * params, double * output_values, double target_current, float current_factor) {
	//output_values[0] = target_current;
	//return;


	if (params->max_current > 0) { 						// The current to inject is positive
		if (target_current == 0) { 						// The target now is 0
			if (output_values[0] > 0) { 				// Decrease until 0
				output_values[0] -= (params->max_current / params->freq)*current_factor;
			} else {
				output_values[0] = 0.0;
			}
		} else { 										// The target now is positive
			if (output_values[0] < target_current) { 	// Increase until max_current
				output_values[0] += (params->max_current / params->freq)*current_factor;
			} else {
				output_values[0] = target_current;
			}
		}
	} else if (params->max_current < 0) {				// The current to inject is negative
		if (target_current == 0) { 						// The target now is 0
			if (output_values[0] < 0) { 				// Increase until 0
				output_values[0] -= (params->max_current / params->freq)*1;
			} else {
				output_values[0] = 0.0;
			}
		} else {										// The target now is negative
			if (output_values[0] > target_current) {	// Decrease until max_current
				output_values[0] += (params->max_current / params->freq)*current_factor;
			} else {
				output_values[0] = target_current;
			}
		}
	}
} 
