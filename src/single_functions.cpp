#include "../includes/single_functions.h"

using namespace LibSerial;

int init_params_single (Params ** params, int duration, SerialStream * serial_stream, double th_lo_per_pd, double th_up_per_pd, double th_lo_per_lp, double th_up_per_lp) {
	*params = (Params *) malloc (sizeof(Params));
	Params * aux_params = *params;

	aux_params->serial_stream = serial_stream;
	aux_params->experiment_type = 0;
	aux_params->n_in_chan = 1;
	aux_params->channels = (Channel *) malloc (sizeof(Channel));

	aux_params->channels[0].min = 999999;
	aux_params->channels[0].max = -999999;
	aux_params->channels[0].min_window = 999999;
	aux_params->channels[0].max_window = -999999;
	aux_params->channels[0].flag = 0;
	aux_params->channels[0].th_lo_per = th_lo_per_pd;
	aux_params->channels[0].th_up_per = th_up_per_lp;

	aux_params->data = (double **) malloc (sizeof(double *) * 6);
	aux_params->data[REALTIME] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[CURRENT] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[SINGLE_NEURON_PERIOD] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[SINGLE_NEURON_V] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[SINGLE_COUNTER] = (double *) malloc (sizeof(double));
	aux_params->data[SINGLE_LAST_PERIOD] = (double *) malloc (sizeof(double));
	aux_params->data[SINGLE_COUNTER][0] = 0;
	aux_params->data[SINGLE_LAST_PERIOD][0] = 0;

	return OK;
} 

void free_params_single (Params ** params) {
	Params * aux_params = *params;

	free(aux_params->data[REALTIME]);
	free(aux_params->data[CURRENT]);
	free(aux_params->data[SINGLE_NEURON_PERIOD]);
	free(aux_params->data[SINGLE_NEURON_V]);
	free(aux_params->data[SINGLE_COUNTER]);
	free(aux_params->data[SINGLE_LAST_PERIOD]);
	free(aux_params->data);

	free(aux_params->channels);

	free(*params);
}


void update_min_max_window_single_first (Params * params, double * input_values) {
	if (input_values[0] > params->channels[0].max_window) params->channels[0].max_window = input_values[0];
    if (input_values[0] < params->channels[0].min_window) params->channels[0].min_window = input_values[0];
}

void update_min_max_window_single (Params * params, double * input_values) {
	double min = params->channels[0].min;
	double max = params->channels[0].max;
	double range = params->channels[0].range;

	if ((input_values[0] > params->channels[0].max_window) && (input_values[0] < (max + range))) params->channels[0].max_window = input_values[0];
    if ((input_values[0] < params->channels[0].min_window) && (input_values[0] > (min - range))) params->channels[0].min_window = input_values[0];
}


void burst_detection_single (Params * params, double * input_values, int i) {
	Channel * aux_chan = &(params->channels[0]);
	double ** data = params->data;
	int burst_dur = 0;

	data[SINGLE_COUNTER][0]++;

	if (input_values[0] > aux_chan->th_up && aux_chan->flag == 1) {
		aux_chan->flag = 0;
		data[SINGLE_LAST_PERIOD][0] = data[SINGLE_COUNTER][0];
		burst_dur = data[SINGLE_COUNTER][0] / 10;
		*(params->serial_stream) << burst_dur << std::endl;
		data[SINGLE_COUNTER][0] = 0;
	} else if (input_values[0] < aux_chan->th_lo && aux_chan->flag == 0) {
		aux_chan->flag = 1;
	}

	data[SINGLE_NEURON_PERIOD][i] = data[SINGLE_LAST_PERIOD][0] / 10000.0;
	data[SINGLE_NEURON_V][i] = input_values[0];
}


void write_to_file_single (Params * params, int duration, char * filename) {
	int i;
	double ** data = params->data;

    FILE * f = fopen(filename, "w");

    fprintf(f, "0\nth_lo_per %.2f th_up_per %.2f\n", params->channels[0].th_lo_per, params->channels[0].th_up_per);

	for (i = 0; i < duration; i++) {
		fprintf(f, "%.0f %f %f %f\n", data[REALTIME][i], data[CURRENT][i], data[SINGLE_NEURON_PERIOD][i], data[SINGLE_NEURON_V][i]);
	}

	fclose(f);
}