#include "types.h"

#define N_DATA_VARIABLES 22
#define N_INV_SIZES 11

#define INV_PD 0
#define INV_LP 1

#define INV_LP_TIMES 2
#define INV_LP_END_TIMES 3
#define INV_LP_PERIOD_TIMES 4
#define INV_LP_V 5
#define INV_LP_EVENT 6
#define INV_LP_END_EVENT 7

#define INV_PD_TIMES 8
#define INV_PD_END_TIMES 9
#define INV_PD_V 10
#define INV_PD_EVENT 11
#define INV_PD_END_EVENT 12

#define INV_LP_PERIOD_ALL 13
#define INV_LPPD_INTERVAL 14
#define INV_PDLP_INTERVAL 15
#define INV_PD_BURST 16
#define INV_LP_BURST 17
#define INV_PD_HYPER 18

#define INV_LP_LAST_PERIOD 19
#define INV_SECOND_ALL 20
#define INV_ARRAYS_SIZES 21

#define INV_SIZE_TIMES_V_LP 0
#define INV_SIZE_TIMES_V_PD 1
#define INV_SIZE_TIMES_V_LP_END 3
#define INV_SIZE_TIMES_V_PD_END 4
#define INV_SIZE_PERIOD 5
#define INV_SIZE_LPPD_INTERVAL 6
#define INV_SIZE_PDLP_INTERVAL 7
#define INV_SIZE_LP_BURST 8
#define INV_SIZE_PD_BURST 9
#define INV_SIZE_PD_HYPER 10


int init_params_invariant (Params ** params, int duration, SerialStream * serial_stream, double th_lo_per_pd, double th_up_per_pd, double th_lo_per_lp, double th_up_per_lp);

void free_params_invariant (Params ** params);

void update_min_max_window_invariant (Params * params, double * input_values);

void update_min_max_window_invariant_first (Params * params, double * input_values);

void burst_detection_invariant (Params * params, double * input_values, int i);

void write_to_file_invariant (Params * params, int duration, char * filename);