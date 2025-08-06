import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from scipy.fftpack import rfft, irfft, fftfreq
from scipy.signal import butter, filtfilt, detrend
from scipy.interpolate import interp1d

import math

import numpy as np
from pprint import pprint

from numpy.lib.stride_tricks import sliding_window_view



def remove_axes(ax, positions=['top', 'right']):
    for p in positions:
        ax.spines[p].set_visible(False)


def get_std_distribution_sliding(data, wsize=20):
    print("Data:", data.shape)
    w_data = sliding_window_view(data, (wsize,))

    print("Sliding window:", w_data.shape)
    std_distribution = np.std(w_data, axis=-1)

    print("Std distribution:", std_distribution.shape)

    return std_distribution


def plot_two_invariant(fig, ax, period1, period2, var1, var2, id=0):
    slope_interval, intercept_interval, r_interval, pvalue_interval, std_error_interval = stats.linregress(period1, var1)
    r2_interval = r_interval*r_interval

    sc = ax.scatter(period1, var1, c=np.linspace(0, len(var1), len(period1)), cmap=plt.get_cmap("Blues"))
    cbar = fig.colorbar(sc, ax=ax, pad=-0.04)
    cbar.set_label('#Cycle')
    ax.plot(period1, intercept_interval+(slope_interval*np.asarray(period1)), alpha=0.5, color="blue", label="R2 LPPD int=%f"%r2_interval)

    slope_interval, intercept_interval, r_interval, pvalue_interval, std_error_interval = stats.linregress(period2, var2)
    r2_interval = r_interval*r_interval

    #plt.figure(figsize=(7,5))
    sc = ax.scatter(period2, var2, c=np.linspace(0, len(var2), len(period2)), cmap=plt.get_cmap("Oranges"))
    cbar = fig.colorbar(sc, ax=ax)

    ax.plot(period2, intercept_interval+(slope_interval*np.asarray(period2)), alpha=0.5, color="orange", label="R2 PD burst=%f"%r2_interval)

    ax.legend()

    #plt.ylim(bottom=0.25, top=1.05)
    #plt.xlim(left=0.65, right=1.5)

    # ax.set_xlabel("Cycle period (s)")
    # ax.set_ylabel("Experiment %d\n\nInterval duration (s)"%id)
    ax.set_ylabel("Interval duration (s)")

    row_title = "Experiment %d\n" % id
    # Set the font size for the "Experiment" part
    font_size_experiment = 14
    font_size_interval = 10

    # Add the row title to the side
    ax.text(-0.15, 0.5, row_title, transform=ax.transAxes, fontsize=font_size_experiment, va='center', ha='right',rotation='vertical')
    # ax.text(-0.15, 0.5, "\n", transform=ax.transAxes, fontsize=font_size_interval, va='center', ha='right')


    remove_axes(ax)

    fig.tight_layout()


def invariants(v_lp, v_pd, is_extra=False, plot=None, ini_times=None, end_times=None):
    flag_v_pd = 0
    ini_times_pd = []
    end_times_pd = []
    ini_v_pd = []
    end_v_pd = []
    min_v_pd = min(v_pd[0:calibration_pts])
    max_v_pd = max(v_pd[0:calibration_pts])
    r_v_pd = max_v_pd - min_v_pd

    flag_v_lp = 0
    ini_times_lp = []
    end_times_lp = []
    ini_v_lp = []
    end_v_lp = []
    min_v_lp = min(v_lp[0:calibration_pts])
    max_v_lp = max(v_lp[0:calibration_pts])
    r_v_lp = max_v_lp - min_v_lp

    lppd_interval = []
    lppd_delay = []
    pdlp_interval = []
    pdlp_delay = []
    pd_burst = []
    lp_burst = []
    period = []

    ignore_lp = False
    last_lp_isi_t = np.inf
    last_spike_lp_t = 0
    last_spike_lp_v = 0
    last_spike_pd_t = 0
    last_spike_pd_v = 0

    for i in range(len(v_pd)):
        # time.sleep(0.0001)

        if (v_pd[i] > (min_v_pd + r_v_pd*upper_th_pd) and flag_v_pd == 1):
            # PD burst starts
            flag_v_pd = 0

            if is_extra:
                # LP burst ends (extracellular)

                ignore_lp = False
                last_lp_isi_t = np.inf

                if (last_spike_lp_v != 0):
                    end_times_lp.append(last_spike_lp_t)
                    end_v_lp.append(last_spike_lp_v)

            ini_times_pd.append(i)
            ini_v_pd.append(v_pd[i])
        elif(v_pd[i] > (min_v_pd + r_v_pd*upper_th_pd)):
            # New spike of ongoing PD burst
            last_spike_pd_t = i
            last_spike_pd_v = v_pd[i]
        elif (v_pd[i] < (min_v_pd + r_v_pd*lower_th_pd) and flag_v_pd == 0):
            # PD burst ends
            flag_v_pd = 1
            flag_v_lp = 1

            if (last_spike_pd_v != 0):
                end_times_pd.append(last_spike_pd_t)
                end_v_pd.append(last_spike_pd_v)

        if (v_lp[i] > (min_v_lp + r_v_lp*upper_th_lp) and flag_v_lp == 1):
            # LP burst starts
            flag_v_lp = 0

            # If there is already one LP and PD bursts then save that cycle intervals
            if (len(ini_times_lp) > 0 and len(ini_times_pd) > 0 and len(end_times_lp) > 0 and len(end_times_pd) > 0):    
                period.append(i - ini_times_lp[-1])
                lppd_interval.append(ini_times_pd[-1] - ini_times_lp[-1])
                lppd_delay.append(ini_times_pd[-1] - end_times_lp[-1])
                pdlp_interval.append(i - ini_times_pd[-1])
                pdlp_delay.append(i - end_times_pd[-1])
                lp_burst.append(end_times_lp[-1] - ini_times_lp[-1])
                pd_burst.append(end_times_pd[-1] - ini_times_pd[-1])

            ini_times_lp.append(i)
            ini_v_lp.append(v_lp[i])

        elif (v_lp[i] > (min_v_lp + r_v_lp*upper_th_lp)) and ignore_lp==False:
            if is_extra==True and ((i - last_spike_lp_t) > 5*last_lp_isi_t):
                # Ignore isolated spikes (possible artifacts)
                ignore_lp = True
            elif (i > 2) and (v_lp[i] < v_lp[i-1]) and (v_lp[i-1] > v_lp[i-2]):
                last_lp_isi_t = i - last_spike_lp_t
                # New spike of ongoing LP burst
                last_spike_lp_t = i-1
                last_spike_lp_v = v_lp[i-1]

        elif (v_lp[i] < (min_v_lp + r_v_lp*lower_th_lp) and
              flag_v_lp == 0 and is_extra == False):

            # LP burst ends (intracellular)
            flag_v_lp = 1
            ignore_lp = False
            last_lp_isi_t = np.inf

            if (last_spike_lp_v != 0):
                end_times_lp.append(last_spike_lp_t)
                end_v_lp.append(last_spike_lp_v)
       
        if (i % calibration_pts == 0):
            min_v_lp = min(v_lp[i:i+calibration_pts])
            max_v_lp = max(v_lp[i:i+calibration_pts])

            min_v_pd = min(v_pd[i:i+calibration_pts])
            max_v_pd = max(v_pd[i:i+calibration_pts])

    lppd_interval = [x / fs for x in lppd_interval]
    lppd_delay = [x / fs for x in lppd_delay]
    pdlp_interval = [x / fs for x in pdlp_interval]
    pdlp_delay = [x / fs for x in pdlp_delay]
    pd_burst = [x / fs for x in pd_burst]
    lp_burst = [x / fs for x in lp_burst]
    period = [x / fs for x in period]

    if ini_times is not None and end_times is not None:
        ini_times['lp'] = ini_times_lp
        ini_times['pd'] = ini_times_pd

        end_times['lp'] = end_times_lp
        end_times['pd'] = end_times_pd

    if plot is not None:
        time = np.arange(0,len(v_lp),1) * 0.0001
        # plot[0].plot(time,v_lp)
        # plot[0].plot(np.array(ini_times_lp)*0.0001, np.array(v_lp[np.array(ini_times_lp)]), ".")
        # plot[0].plot(np.array(end_times_lp)*0.0001, np.array(v_lp[np.array(end_times_lp)]), ".")
        # plot[2].plot(time,v_pd)
        # plot[2].plot(np.array(ini_times_pd)*0.0001, np.array(v_pd[np.array(ini_times_pd)]), ".")
        # plot[2].plot(np.array(end_times_pd)*0.0001, np.array(v_pd[np.array(end_times_pd)]), ".")
        # # plt.show()

        for ini, end in zip(ini_times_lp[:-1], ini_times_lp[1:]):
            plot[0].hlines(y=v_lp[ini]+0.1, xmin=ini * 0.0001, xmax=end * 0.0001, color='green', linewidth=6, alpha=0.6)  
            plot[2].hlines(y=v_pd[ini]+0.1, xmin=ini * 0.0001, xmax=end * 0.0001, color='green', linewidth=6, alpha=0.6)  
            plot[4].hlines(y=2, xmin=ini * 0.0001, xmax=end * 0.0001, color='green', linewidth=6, alpha=0.6)     
            plot[4].plot([ini * 0.0001, end * 0.0001], [2, 2], '|', color='black')  # Markers at borders

        # Plot v_lp with horizontal lines
        plot[0].plot(time, v_lp)
        for ini, end in zip(ini_times_lp[:-1], ini_times_pd[1:]):
            plot[0].hlines(y=v_lp[ini], xmin=ini * 0.0001, xmax=end * 0.0001, color='red', linewidth=6, alpha=0.4)  
            plot[4].hlines(y=1, xmin=ini * 0.0001, xmax=end * 0.0001, color='red', linewidth=6, alpha=0.6)     
            plot[4].plot([ini * 0.0001, end * 0.0001], [1, 1], '|', color='black')  # Markers at borders

        # Plot v_pd with horizontal lines
        plot[2].plot(time, v_pd)
        for ini, end in zip(ini_times_pd, end_times_pd):
            plot[2].hlines(y=v_pd[ini], xmin=ini * 0.0001, xmax=end * 0.0001, color='blue', linewidth=6, alpha=0.4)  
            plot[4].hlines(y=1.5, xmin=ini * 0.0001, xmax=end * 0.0001, color='blue', linewidth=6, alpha=0.6)     
            plot[4].plot([ini * 0.0001, end * 0.0001], [1.5, 1.5], '|', color='black')  # Markers at borders


    return period, lppd_interval, lppd_delay, pdlp_interval, pdlp_delay, lp_burst, pd_burst


def get_intervals_dict():
    periods = []
    intervals = []
    ini_times = []
    end_times = []
    v_data = []
    for i in range(n_exp):
        periods.append({})
        periods_dict = periods[-1]

        intervals.append({})
        ints_dict = intervals[-1]

        ini_times.append({})
        ini_times_dict = ini_times[-1]

        end_times.append({})
        end_times_dict = end_times[-1]

        v_data.append({})
        v_data_dict = v_data[-1]

        for i_tag, tag in enumerate(intervals_tags):
            filename = prefix + files[tag][i]
            start = starts[tag][i]*fs
            end = start + (durations[tag][i]*fs)

            # Load data into their variables
            dataset = pd.read_csv(filename, delimiter=' ', header=header)
            data = dataset.values

            v_pd = data[start:end, pdn]
            v_lp = data[start:end, lpn]
            v_extra = data[start:end, extra]

            ini_times_dict[tag] = {}
            end_times_dict[tag] = {}

            period, lppd_interval, _, _, _, _, pd_burst = invariants(v_extra, v_pd, is_extra=True,
                                                                     ini_times=ini_times_dict[tag],
                                                                     end_times=end_times_dict[tag])

            v_data_dict[tag] = {}
            v_data_dict[tag]['lp'] = v_extra
            v_data_dict[tag]['pd'] = v_pd

            periods_dict[tag] = period

            if tag == "lppd":
                ints_dict[tag] = lppd_interval
            elif tag == "pd":
                ints_dict[tag] = pd_burst

    return v_data, periods, intervals, ini_times, end_times


def compute_speeds(n, resample, wsize=20, path='captura_patas_videos/'):
    # Create general list for all experiments
    speeds = []
    times = []
    distances = []

    # TODO: mejorar y unificar bucle con el del plot de la figura
    for i in range(n_exp):
        # Link list and dict to avoid append
        # speed automatically update with speed_dict
        speeds.append({})
        speed_dict = speeds[-1]

        times.append({})
        time_dict = times[-1]

        distances.append({})
        distance_dict = distances[-1]

        # Load data for all tags in the experiment
        data_videos = {tag: pd.read_csv(path+experiments[i]+"_"+tag+".txt", delimiter=" ").values
                       for tag in intervals_tags}

        # Calculate end_video value for current experiment as de minimum value for a interval tag
        # Example: LPPD: 605; PD: 1206 --> end_video = 605
        # end_video = min([data.shape[0] for tag, data in data_videos.items()])

        # y_inter = data_videos[np.argmin([data.shape[0] for tag, data in data_videos.items()])]

        end_video = -1

        for tag in intervals_tags:
            data_video = data_videos[tag]

            # Negative sign inverts the signal
            #   (camera starts at 1920 pixel from the right)
            s = - data_video[start_video:end_video, 3]

            # Sliding window
            window_size = n*2
            kernel = np.ones(window_size) / window_size
            smoothed_data = np.convolve(s, kernel, mode='valid')
            s = smoothed_data

            # derivative = diff/sampling_rate
            ds = np.diff(s)*n

            # Sliding window over derivative
            window_size = n*2
            kernel = np.ones(window_size) / window_size
            smoothed_data = np.convolve(ds, kernel, mode='valid')
            ds = smoothed_data  # px / s

            # represent x-axis as time (seconds)
            time = data_video[start_video:end_video-1-(window_size-1)*2, 0]/1000
            # represent x-axis as cm (xvalues)
            distance = data_video[start_video:end_video-1-(window_size-1)*2, 3] * cm_per_px

            if resample:
                # Resample
                time -= 10  # ajuste tiempo final

                distance -= 10  # ajuste distancia final
                f = interp1d(distance, ds, fill_value='extrapolate')

                # x_resample = np.linspace(10, 50, 100)
                # ignores 10s end of video.
                x_resample = np.arange(0, 40.5, 0.5)
                ds = f(x_resample)
                distance = x_resample

            ds = ds[::-1]

            speed_dict[tag] = ds * cm_per_px
            distance_dict[tag] = distance
            time_dict[tag] = time

    return speeds, times, distances


def get_std_distribution(data, wsize=20):
    # Create general list for all experiments
    std_distributions = []

    for i in range(n_exp):
        std_distributions.append({})
        std_dict = std_distributions[-1]

        for tag in intervals_tags:
            std_dict[tag] = get_std_distribution_sliding(data[i][tag], data[i][tag].shape[0]//wsize)
            # std_dict[tag] = get_std_distribution_sliding(data[i][tag], wsize)

    return std_distributions


fig_format = 'pdf'

fig_width = 15
row_height = 2.5  #Best value to fit paper!
start_video = 0
end_video = -1
cm_per_px = 0.03

intervals_tags = ["lppd", "pd"]

#experiments = ["sub1", "sub6", "sub14", "sub15_2", "sub16"]
experiments = ["experiment1", "experiment2", "experiment4", "experiment5", "experiment6"]
n_exp = len(experiments)

files = {}
durations = {}
starts = {}

#files["lppd"] = ["2022y_11m_16d/17h_20m_12s.txt", "2022y_11m_16d/17h_50m_39s.txt", "2022y_11m_23d/16h_33m_17s.txt", "2022y_11m_28d/16h_14m_40s.txt", "2022y_11m_23d/17h_7m_11s.txt"]
#files["pd"] = ["2022y_11m_16d/17h_32m_0s.txt", "2022y_11m_16d/17h_58m_46s.txt", "2022y_11m_23d/16h_45m_38s.txt", "2022y_11m_28d/16h_21m_26s.txt", "2022y_11m_23d/17h_12m_20s.txt"]

files["lppd"] = ["experiment1_lppd_signal.txt", "experiment2_lppd_signal.txt", "experiment3_lppd_signal.txt", "experiment4_lppd_signal.txt", "experiment5_lppd_signal.txt"]
files["pd"] = ["experiment1_pd_signal.txt", "experiment2_pd_signal.txt", "experiment3_pd_signal.txt", "experiment4_pd_signal.txt", "experiment5_pd_signal.txt"]

# Values of video duration: time to reach final mark
durations["lppd"] = [49, 54, 33, 35, 50]
durations["pd"] = [24, 62, 41, 35, 40]

labels = ["invariant", "no invariant"]
prefix = "data/"


fs = 10000                                         # Sampling rate (in Hz)
calibration_time = 5.0                             # Calibration time for drift compensation (in seconds)
calibration_pts = int(calibration_time * fs)

# start = 21 * fs                                 # Start time to skip controls or calibration times (seconds x sampling rate)
#start time value for each file:
starts["lppd"] = [39, 47, 27, 30, 30]
starts["pd"] = [25, 52, 22, 32, 31]


header = 2

extra = 3     # Extracellular signal column
pdn = 2     # PD intracellular signal column
lpn = 1     # LP intracellular signal column

period_col = 8
ampl_col = 9

upper_th_pd = 0.7  # Upper threshold for PD
upper_th_lp = 0.7  # Upper threshold for LP
lower_th_pd = 0.4  # Lower threshold for PD
lower_th_lp = 0.4  # Lower threshold for LP


norms_min = {}
norms_max = {}
norms_min["lppd"] = [407.7, 967.7, 533, 517.3, 741.6]
norms_max["lppd"] = [1308.2, 1890.1, 1047.3, 733.8, 1326.2]
norms_min["pd"] = [81.4, 119, 110.1, 117.0, 124.3]
norms_max["pd"] = [173.9, 179.6, 165.7, 162.3, 160.2]
MAX_AMPLITUDE = 40#Max angle
MIN_AMPLITUDE = 6#Min angle


# Get intervals, speed and plot main figure
print("computing speeds...")
n = 25 * 1  # 25 ptos (frames) son un 1s
org_speeds, org_times, org_distances = compute_speeds(n, resample=False)
speeds, times, distances = compute_speeds(n, resample=True)

for i in range(n_exp):
    fig, axs = plt.subplots(nrows=2, figsize=(20,10), sharex=True)
    for i_tag, tag in enumerate(intervals_tags):
        filename = prefix + files[tag][i]
        start = starts[tag][i]*fs
        end = start + (durations[tag][i]*fs)

        # Load data into their variables
        dataset = pd.read_csv(filename, delimiter=' ', header=header)
        data = dataset.values

        v_pd = data[start:end, pdn]
        v_lp = data[start:end, extra]

        norm_pd = (v_pd - np.min(v_pd)) / (np.max(v_pd) - np.min(v_pd))
        norm_lp = (v_lp - np.min(v_lp)) / (np.max(v_lp) - np.min(v_lp))

        period = data[start:end, period_col]
        amplitude = data[start:end, ampl_col]

        time = data[start:end, 0]
        ax2 = axs[i_tag].twinx()
        axs[i_tag].plot(time, norm_lp, color='blue', alpha=0.5)
        axs[i_tag].plot(time, norm_pd, color='orange', alpha=0.8)

        ax2.scatter(time, period, color='darkblue', label='period')
        ax2.scatter(time, amplitude, color='darkorange', label='amplitude')
        
        angles= ((amplitude*10 - norms_min[tag][i]) / (norms_max[tag][i]-norms_min[tag][i])) * (MAX_AMPLITUDE - MIN_AMPLITUDE) + MIN_AMPLITUDE

        ax2.scatter(time, angles, color='red', label='angles*10')

        ax2.legend()
        
        plt.title("Experiment %d, %s"%(i+1, tag))
    plt.show()



print("getting intervals...")
v_data, periods, ints, ini_times, end_times = get_intervals_dict()

fig, axs = plt.subplots(n_exp, 2, figsize=(fig_width, row_height*n_exp), gridspec_kw={'width_ratios': [1.5, 2.5]})

for i in range(n_exp):
    # Plot invariants
    plot_two_invariant(fig, axs[i, 0], periods[i]["lppd"][1:], periods[i]["pd"][1:], ints[i]["lppd"][1:], ints[i]["pd"][1:], id=i+1)

    # Plot speeds

    # Plot for interval 1
    axs[i, 1].plot(distances[i]["lppd"], speeds[i]["lppd"], color="tab:blue", label="%s std %.2f"%(labels[0],np.std(speeds[i]["lppd"])))#Derivada de X frente a tiempo filtrada

    axs[i, 1].plot(distances[i]["pd"], speeds[i]["pd"], color="tab:orange", label="%s std %.2f"%(labels[1],np.std(speeds[i]["pd"])))#Derivada de X frente a tiempo filtrada

    axs[i, 1].set_ylabel("Speed (cm/s)")
    axs[i, 1].legend(loc="upper left")
    if i < n_exp-1:
        remove_axes(axs[i, 1], ['top', 'right', 'bottom'])
        axs[i, 1].set_xticks([])
    else:
        remove_axes(axs[i, 1])

    # Importante para la representación
    axs[i, 1].set_ylim(0, 3)


axs[-1, 1].set_xlabel("Distance (cm)")
axs[-1, 0].set_xlabel("Cycle period (s)")

plt.tight_layout()
plt.savefig('./images/speed_panel.%s' % fig_format, format=fig_format)
# plt.show()

secs = 1/fs
colors = ['red', 'blue']


for i in range(n_exp):
    fig_trace, axs_traces = plt.subplots(4, 2, figsize=(fig_width, row_height*n_exp),sharex=True)
    fig_trace.suptitle('Experiment %d' % (i+1))

    for i_tag, tag in enumerate(intervals_tags):
        v_lp = v_data[i][tag]['lp']
        v_pd = v_data[i][tag]['pd']

        time = np.arange(0, len(v_lp), 1) * secs

        for ini, end in zip(ini_times[i][tag]['lp'][:-1], ini_times[i][tag]['lp'][1:]):
            axs_traces[0, i_tag].hlines(y=v_lp[ini]+0.1, xmin=ini * secs, xmax=end * secs, color='green', linewidth=6, alpha=0.6, label='period')  
            axs_traces[1, i_tag].hlines(y=v_pd[ini]+0.1, xmin=ini * secs, xmax=end * secs, color='green', linewidth=6, alpha=0.6)  

        # Plot v_lp with horizontal lines
        axs_traces[0, i_tag].plot(time, v_lp)
        for ini, end in zip(ini_times[i][tag]['lp'], ini_times[i][tag]['pd']):
            axs_traces[0, i_tag].hlines(y=v_lp[ini], xmin=ini * secs, xmax=end * secs, color='red', linewidth=6, alpha=0.4, label='lppd')

        # Plot v_pd with horizontal lines
        axs_traces[1, i_tag].plot(time, v_pd)
        for ini, end in zip(ini_times[i][tag]['pd'], end_times[i][tag]['pd']):
            axs_traces[1, i_tag].hlines(y=v_pd[ini], xmin=ini * secs, xmax=end * secs, color='blue', linewidth=6, alpha=0.4, label='pd')

        # Plot speed values
        axs_traces[2, i_tag].plot(org_times[i][tag], org_speeds[i][tag], label="Speed")
        axs_traces[2, i_tag].set_ylabel('Speed (cm/s)')
        axs_traces[2, i_tag].set_ylim(0,3)


        if i == 3 and tag=='pd':
            cycle_refs = np.array(ini_times[i][tag]['lp'][1:-2]) * secs

            interval = np.array(ints[i][tag][1:])
            period = np.array(periods[i][tag][1:])
        else:
            cycle_refs = np.array(ini_times[i][tag]['lp'][1:-1]) * secs

            interval = np.array(ints[i][tag][1:])
            period = np.array(periods[i][tag][1:])

        print(cycle_refs.shape, interval.shape, period.shape)

        axs_traces2 = axs_traces[2, i_tag].twinx()



        # axs_traces2.vlines(x=cycle_refs, ymin=0, ymax=interval, color=colors[i_tag], alpha=0.4, label=tag)
        # axs_traces2.vlines(x=cycle_refs, ymin=0, ymax=period, color='green', alpha=0.4, label='period')
        # # axs_traces2.vlines(x=cycle_refs, ymin=0, ymax=interval/period, color='purple', alpha=0.4)

        # relation = interval[1:]/interval[:-1]
        relation = interval/period
        # norm_relation =  (relation - np.min(interval))/(np.max(interval) - np.min(interval))
        norm_relation =  (relation - np.min(interval))/(np.max(interval) - np.min(interval))
        # norm_relation = (relation - np.min(period)) / (np.max(period) - np.min(period))
        axs_traces2.plot(cycle_refs, norm_relation, color='purple', alpha=0.4, label='interval relation')
        # axs_traces2.plot(cycle_refs[:-1], relation, color='purple', alpha=0.4, label='interval relation')

        # Set labels for the y-axes
        axs_traces2.set_ylabel('Interval/period relation')


        # axs_traces2.set_ylim(0.6, 0.8)

        # Set labels for the y-axes
        # axs_traces2.set_ylabel('Intervals (s)')
        axs_traces2.legend()

        # Plot speed values
        axs_traces[3, i_tag].plot(org_times[i][tag], org_speeds[i][tag], label="Speed")
        axs_traces[3, i_tag].set_ylabel('Speed (cm/s)')
        axs_traces[3, i_tag].set_ylim(0,3)

        # Plot cycle values
        axs_traces2 = axs_traces[3, i_tag].twinx()

        #normalized and transposed to angles
        c = 2.5#longitud de la pata
        norms_min = {}
        norms_max = {}
        norms_min["lppd"] = [407.7, 967.7, 533, 517.3, 741.6]
        norms_max["lppd"] = [1308.2, 1890.1, 1047.3, 733.8, 1326.2]
        norms_min["pd"] = [81.4, 119, 110.1, 117.0, 124.3]
        norms_max["pd"] = [173.9, 179.6, 165.7, 162.3, 160.2]
        MAX_AMPLITUDE = 40#Max angle
        MIN_AMPLITUDE = 6#Min angle


        angles= ((interval*1000 - norms_min[tag][i]) / (norms_max[tag][i]-norms_min[tag][i])) * (MAX_AMPLITUDE - MIN_AMPLITUDE) + MIN_AMPLITUDE
        # axs_traces2.plot(cycle_refs, angles/period, color='green', alpha=0.4)
        axs_traces2.plot(cycle_refs, 2*c*np.sin(angles*2*np.pi/360.)/period, color='green', alpha=0.4, label = 'Angle/period')       
        axs_traces2.set_ylabel('Angle/period relation')
        axs_traces2.legend()


        axs_traces[0, 0].set_title("LPPD")
        axs_traces[0, 1].set_title("PD")

    plt.tight_layout()

plt.show()

# Statistical test
def test(test, data, equal_var=True, verbose=True, center='median'):
    p_values = []
    for i in range(n_exp):

        d_lppd = list(data[i]['lppd'])
        d_pd = list(data[i]['pd'])

        # Realiza la prueba t de Student
        t_stat, p_value = test(d_lppd, d_pd)

        if test == stats.levene:
            t_stat, p_value = test(d_lppd, d_pd, center=center)

        p_values.append(p_value)

    print(str(p_values).replace(',', ';').replace('.', ','))
    return p_values

def print_all_tests(data):

    print("\n\nmannwhitneyu")
    test(stats.mannwhitneyu, data, verbose = False)

    print("\n\nKolmogorov-Smirnov")
    test(stats.ks_2samp, data, verbose=False)

# wsize = 20
wsize=4

print("\n\nNO RESAMPLED")

# wsize = 150
org_std_distributions = get_std_distribution(org_speeds, wsize)


print("\n\nTEST ON STD DISTRIBUTIONS")
print_all_tests(org_std_distributions)


means_lppd = [np.mean(org_std_distributions[i]["lppd"]) for i in range(n_exp)]
means_pd = [np.mean(org_std_distributions[i]["pd"]) for i in range(n_exp)]

stdslp = [np.std(org_std_distributions[i]["lppd"]) for i in range(n_exp)]
stdspd = [np.std(org_std_distributions[i]["pd"]) for i in range(n_exp)]


plt.figure(figsize=(fig_width, row_height))
# plt.xlabel("Experiment No.")
plt.ylabel("STD distribution mean")
plt.errorbar(x=[1, 2, 3, 4, 5], y=means_lppd, yerr=stdslp, xerr=0.05, fmt=' ', label=labels[0])
plt.errorbar(x=[1.1, 2.1, 3.1, 4.1, 5.1], y=means_pd, yerr=stdspd, xerr=0.05, fmt=' ', label=labels[1])

from mpl_toolkits.axes_grid1.inset_locator import mark_inset

p_values = test(stats.ks_2samp, org_std_distributions, verbose = False)
print(p_values)
# Statistical significance:
for i,p in enumerate(p_values):
    if p < 0.001:
        significance = "***"
    elif p < 0.01:
        significance = "**"
    elif p < 0.05:
        significance = "*"
    else:
        significance = ""
    
    # for i, (lppd,pd) in enumerate(zip((means_lppd+stdslp), (means_pd+stdspd))):
    # Find the maximum value and its corresponding index
    max_y_lppd = means_lppd[i] + stdslp[i]
    max_x_lppd = i+1

    max_y_pd = means_pd[i] + stdspd[i]
    max_x_pd = i+1.1

    # Annotate with asterisks if desired
    # plt.annotate(significance, xy=(max_x_lppd, max_y_lppd), xytext=(max_x_lppd, max_y_lppd + 0.05))

    plt.annotate(significance, xy=(max_x_lppd, max_y_pd), xytext=(max_x_lppd+0.02, max_y_pd + 0.05))
    plt.hlines(y=max_y_pd + 0.04, xmin=i+1, xmax=i+1.1, color='black', linestyle='-', linewidth=1)

    # # Add vertical markers at the ends of the line
    # plt.vlines(x=max_x_lppd, ymin=max_y_lppd+0.05, ymax=max_y_pd + 0.14, color='black', linestyle='-', linewidth=1)
    # plt.vlines(x=max_x_pd, ymin=max_y_pd+0.05, ymax=max_y_pd + 0.14, color='black', linestyle='-', linewidth=1)

    ax = plt.gca()

experiments_labels = ["Experiment %d"%(i+1) for i in range(n_exp)]
plt.xticks([1.05, 2.05, 3.05, 4.05, 5.05],experiments_labels)
ax = plt.gca()
remove_axes(ax)
# plt.title("NO RESAMPLED\n wsize=1/%d"%wsize)
plt.legend()
plt.tight_layout()
plt.savefig('./images/std_distribution_errors_ORIGINAL_w%d.%s' % (wsize, fig_format), format=fig_format)


