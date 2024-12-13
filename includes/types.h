#ifndef TYPES_H
#define TYPES_H

#include <libserial/SerialStream.h>
#include <iostream>
#include <cstdlib>
#include <iostream>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>
#include <math.h>
#include <sys/stat.h>
#include <sys/types.h>

using namespace LibSerial;

/*typedef struct _Channel Channel;
typedef struct _Params Params;*/

#define EXP_SINGLE 0
#define EXP_INVARIANT 1

#define REALTIME 0
#define CURRENT 1


typedef struct Channel {
	double v;
	double range;
	double th_lo;
	double th_up;
	double th_lo_per;
	double th_up_per;
	double min;
	double max;
	double min_window;
	double max_window;
	int flag;
};


typedef struct Params {
	SerialStream * serial_stream;
	int experiment_type;
	int stimulation_type;
	double max_current;
	int freq;
	int n_in_chan;
	Channel * channels;
	double ** data;
};

#define OK 0
#define ERR -1


#endif //TYPES_H