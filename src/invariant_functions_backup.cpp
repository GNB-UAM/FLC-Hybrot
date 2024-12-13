#include "../includes/invariant_functions.h"

using namespace LibSerial;

int init_params_invariant (Params ** params, int duration, SerialStream * serial_stream, double th_lo_per, double th_up_per) {
	*params = (Params *) malloc (sizeof(Params));
	Params * aux_params = *params;

	aux_params->serial_stream = serial_stream;
	aux_params->experiment_type = 1;
	aux_params->n_in_chan = 2;
	aux_params->channels = (Channel *) malloc (sizeof(Channel) * 2);

	aux_params->channels[INV_PD].min = 999999;
	aux_params->channels[INV_PD].max = -999999;
	aux_params->channels[INV_PD].min_window = 999999;
	aux_params->channels[INV_PD].max_window = -999999;
	aux_params->channels[INV_PD].flag = 0;
	aux_params->channels[INV_PD].th_lo_per = th_lo_per;
	aux_params->channels[INV_PD].th_up_per = 0.7;

	aux_params->channels[INV_LP].min = 999999;
	aux_params->channels[INV_LP].max = -999999;
	aux_params->channels[INV_LP].min_window = 999999;
	aux_params->channels[INV_LP].max_window = -999999;
	aux_params->channels[INV_LP].flag = 0;
	aux_params->channels[INV_LP].th_lo_per = 0.4;
	aux_params->channels[INV_LP].th_up_per = th_up_per;

	aux_params->data = (double **) malloc (sizeof(double *) * 12);

	aux_params->data[REALTIME] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[CURRENT] = (double *) malloc (sizeof(double) * duration);

	aux_params->data[INV_LP_TIMES] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_LP_PERIOD_TIMES] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_LP_V] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_LP_EVENT] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_LP_PERIOD_ALL] = (double *) malloc (sizeof(double) * duration);

	aux_params->data[INV_PD_V] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_PD_EVENT] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_LPPD_INTERVAL] = (double *) malloc (sizeof(double) * duration);

	aux_params->data[INV_LP_LAST_PERIOD] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_ARRAYS_SIZES] = (double *) calloc (3, sizeof(double));

	return OK;
}


void free_params_invariant (Params ** params) {
	Params * aux_params = *params;

	int i;
	for (i = 0; i < 12; i++) {
		free(aux_params->data[i]);
	}

	free(aux_params->channels);

	free(*params);
}


void update_min_max_window_invariant_first (Params * params, double * input_values) {
	if (input_values[INV_PD] > params->channels[INV_PD].max_window) params->channels[INV_PD].max_window = input_values[INV_PD];
    if (input_values[INV_PD] < params->channels[INV_PD].min_window) params->channels[INV_PD].min_window = input_values[INV_PD];

    double abs_input = fabs(input_values[INV_LP]);
    if (abs_input > params->channels[INV_LP].max_window) params->channels[INV_LP].max_window = abs_input;
    if (abs_input < params->channels[INV_LP].min_window) params->channels[INV_LP].min_window = abs_input;
}

void update_min_max_window_invariant (Params * params, double * input_values) {
	double min = params->channels[INV_LP].min;
	double max = params->channels[INV_LP].max;
	double range = params->channels[INV_LP].range;
	double abs_input = fabs(input_values[INV_LP]);

	if (abs_input > params->channels[INV_LP].max_window && (abs_input < (max + range))) params->channels[INV_LP].max_window = abs_input;
    if (abs_input < params->channels[INV_LP].min_window && (abs_input > (min - range))) params->channels[INV_LP].min_window = abs_input;

    min = params->channels[INV_PD].min;
	max = params->channels[INV_PD].max;
	range = params->channels[INV_PD].range;

	if (input_values[INV_PD] > params->channels[INV_PD].max_window && (input_values[INV_PD] < (max + range))) params->channels[INV_PD].max_window = input_values[INV_PD];
    if (input_values[INV_PD] < params->channels[INV_PD].min_window && (input_values[INV_PD] > (min - range))) params->channels[INV_PD].min_window = input_values[INV_PD];
}


void burst_detection_invariant (Params * params, double * input_values, int i) {
	double aux_pd = 0, aux_lp = 0;
	char buf[10];
	Channel * lp = &(params->channels[INV_LP]);
	Channel * pd = &(params->channels[INV_PD]);
	double ** data = params->data;

	int size_times_v_lp = data[INV_ARRAYS_SIZES][INV_SIZE_TIMES_V_LP];
	int size_lppd_interval = data[INV_ARRAYS_SIZES][INV_SIZE_LPPD_INTERVAL];
	int size_period = data[INV_ARRAYS_SIZES][INV_SIZE_PERIOD];

	/*if ((input_values[INV_PD] < (pd->max + pd->range)) && (input_values[INV_PD] > (pd->min - pd->range))) {
		data[INV_PD_V][i] = input_values[INV_PD];
	} else {
		data[INV_PD_V][i] = data[INV_PD_V][i-1];
	}
	

	if ((input_values[INV_LP] < (lp->max + lp->range)) && (input_values[INV_LP] > (lp->min - lp->range))) {
		data[INV_LP_V][i] = input_values[INV_LP];
	} else {
		data[INV_LP_V][i] = data[INV_LP_V][i-1];
	}*/

	data[INV_PD_V][i] = input_values[INV_PD];
	data[INV_LP_V][i] = input_values[INV_LP];

	if (data[INV_PD_V][i] > pd->th_up && pd->flag == 1) {
		// Inicio de la rafaga de la PD
		pd->flag = 0;

		// Si ya ha habido alguna rafaga de la LP antes calculamos el intervalo LPPD
		if (size_times_v_lp > 0) {
			data[INV_LPPD_INTERVAL][size_lppd_interval] = (i - data[INV_LP_TIMES][size_times_v_lp-1]) / 10.0;
			data[INV_ARRAYS_SIZES][INV_SIZE_LPPD_INTERVAL]++;

			if (size_period > 0) {
				sprintf(buf, "%.0f\t%.0f", (data[INV_LPPD_INTERVAL][size_lppd_interval-1] * 1 / 30), data[INV_LP_PERIOD_TIMES][size_period-1] * 1);
				//printf("%s\n", buf);
				*(params->serial_stream) << buf << std::endl;
			}
		}

		aux_pd = 1;
	} else if (data[INV_PD_V][i] < pd->th_lo && pd->flag == 0) {
		// Fin de la rafaga de la PD, y por tanto puede empezar la LP
		pd->flag = 1;
		lp->flag = 1;
	}


	if (data[INV_LP_V][i] > lp->th_up && lp->flag == 1) {
		// Inicio de rafaga de la LP
		lp->flag = 0;

		// Guarda el periodo de la LP
		if (size_times_v_lp > 0) {
			data[INV_LP_PERIOD_TIMES][size_period] = (i - data[INV_LP_TIMES][size_times_v_lp-1]) / 10.0;
			data[INV_ARRAYS_SIZES][INV_SIZE_PERIOD]++;
		}

		data[INV_LP_TIMES][size_times_v_lp] = i;
		data[INV_ARRAYS_SIZES][INV_SIZE_TIMES_V_LP]++;

		aux_lp = 1;
	}

	data[INV_PD_EVENT][i] = aux_pd;
	data[INV_LP_EVENT][i] = aux_lp;
	data[INV_LP_PERIOD_ALL][i] = data[INV_LP_PERIOD_TIMES][size_period-1];
}


void write_to_file_invariant (Params * params, int duration, char * filename) {
	int i;
	double ** data = params->data;

    FILE * f = fopen(filename, "w");

    fprintf(f, "1\nth_lo_per %.2f th_up_per %.2f\n", params->channels[INV_PD].th_lo_per, params->channels[INV_LP].th_up_per);

	for (i = 0; i < duration; i++) {
		fprintf(f, "%.0f %f %f %f %.0f %.0f %f\n", data[REALTIME][i], data[CURRENT][i], data[INV_PD_V][i], data[INV_LP_V][i], data[INV_PD_EVENT][i], data[INV_LP_EVENT][i], data[INV_LP_PERIOD_ALL][i]);
	}

	fclose(f);
}