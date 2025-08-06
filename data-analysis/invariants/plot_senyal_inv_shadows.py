import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy import signal
import scipy.fftpack

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = signal.butter(order, [low, high], btype='band')
    return b, a

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_highpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def plot_fft(data):
	# Number of samplepoints
	N = len(data)
	# sample spacing
	T = 1.0 / 800.0
	yf = scipy.fftpack.fft(data)
	xf = np.linspace(0.0, 1.0/(2.0*T), N/2)

	fig, ax = plt.subplots()
	ax.plot(xf, 2.0/N * np.abs(yf[:N//2]))
	plt.show()


def filt_extracellular(v):
	minv = np.min(v[:15000])
	maxv = np.max(v[:15000])
	rangev = maxv - minv
	th_up = 0.9
	th_lo = 0.1
	mean_pts = 3

	v_filt = []
	for k in range(len(v)):
		if (k > 100 and k < len(v)-100 and v[k] < (minv + rangev * th_up) and v[k] > (minv + rangev * th_lo)):
			v_filt.append(np.mean(v[k-mean_pts:k+mean_pts]))
		else:
			v_filt.append(v[k])

		if (k % 15000 == 0 and k > 15000 and k < len(v)-15000):
			minv = np.min(v[k-15000:k+15000])
			maxv = np.max(v[k-15000:k+15000])
			rangev = maxv - minv

	return v_filt


def filt_intracellular(v):
	minv = np.min(v[:15000])
	maxv = np.max(v[:15000])
	rangev = maxv - minv
	th_up = 0.45
	mean_pts_up = 10
	mean_pts_lo = 100

	v_filt = []
	for k in range(len(v)):
		if (k > 100 and k < len(v)-100 and v[k] < (minv + rangev * th_up)):
			v_filt.append(np.mean(v[k-mean_pts_lo:k+mean_pts_lo]))
		elif (k > 100 and k < len(v)-100 and v[k] >= (minv + rangev * th_up)):
			v_filt.append(np.mean(v[k-mean_pts_up:k+mean_pts_up]))
		else:
			v_filt.append(v[k])

		if (k % 15000 == 0 and k > 15000 and k < len(v)-15000):
			minv = np.min(v[k-15000:k+15000])
			maxv = np.max(v[k-15000:k+15000])
			rangev = maxv - minv

	return v_filt

#filename = "2019y7m5d/toma_inv_6.txt"
#filename = "signal_model_robot.txt"
filename = "controlador_robot/data/2021y_12m_1d/15h_33m_8s.txt"
dataset = pd.read_csv(filename, delimiter=' ', header=2)
data = dataset.values


start = 100000 # 10s
end = 562800 # 56.1s


# --- Extract data ---
i = [x / 10000 for x in data[start:end, 0]]
c = data[start:end, 1]
v_pd = data[start:end, 2]
v_lp = data[start:end, 3]
e_pd = data[start:end, 4]
e_lp = data[start:end, 5]
period = [x / 1000 for x in data[start:end, 6]]

# --- Filter traces ---
v_lp_filt = filt_extracellular(v_lp)
plt.plot(v_lp)
plt.plot(v_lp_filt)
plt.title("v_lp and filtered")
plt.show()

v_pd_filt = filt_intracellular(v_pd)
plt.plot(v_pd)
plt.plot(v_pd_filt)
plt.title("v_pd and filtered")
plt.show()

# --- Calculate LPPD intervals (absolute, not just single spike-to-spike) ---
interval_lppd = []
last_lp = 0
interval = 0
for k in range(len(i)):
    if e_pd[k] == 1:
        interval = k - last_lp
    if e_lp[k] == 1:
        last_lp = k
    interval_lppd.append(interval)

interval_lppd = [x / 10 / 1000 for x in interval_lppd]  # Convert to seconds

# --- Calculate single period and interval values + save PD spike indices ---
period_single = []
interval_lppd_single = []
pd_indices = []
last_lp = 0

for k in range(len(i)):
    if e_pd[k] == 1:
        interval = k - last_lp
        if last_lp != 0:
            interval_lppd_single.append(interval)
            pd_indices.append(k)

    if e_lp[k] == 1:
        if len(interval_lppd_single) > 0:
            period_single.append(k - last_lp)
        last_lp = k

# --- Detect regions where c < -0.5 ---
def find_regions_less_than_threshold(c, threshold=-0.5):
    c = np.asarray(c)
    regions = []
    in_region = False
    start = None

    for i, val in enumerate(c):
        if val < threshold and not in_region:
            start = i
            in_region = True
        elif val >= threshold and in_region:
            end = i - 1
            regions.append((start, end))
            in_region = False

    if in_region:
        regions.append((start, len(c) - 1))

    return regions

low_c_regions = find_regions_less_than_threshold(c, threshold=-0.5)
print("Regions where c < -0.5:", low_c_regions)
print(pd_indices)
# --- Tag intervals based on whether their PD spike falls into a low-c region ---
tags = []  # True if this interval falls within a c < -0.5 region
for idx in pd_indices:
    in_low_c = any(start <= idx <= end for (start, end) in low_c_regions)
    tags.append(in_low_c)

# --- Normalize and rescale values ---
period_single = [x / 10000 for x in period_single]  # Convert to seconds
interval_lppd_single = [x / np.max(interval_lppd_single) for x in interval_lppd_single]

# --- Linear regression ---
slope_interval, intercept_interval, r_interval, pvalue_interval, std_error_interval = stats.linregress(period_single, interval_lppd_single)
r2_interval = r_interval ** 2

# --- Convert to numpy arrays for indexing ---
period_single = np.asarray(period_single)
interval_lppd_single = np.asarray(interval_lppd_single)
tags = np.asarray(tags)
print(tags)
# --- Plot ---

plt.figure(figsize=(7,5))
plt.scatter(period_single[tags], interval_lppd_single[tags], color='grey', label='c < -0.5', s=100, alpha=0.6)
plt.scatter(period_single[~tags], interval_lppd_single[~tags], color='blue', label='c = 0', s=100, alpha=0.6)
plt.scatter(period_single, interval_lppd_single, c=np.linspace(0, len(interval_lppd_single), len(period_single)), cmap=plt.get_cmap("Blues"))

plt.colorbar()
plt.plot(period_single, intercept_interval+(slope_interval*np.asarray(period_single)), alpha=0.5, color='blue', label="R2 LPPD=%f"%r2_interval)

plt.legend()

plt.ylim(bottom=0.25, top=1.05)
plt.xlim(left=0.65, right=1.5)

plt.xlabel('LP period [s]')
plt.ylabel('LPPD interval [s] (norm)')

plt.tight_layout()
plt.show()



# plot it
f, (a0, a1) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [2, 2]}, sharex = True)
a0.plot(i, v_lp_filt, "lightseagreen")
a0.set_ylabel("Voltage (mV)")
a0.set_xlim(left=0, right=i[-1])

a1.plot(i, v_pd_filt, "darkolivegreen")
a1.set_ylabel("Voltage (mV)")
a1.set_xlim(left=0, right=i[-1])


#f.xlabel("Time (s)")
f.tight_layout()
f.show()
plt.show()


# plot it
f, (a0, a1, a2, a3) = plt.subplots(4, 1, gridspec_kw={'height_ratios': [2, 2, 1, 5]}, sharex = True)
a0.plot(v_lp, "lightseagreen")
a0.set_ylabel("Voltage (mV)")
#a0.set_xlim(left=2, right=i[-1])

a1.plot(v_pd, "darkolivegreen")
a1.set_ylabel("Voltage (mV)")
#a1.set_xlim(left=2, right=i[-1])


a2.plot(c, "orange")
a2.set_ylabel("Injected current (nA)")
#a2.set_xlim(left=2, right=i[-1])


a3.plot(period)
a3.plot(interval_lppd)
a3.set_ylabel("Burst duration (s)")
#a3.set_ylim(bottom=0.55, top=0.85)
#a3.set_xlim(left=2, right=i[-1])


#f.xlabel("Time (s)")
f.tight_layout()
f.show()
plt.show()

