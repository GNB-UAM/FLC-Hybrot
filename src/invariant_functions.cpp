#include "../includes/invariant_functions.h"

using namespace LibSerial;

#define TEMPORAL_FACTOR 1
#define MIN_PERIOD 500
#define MAX_AMPLITUDE 40
#define MIN_AMPLITUDE 6

#define USE_INTERVAL 0 // 0 = LPPD interval; 1 = PD burst

#define NORM_MIN 994.8
#define NORM_MAX 2217.8
#define SLOPE -0.035

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

	aux_params->data = (double **) malloc (sizeof(double *) * N_DATA_VARIABLES);

	aux_params->data[REALTIME] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[CURRENT] = (double *) malloc (sizeof(double) * duration);

	aux_params->data[INV_LP_TIMES] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_LP_END_TIMES] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_LP_PERIOD_TIMES] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_LP_V] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_LP_EVENT] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_LP_END_EVENT] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_LP_PERIOD_ALL] = (double *) malloc (sizeof(double) * duration);

	aux_params->data[INV_PD_TIMES] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_PD_END_TIMES] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_PD_V] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_PD_EVENT] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_PD_END_EVENT] = (double *) malloc (sizeof(double) * duration);

	aux_params->data[INV_LPPD_INTERVAL] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_PDLP_INTERVAL] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_PD_BURST] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_LP_BURST] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_PD_HYPER] = (double *) malloc (sizeof(double) * duration);

	aux_params->data[INV_LP_LAST_PERIOD] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_SECOND_ALL] = (double *) malloc (sizeof(double) * duration);
	aux_params->data[INV_ARRAYS_SIZES] = (double *) calloc (N_INV_SIZES, sizeof(double));

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
	// double abs_input = input_values[INV_LP];
	double abs_input = fabs(input_values[INV_LP]);

	if (abs_input > params->channels[INV_LP].max_window && (abs_input < (max + range))) params->channels[INV_LP].max_window = abs_input;
    if (abs_input < params->channels[INV_LP].min_window && (abs_input > (min - range))) params->channels[INV_LP].min_window = abs_input;

    min = params->channels[INV_PD].min;
	max = params->channels[INV_PD].max;
	range = params->channels[INV_PD].range;

	if (input_values[INV_PD] > params->channels[INV_PD].max_window && (input_values[INV_PD] < (max + range))) params->channels[INV_PD].max_window = input_values[INV_PD];
    if (input_values[INV_PD] < params->channels[INV_PD].min_window && (input_values[INV_PD] > (min - range))) params->channels[INV_PD].min_window = input_values[INV_PD];
}

int last_spike_pd_t = -1;

void burst_detection_invariant (Params * params, double * input_values, int i) {
	double aux_pd = 0, aux_lp = 0, aux_end_pd = 0, aux_end_lp = 0;
	char buf[10];
	Channel * lp = &(params->channels[INV_LP]);
	Channel * pd = &(params->channels[INV_PD]);
	double ** data = params->data;

	int size_times_v_lp = data[INV_ARRAYS_SIZES][INV_SIZE_TIMES_V_LP];
	int size_times_v_lp_end = data[INV_ARRAYS_SIZES][INV_SIZE_TIMES_V_LP_END];
	int size_times_v_pd = data[INV_ARRAYS_SIZES][INV_SIZE_TIMES_V_PD];
	int size_times_v_pd_end = data[INV_ARRAYS_SIZES][INV_SIZE_TIMES_V_PD_END];
	int size_lppd_interval = data[INV_ARRAYS_SIZES][INV_SIZE_LPPD_INTERVAL];
	int size_pdlp_interval = data[INV_ARRAYS_SIZES][INV_SIZE_PDLP_INTERVAL];
	int size_pd_burst = data[INV_ARRAYS_SIZES][INV_SIZE_PD_BURST];
	int size_lp_burst = data[INV_ARRAYS_SIZES][INV_SIZE_LP_BURST];
	int size_pd_hyper = data[INV_ARRAYS_SIZES][INV_SIZE_PD_HYPER];
	int size_period = data[INV_ARRAYS_SIZES][INV_SIZE_PERIOD];

	//printf("%f %f\n",pd->th_up,pd->th_lo );
/*
	if ((input_values[INV_PD] < (pd->max + pd->range)) && (input_values[INV_PD] > (pd->min - pd->range))) {
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
		/*if (size_times_v_lp > 0) {
			data[INV_LPPD_INTERVAL][size_lppd_interval] = (i - data[INV_LP_TIMES][size_times_v_lp-1]) / 10.0;
			data[INV_ARRAYS_SIZES][INV_SIZE_LPPD_INTERVAL]++;

			if (size_period > 0) {
				sprintf(buf, "%.0f,%.0f", (data[INV_LPPD_INTERVAL][size_lppd_interval-1] * 1 / 30), data[INV_LP_PERIOD_TIMES][size_period-1] * 1);
				//printf("%s\n", buf);
				*(params->serial_stream) << buf << std::endl;
			}
		}*/

		data[INV_PD_TIMES][size_times_v_pd] = i;
		data[INV_ARRAYS_SIZES][INV_SIZE_TIMES_V_PD]++;

		aux_pd = 1;
	//} else if (data[INV_PD_V][i] > pd->th_up) {
	//} else if (data[INV_PD_V][i] > pd->th_up && (data[INV_PD_V][i] - data[INV_PD_V][i-1] > (0.6/25))) {
	} else if (i >= 30 && data[INV_PD_V][i] > pd->th_up) {
		double mean_1 = 0, mean_2 = 0, mean_3 = 0;
		int j;

		for (j=0; j < 10; j++) {
			mean_1 += data[INV_PD_V][i-j];
		}
		mean_1 /= 10;

		for (j=10; j < 20; j++) {
			mean_2 += data[INV_PD_V][i-j];
		}
		mean_2 /= 10;

		for (j=20; j < 30; j++) {
			mean_3 += data[INV_PD_V][i-j];
		}
		mean_3 /= 10;

		if ((mean_1 - mean_2 < SLOPE) && mean_2 > mean_3) {
			last_spike_pd_t = i-15;
		}
	} else if (data[INV_PD_V][i] < pd->th_lo && pd->flag == 0) {
		// Fin de la rafaga de la PD, y por tanto puede empezar la LP
		pd->flag = 1;
		lp->flag = 1;

		if (last_spike_pd_t != -1) {
			data[INV_PD_END_TIMES][size_times_v_pd_end] = last_spike_pd_t;
			data[INV_ARRAYS_SIZES][INV_SIZE_TIMES_V_PD_END]++;
			data[INV_PD_END_EVENT][last_spike_pd_t] = 1;
		}

		//aux_end_pd = 1;
	}


	if (data[INV_LP_V][i] > lp->th_up && lp->flag == 1) {
		// Inicio de rafaga de la LP
		lp->flag = 0;

		// Guarda el periodo de la LP
		if (size_times_v_lp > 0) {
			data[INV_LPPD_INTERVAL][size_lppd_interval] = (data[INV_PD_TIMES][size_times_v_pd-1] - data[INV_LP_TIMES][size_times_v_lp-1]) / 10.0;
			data[INV_ARRAYS_SIZES][INV_SIZE_LPPD_INTERVAL]++;

			data[INV_LP_PERIOD_TIMES][size_period] = (i - data[INV_LP_TIMES][size_times_v_lp-1]) / 10.0;
			data[INV_ARRAYS_SIZES][INV_SIZE_PERIOD]++;

			data[INV_PDLP_INTERVAL][size_pdlp_interval] = (i - data[INV_PD_TIMES][size_times_v_pd-1]) / 10.0;
			data[INV_ARRAYS_SIZES][INV_SIZE_PDLP_INTERVAL]++;

			data[INV_PD_BURST][size_pd_burst] = (data[INV_PD_END_TIMES][size_times_v_pd_end-1] - data[INV_PD_TIMES][size_times_v_pd-1]) / 10.0;
			data[INV_ARRAYS_SIZES][INV_SIZE_PD_BURST]++;

			if (size_times_v_pd_end > 1) {
				data[INV_PD_HYPER][size_pd_hyper] = (data[INV_PD_TIMES][size_times_v_pd-1] - data[INV_PD_END_TIMES][size_times_v_pd_end-2]) / 10.0;
			} else {
				data[INV_PD_HYPER][size_pd_hyper] = 0;
			}
			data[INV_ARRAYS_SIZES][INV_SIZE_PD_HYPER]++;
			

			
			if (USE_INTERVAL == 0) {
				/* Sends LPPD interval */
				if (size_period > 0 && data[INV_ARRAYS_SIZES][INV_SIZE_LPPD_INTERVAL] > 0) {
					double norm_var1 = data[INV_LP_PERIOD_TIMES][size_period] * TEMPORAL_FACTOR;
					double norm_var2 = (((data[INV_LPPD_INTERVAL][size_lppd_interval]) - NORM_MIN) / (NORM_MAX-NORM_MIN)) * (MAX_AMPLITUDE - MIN_AMPLITUDE) + MIN_AMPLITUDE;
					norm_var2 *= TEMPORAL_FACTOR;

					sprintf(buf, "%.0f,%.0f", norm_var1, abs(norm_var2));
					//printf("%f %f %f %d %s\n", data[INV_LPPD_INTERVAL][size_lppd_interval], NORM_MIN, NORM_MAX, MAX_AMPLITUDE, buf);
					if (norm_var1 < MIN_PERIOD || norm_var2 > MAX_AMPLITUDE) {
						printf("%s\n", buf);
					}

					printf("Writing %s to serial\n",buf);
					*(params->serial_stream) << buf << std::endl;
				}
			} else if (USE_INTERVAL == 1) {
				/* Sends PD burst */
				if (size_period >= 0 && data[INV_ARRAYS_SIZES][INV_SIZE_PD_BURST] > 0) {
					double norm_var1 = data[INV_LP_PERIOD_TIMES][size_period] * TEMPORAL_FACTOR;
					double norm_var2 = (((data[INV_PD_BURST][size_pd_burst]) - NORM_MIN) / (NORM_MAX-NORM_MIN)) * (MAX_AMPLITUDE - MIN_AMPLITUDE) + MIN_AMPLITUDE;
					norm_var2 *= TEMPORAL_FACTOR;

					sprintf(buf, "%.0f,%.0f", norm_var1, abs(norm_var2));
					if (norm_var1 < MIN_PERIOD || norm_var2 > MAX_AMPLITUDE) {
						printf("%s\n", buf);
					}
					printf("Writing %s to serial\n",buf);
					
					*(params->serial_stream) << buf << std::endl;
				}
			}

			/* Sends PDLP interval */
			/*if (size_period >= 0 && data[INV_ARRAYS_SIZES][INV_SIZE_PDLP_INTERVAL] > 0) {
				double norm_var1 = data[INV_LP_PERIOD_TIMES][size_period] * TEMPORAL_FACTOR;
				double norm_var2 = (((data[INV_PDLP_INTERVAL][size_pdlp_interval] * TEMPORAL_FACTOR) - NORM_MIN) / NORM_MAX) * MAX_AMPLITUDE;

				sprintf(buf, "%.0f,%.0f", norm_var2, norm_var1);
				if (norm_var1 < MIN_PERIOD || norm_var2 > MAX_AMPLITUDE) {
					printf("%s\n", buf);
				}
				
				*(params->serial_stream) << buf << std::endl;
			}*/

			/* Sends PD hyperpol */
			/*if (size_period >= 0 && data[INV_ARRAYS_SIZES][INV_SIZE_PD_HYPER] > 1) {
				double norm_var1 = data[INV_LP_PERIOD_TIMES][size_period] * TEMPORAL_FACTOR;
				double norm_var2 = (((data[INV_PD_HYPER][size_pd_hyper] * TEMPORAL_FACTOR) - NORM_MIN) / NORM_MAX) * MAX_AMPLITUDE;

				sprintf(buf, "%.0f,%.0f", norm_var2, norm_var1);
				if (norm_var1 < MIN_PERIOD || norm_var2 > MAX_AMPLITUDE) {
					printf("%s\n", buf);
				}
				
				*(params->serial_stream) << buf << std::endl;
			}*/
		}

		data[INV_LP_TIMES][size_times_v_lp] = i;
		data[INV_ARRAYS_SIZES][INV_SIZE_TIMES_V_LP]++;

		aux_lp = 1;
	}

	data[INV_PD_EVENT][i] = aux_pd;
	//data[INV_PD_END_EVENT][i] = aux_end_pd;
	data[INV_LP_EVENT][i] = aux_lp;
	data[INV_LP_END_EVENT][i] = aux_end_lp;
	data[INV_LP_PERIOD_ALL][i] = data[INV_LP_PERIOD_TIMES][size_period-1];

	if (USE_INTERVAL == 0) {
		data[INV_SECOND_ALL][i] = data[INV_LPPD_INTERVAL][size_lppd_interval-1];
	} else if (USE_INTERVAL == 1 == 1) {
		data[INV_SECOND_ALL][i] = data[INV_PD_BURST][size_pd_burst-1];
	}
	
	

	/*if (size_lppd_interval == size_period) {
		data[INV_LP_PERIOD_ALL][i] = data[INV_LPPD_INTERVAL][size_lppd_interval-1] / data[INV_LP_PERIOD_TIMES][size_period-1];
		//data[INV_LP_PERIOD_ALL][i] = data[INV_LPPD_INTERVAL][size_lppd_interval-1];
	} else {
		data[INV_LP_PERIOD_ALL][i] = data[INV_LPPD_INTERVAL][size_lppd_interval-2] / data[INV_LP_PERIOD_TIMES][size_period-1];
		//data[INV_LP_PERIOD_ALL][i] = data[INV_LPPD_INTERVAL][size_lppd_interval-2];
	}*/
	
	//data[INV_LP_PERIOD_ALL][i] = data[INV_PDLP_INTERVAL][size_pdlp_interval-1] / data[INV_LP_PERIOD_TIMES][size_period-1];
}


void write_to_file_invariant (Params * params, int duration, char * filename) {
	int i;
	double ** data = params->data;

    FILE * f = fopen(filename, "w");

    fprintf(f, "1\nth_lo_per %.2f th_up_per %.2f\n", params->channels[INV_PD].th_lo_per, params->channels[INV_LP].th_up_per);
	
	fprintf(f, "Time Current Inv_PD_V INV_LP_V INV_PD_EVENT INV_LP_EVENT INV_LP_PERIOD_ALL\n");

	for (i = 0; i < duration; i++) {
		fprintf(f, "%.0f %f %f %f %.0f %.0f %.0f %.0f %f %f\n", data[REALTIME][i], data[CURRENT][i], data[INV_PD_V][i], data[INV_LP_V][i], data[INV_PD_EVENT][i], data[INV_PD_END_EVENT][i], data[INV_LP_EVENT][i], data[INV_LP_END_EVENT][i], data[INV_LP_PERIOD_ALL][i], data[INV_SECOND_ALL][i]);
	}

	fclose(f);
}
