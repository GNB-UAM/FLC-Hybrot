#include "../includes/time_functions.h"
#include "../includes/common_functions.h"
#include "../includes/device_functions.h"

using namespace LibSerial;

struct option main_opts[] = {
	{"experiment_type", required_argument, NULL, 'E'},
	{"frequency", required_argument, NULL, 'f'},
	{"time", required_argument, NULL, 't'},
	{"current", required_argument, NULL, 'c'},
	{"stimulation_type", required_argument, NULL, 'S'},
	{"pulse_duration", required_argument, NULL, 'D'},
	{"lower_threshold", required_argument, NULL, 'L'},
	{"upper_threshold", required_argument, NULL, 'U'},
	{"input_channels", required_argument, NULL, 'i'},
	{"output_channels", required_argument, NULL, 'o'},
	{"serial_port", required_argument, NULL, 'p'},
	{"output_factor", required_argument, NULL, 'O'},
	{"help", no_argument, NULL, 'h'},
	{0},
};

void do_print_usage ()
{
	printf("usage:\tcontroller [OPTS]\n");
	printf("\tOPTS:\t -E, --experiment_type: 0 for single neuron, 1 for invariant\n");
	printf("\t\t -f, --frequency: sample frequency (in Hz)\n");
	printf("\t\t -t, --time: experiment duration (in s)\n");
	printf("\t\t -L, --lower_threshold: lower threshold for burst detection (percentage)\n");
	printf("\t\t -U, --upper_threshold: upper threshold for burst detection (percentage)\n");
	printf("\t\t -c, --current: value of the current to inject (in nA)\n");
	printf("\t\t -S, --stimulation_type: 0 for continuous current, 1 for fixed pulses, 2 for variable pulses\n");
	printf("\t\t -D, --pulse_duration: if using stimulation by pulses, duration of the pulses (in s)\n");
	printf("\t\t -i, --input_channels: input channels, separated by commas (ej: 0,2,3,7)\n");
	printf("\t\t -o, --output_channels: output channels, separated by commas (ej: 0,2,3,7)\n");
	printf("\t\t -p, --serial_port: serial port\n");
	printf("\t\t -O, --output_factor: output factor\n");
	printf("\t\t -h, --help: print this help\n");
}

void parse_channels (char * str, int ** channels, int * n_chan) {
	int n_chan_aux = 0;
	int chan_aux[32];
	char * token = NULL;
	int i;

	token = strtok(str, ",");
	

	while (token != NULL) {
		chan_aux[n_chan_aux] = atoi(token);
		n_chan_aux++;

		token = strtok(NULL, ",");
	}

	*channels = (int *) malloc (sizeof(int) * n_chan_aux);
	*n_chan = n_chan_aux;

	for (i = 0; i < n_chan_aux; i++) {
		(*channels)[i] = chan_aux[i];
	}

	return;
}





int main (int argc, char *argv[]) {
	Params * params;
	SerialStream serial_stream;

	// DAQ variables
	void * dsc = NULL;
	Daq_session * session = NULL;
	double * input_values = NULL;
	double * output_values = NULL;

	// Time variables
	struct timespec ts_target, ts_start, ts_iter, ts_result;
	double t_elapsed; /* In microseconds */

	// General variables
	int i;

	char next_char = '0';
	char last_char = '0';
	int drift_counter = 0;

	char serial_port_name[30];
	memset(serial_port_name, '\0', sizeof(serial_port_name));
	strcpy(serial_port_name, "/dev/ttyUSB0");


	int experiment_type = 0;
	int stimulation_type = 0;
	int freq = 10000;
	int period;
	int duration = 120;
	int observation_time = 20;
	double max_current = 0.01;
	double th_lo_per = 0.1;
	double th_up_per = 0.7;
	double output_factor = 10;

	int n_out_chan = 0;
	int n_in_chan = 0;
	int * out_channels = NULL;
	int * in_channels = NULL;

	int pulse_duration = 1;
	double target_current = 0;

	int ret;

	while ((ret = getopt_long(argc, argv, "E:f:t:L:U:c:S:D:i:o:p:O:h", main_opts, NULL)) >= 0) {
		switch (ret) {
			case 'E':
				experiment_type = atoi(optarg);
				break;
			case 'f':
				freq = atoi(optarg);
				break;
			case 't':
				duration = atoi(optarg);
				break;
			case 'L':
				th_lo_per = atof(optarg);
				break;
			case 'U':
				th_up_per = atof(optarg);
				break;
			case 'c':
				max_current = atof(optarg);
				break;
			case 'S':
				stimulation_type = atoi(optarg);
				break;
			case 'D':
				pulse_duration = atoi(optarg);
				break;
			case 'i':
				parse_channels(optarg, &(in_channels), &(n_in_chan));
				break;
			case 'o':
				parse_channels(optarg, &(out_channels), &(n_out_chan));
				break;
			case 'p':
				memset(serial_port_name, '\0', sizeof(serial_port_name));
				strcpy(serial_port_name, optarg);
				break;
			case 'O':
				output_factor = atof(optarg);
				break;
			case 'h':
			default:
				do_print_usage();
				return 0;
		}
	}

	// Convert from seconds to points
	duration = duration * freq;
	pulse_duration = pulse_duration * freq;
	observation_time = observation_time * freq;
	period = (1.0 / freq) * NSEC_PER_SEC;

	// Apply output_factor to the current
	max_current = max_current / output_factor;

	if (n_out_chan < 1) {
		printf("Wrong number of output channels.\n");
		free(in_channels);
    	free(out_channels);
		return ERR;
	}

	// Init
	if (init_params(&params, &serial_stream, experiment_type, stimulation_type, n_in_chan, duration, freq, max_current, th_lo_per, th_up_per) != OK) {
		printf("Wrong number of input channels.\n");
		free(in_channels);
    	free(out_channels);
		return ERR;
	}


	/****************************************************
    Open DAQ
    ****************************************************/
    if (daq_open_device((void**) &dsc) != OK) {
        fprintf(stderr, "RT_THREAD: error opening device.\n");

        return ERR;
    }

    if (daq_create_session ((void**) &dsc, &session) != OK) {
        fprintf(stderr, "RT_THREAD: error creating DAQ session.\n");
        daq_close_device ((void**) &dsc);

        return ERR;
    }

    input_values = (double *) malloc (sizeof(double) * n_in_chan);
    output_values = (double *) malloc (sizeof(double) * n_out_chan);


    for (i = 0; i < n_out_chan; i++) {
        input_values[i] = 0;
    }
    for (i = 0; i < n_out_chan; i++) {
        output_values[i] = 0;
    }

    if (daq_write(session, n_out_chan, out_channels, output_values) != OK) {
        fprintf(stderr, "RT_THREAD: error writing to DAQ.\n");
        daq_close_device ((void**) &dsc);

        return ERR;
    }

    /****************************************************
    Open serial connection
    ****************************************************/
    if (params->serial_stream->IsOpen() == false){
		params->serial_stream->Open(serial_port_name);
		params->serial_stream->SetBaudRate(BaudRate::BAUD_19200);
		params->serial_stream->SetCharacterSize(CharacterSize::CHAR_SIZE_8);
	}

	// TODO Stop robot for calibration
	// The robot will start when receiving the first cycle
	*(params->serial_stream) << '0\t0' << std::endl;

	printf("Start observation (%ds) and interaction (%ds)\n", observation_time/freq, duration/freq);

	/****************************************************
    Observation
    ****************************************************/
    clock_gettime(CLOCK_MONOTONIC, &ts_target);
    ts_assign(&ts_start,  ts_target);
    ts_add_time(&ts_target, 0, period);


	for (i = 0; i < observation_time; i++) {
		/* Sleep */
		clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &ts_target, NULL);

		/* Wake up and get times */
        clock_gettime(CLOCK_MONOTONIC, &ts_iter);
        ts_substraction(&ts_start, &ts_iter, &ts_result);
        t_elapsed = (ts_result.tv_sec * NSEC_PER_SEC + ts_result.tv_nsec) * 0.001;

        ts_add_time(&ts_target, 0, period);

        /* Read from DAQ */
		if (daq_read(session, n_in_chan, in_channels, input_values) != 0) {

            for (i = 0; i < n_out_chan; i++) {
                output_values[i] = 0;
            }

            if (daq_write(session, n_out_chan, out_channels, output_values) != OK) {
                fprintf(stderr, "RT_THREAD: error writing to DAQ.\n");
                daq_close_device ((void**) &dsc);
                return ERR;
            }

            free(session);
            daq_close_device ((void**) &dsc);
		    free(input_values);
		    free(output_values);

            return ERR;
        }

        /* Update min and max in the temporal window */
        update_min_max_window_first(params, input_values);
	}

	printf("End calibration\n");


	/* Update amplitude parameters */
	update_amplitude(params);

	//TODO Empty serial buffer
	*(params->serial_stream) << '0\t0' << std::endl;


	/****************************************************
    Interaction
    ****************************************************/
    for (i = 0, drift_counter = 0; i < duration; i++, drift_counter++) {
		/* Sleep */
		clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &ts_target, NULL);

		/* Wake up and get times */
        clock_gettime(CLOCK_MONOTONIC, &ts_iter);
        ts_substraction(&ts_start, &ts_iter, &ts_result);
        t_elapsed = (ts_result.tv_sec * NSEC_PER_SEC + ts_result.tv_nsec) * 0.001;

        ts_add_time(&ts_target, 0, period);

        /* Read from serial */
		if (params->serial_stream->IsDataAvailable()) {
			last_char = next_char;
			*(params->serial_stream) >> next_char;
			if (next_char != '3' && next_char != '1') {
				next_char = last_char;
			}
		}


		/* Read from DAQ */
		if (daq_read(session, n_in_chan, in_channels, input_values) != 0) {
            for (i = 0; i < n_out_chan; i++) {
                output_values[i] = 0;
            }

            if (daq_write(session, n_out_chan, out_channels, output_values) != OK) {
                fprintf(stderr, "RT_THREAD: error writing to DAQ.\n");
                daq_close_device ((void**) &dsc);
                return ERR;
            }

            free(session);
            daq_close_device ((void**) &dsc);
		    free(input_values);
		    free(output_values);

            return ERR;
        }
        
        // Drift compensation
        update_min_max_window(params, input_values);

        //if (drift_counter > 0.5 * freq) {
        if (drift_counter > 2.5 * freq) {
        	update_amplitude(params);
			drift_counter = 0;
        }
 
        /* Burst detection and robot control */
        burst_detection(params, input_values, i);


        /* Stimulation */
        if (next_char == '3') {
			target_current = max_current;
		} else {
			target_current = 0;
		}
        select_stimulus(params, output_values, target_current);

   		/* Write to DAQ */
        if (daq_write(session, n_out_chan, out_channels, output_values) != OK) {
	        fprintf(stderr, "RT_THREAD: error writing to DAQ.\n");
	        daq_close_device ((void**) &dsc);

	        return ERR;
	    }


	    /* Save time and current */
	    params->data[CURRENT][i] = output_values[0] * output_factor;
        params->data[REALTIME][i] = t_elapsed;
	}


	/****************************************************
    Write to file
    ****************************************************/
    printf("Ended experiment. Saving data to file...\n");
    write_to_file(params, duration);
    printf("Data saved!\n");

    //TODO refractor to function
    //Stop robot
	*(params->serial_stream) << '0\t0' << std::endl;


	/****************************************************
    Clean up and finish
    ****************************************************/

	/*Send zero*/
    for (i = 0; i < n_out_chan; i++) {
        output_values[i] = 0;
    }
    if (daq_write(session, n_out_chan, out_channels, output_values) != OK) {
        fprintf(stderr, "RT_THREAD: error writing to DAQ.\n");
        daq_close_device ((void**) &dsc);

        return ERR;
    }

    free(session);
    daq_close_device ((void**) &dsc);
    free(input_values);
    free(output_values);

    free(in_channels);
    free(out_channels);
    free_params(&params);

    return OK;
}
