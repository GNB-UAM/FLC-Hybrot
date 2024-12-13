#include "../includes/common_functions.h"

using namespace LibSerial;

int init_params (Params ** params, SerialStream * serial_stream, int experiment_type, int stimulation_type, 
	int n_in_chan, int duration, int freq, double max_current, double th_lo_per, double th_up_per) {
	if (experiment_type == EXP_SINGLE) { // Single
		if (n_in_chan >= 1) {
			init_params_single(params, duration, serial_stream, th_lo_per, th_up_per);
		} else {
			return ERR;
		}
	} else if (experiment_type == EXP_INVARIANT) { // Invariant
		if (n_in_chan >= 2) {
			init_params_invariant(params, duration, serial_stream, th_lo_per, th_up_per);
		} else {
			return ERR;
		}
	} else {
		printf("Not valid experiment type\n");
		return ERR;
	}

	(*params)->stimulation_type = stimulation_type;
	(*params)->freq = freq;
	(*params)->max_current = max_current;

	return OK;
}

void free_params (Params ** params) {
	if ((*params)->experiment_type == 0) {
		free_params_single(params);
	} else if ((*params)->experiment_type == 1) {
		free_params_invariant(params);
	}
}


void update_min_max_window (Params * params, double * input_values) {
	if (params->experiment_type == EXP_SINGLE) {
		update_min_max_window_single(params, input_values);
	} else if (params->experiment_type == EXP_INVARIANT) {
		update_min_max_window_invariant(params, input_values);
	}
}


void update_min_max_window_first (Params * params, double * input_values) {
	if (params->experiment_type == EXP_SINGLE) {
		update_min_max_window_single_first(params, input_values);
	} else if (params->experiment_type == EXP_INVARIANT) {
		update_min_max_window_invariant_first(params, input_values);
	}
}

void update_amplitude (Params * params) {
	int i;

	for (i = 0; i < params->n_in_chan; i++) {
		Channel * aux_chan = &(params->channels[i]);

		aux_chan->max = aux_chan->max_window;
		aux_chan->min = aux_chan->min_window;

    	aux_chan->range = aux_chan->max - aux_chan->min;
    	aux_chan->th_up = aux_chan->min + (aux_chan->range * aux_chan->th_up_per);
		aux_chan->th_lo = aux_chan->min + (aux_chan->range * aux_chan->th_lo_per);

		// printf("%f %f %f %f %f\n", aux_chan->th_up, aux_chan->th_lo,aux_chan->range , aux_chan->min_window, aux_chan->max_window );
		aux_chan->max_window = -999999;
        aux_chan->min_window = 999999;
	}
}


void burst_detection (Params * params, double * input_values, int i) {
	if (params->experiment_type == EXP_SINGLE) {
		burst_detection_single(params, input_values, i);
	} else if (params->experiment_type == EXP_INVARIANT) {
		burst_detection_invariant(params, input_values, i);
	}
}


void select_stimulus(Params * params, double * output_values, double target_current) {
	if (params->stimulation_type == GRADUAL_CURRENT) {
		gradual_current(params, output_values, target_current);
	}
}


void write_to_file (Params * params, int duration) {
	time_t t;
    struct tm tm;
    char * path = NULL;
    char * hour = NULL;
    char * filename = NULL;

	t = time(NULL);
    tm = *localtime(&t);

    asprintf(&path, "data/%dy_%dm_%dd", tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday);


    struct stat st = {0};

    umask(0000);

    if (stat("data", &st) == -1) {
        mkdir("data", 0777);
    }

    if (stat(path, &st) == -1) {
        mkdir(path, 0777);
    }

    asprintf(&hour, "/%dh_%dm_%ds", tm.tm_hour, tm.tm_min, tm.tm_sec);
    asprintf(&filename, "%s%s.txt", path, hour);

    printf("Filename: %s\n", filename);

	if (params->experiment_type == EXP_SINGLE) {
		write_to_file_single(params, duration, filename);
	} else if (params->experiment_type == EXP_INVARIANT) {
		write_to_file_invariant(params, duration, filename);
	}


	free(path);
	free(hour);
	free(filename);
}
