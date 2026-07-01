#include "../includes/device_functions.h"
#include <string.h>

#define READ_FROM_FILE 1


/* Read from file variables */
FILE * f;

int daq_open_device (void ** device) {

	if (READ_FROM_FILE == 1) {
		char * filename = (char *) *device;

		printf("Trying to open %s\n", filename);

		f = fopen(filename, "r");

        if (!f)
        {
        	perror("READ FROM FILE activated and file not found");
        	return ERR;
		}
		//Ignore headers
		printf("ignoring headers");
		char buf[999];
		fgets(buf, sizeof(char) * 200, f);
		printf("%s\n", buf);
		fgets(buf, sizeof(char) * 200, f);
		printf("%s\n", buf);
		fgets(buf, sizeof(char) * 200, f);
		printf("%s\n", buf);

		printf("File successfully open\n");
	}

	return OK;
}

int daq_close_device (void ** device) {

	if (READ_FROM_FILE == 1) fclose(f);


	return OK;
}



int read_single_data_file (int * channels, int n_channels, double ** ret) {
	char buf[999];
	fgets(buf, sizeof(char) * 200, f);

	int k = 0;
	char * elemento;
	elemento = strtok(buf, " ");

	if (elemento == NULL) return -1;

	for (int i = 0; i < n_channels; i++) {
		if (k == channels[i]) {
			(*ret)[i] = atof(elemento); 
		}
	}

	while (elemento != NULL) {
		k++;
		elemento = strtok(NULL, " ");

		for (int i = 0; i < n_channels; i++) {
			if (k == channels[i]) {
				(*ret)[i] = atof(elemento); 
			}
		}
	}

	return 0;
}


int daq_read (Daq_session * session, int n_channels, int * channels, double * ret) {
	int i;
	double aux;

	if (READ_FROM_FILE == 1) {
		if (read_single_data_file (channels, n_channels, &ret) != 0) {
			printf("Error reading from file\n");
    		return -1;
		}
	}
    
    return 0;
}