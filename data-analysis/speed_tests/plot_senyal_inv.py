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


def plot_invariant(var1, var2, label1="var1", label2="var2", color="blue"):
	slope_interval, intercept_interval, r_interval, pvalue_interval, std_error_interval = stats.linregress(var1, var2)
	r2_interval = r_interval*r_interval

	plt.figure(figsize=(7,5))
	plt.scatter(var1, var2, c=np.linspace(0, len(var2), len(var1)), cmap=plt.get_cmap("Blues"))
	plt.colorbar()
	plt.plot(var1, intercept_interval+(slope_interval*np.asarray(var1)), alpha=0.5, color=color, label="R2 LPPD=%f"%r2_interval)

	plt.legend()

	#plt.ylim(bottom=0.25, top=1.05)
	#plt.xlim(left=0.65, right=1.5)

	plt.xlabel(label1)
	plt.ylabel(label2)

	plt.tight_layout()
	plt.show()


def invariants(v_lp, v_pd):
	upper_th_pd = 0.8
	upper_th_lp = 0.8
	lower_th_pd = 0.1
	lower_th_lp = 0.4

	flag_v_pd = 0
	ini_times_pd = []
	end_times_pd = []
	ini_v_pd = []
	end_v_pd = []
	min_v_pd = min(v_pd[0:15000])
	max_v_pd = max(v_pd[0:15000])
	r_v_pd = max_v_pd - min_v_pd

	flag_v_lp = 0
	ini_times_lp = []
	end_times_lp = []
	ini_v_lp = []
	end_v_lp = []
	min_v_lp = min(v_lp[0:15000])
	max_v_lp = max(v_lp[0:15000])
	r_v_lp = max_v_lp - min_v_lp


	lppd_interval = []
	lppd_delay = []
	pdlp_interval = []
	pdlp_delay = []
	pd_burst = []
	lp_burst = []
	period = []

	last_spike_lp_t = 0
	last_spike_lp_v = 0
	last_spike_pd_t = 0
	last_spike_pd_v = 0

	for i in range(len(v_pd)):
		#time.sleep(0.0001)

		if (v_pd[i] > (min_v_pd + r_v_pd*upper_th_pd) and flag_v_pd == 1):
			# PD burst starts
			flag_v_pd = 0

			ini_times_pd.append(i)
			ini_v_pd.append(v_pd[i])
		elif(v_pd[i] > (min_v_pd + r_v_pd*upper_th_pd)):
			# New spike of ongoing PD burst
			last_spike_pd_t = i
			last_spike_pd_v = v_pd[i]
		elif (v_pd[i] < (min_v_pd + r_v_pd*lower_th_pd) and flag_v_pd == 0):
			# PD burst ends
			flag_v_pd = 1

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
		elif(v_lp[i] > (min_v_lp + r_v_lp*upper_th_lp)):
			# New spike of ongoing LP burst
			last_spike_lp_t = i
			last_spike_lp_v = v_lp[i]
		elif (v_lp[i] < (min_v_lp + r_v_lp*lower_th_lp) and flag_v_lp == 0):
			# LP burst ends
			flag_v_lp = 1

			if (last_spike_lp_v != 0):
				end_times_lp.append(last_spike_lp_t)
				end_v_lp.append(last_spike_lp_v)


		if (i % 15000 == 0):
			min_v_lp = min(v_lp[i:i+15000])
			max_v_lp = max(v_lp[i:i+15000])

			min_v_pd = min(v_pd[i:i+15000])
			max_v_pd = max(v_pd[i:i+15000])




	lppd_interval = [x / 10000 for x in lppd_interval]
	lppd_delay = [x / 10000 for x in lppd_delay]
	pdlp_interval = [x / 10000 for x in pdlp_interval]
	pdlp_delay = [x / 10000 for x in pdlp_delay]
	pd_burst = [x / 10000 for x in pd_burst]
	lp_burst = [x / 10000 for x in lp_burst]
	period = [x / 10000 for x in period]



	plot_invariant(period, lppd_interval, label1="Period", label2="LPPD interval")
	plot_invariant(period, lppd_delay, label1="Period", label2="LPPD delay")
	plot_invariant(period, pdlp_interval, label1="Period", label2="PDLP interval")
	plot_invariant(period, pdlp_delay, label1="Period", label2="PDLP delay")
	plot_invariant(period, lp_burst, label1="Period", label2="LP burst")
	plot_invariant(period, pd_burst, label1="Period", label2="PD burst")



	return

#filename = "2019y7m5d/toma_inv_6.txt"
#filename = "signal_model_robot.txt"
filename = "/media/skynet/PHILIPS UFD/2022y_11m_28d/16h_43m_22s.txt"
dataset = pd.read_csv(filename, delimiter=' ', header=2)
data = dataset.values


start = int((0) * 10000) # 10s
end =  -1

i = [x / 10000 for x in data[start:end,0]]
c = data[start:end,1]
v_pd = data[start:end,2]
v_lp = data[start:end,3]
e_pd = data[start:end,4]
e_lp = data[start:end,5]
period = [x / 1000 for x in data[start:end,6]]

print(np.unique(period))

#v_lp[::2] = -v_lp[::2] # reconstruir el extracelular

v_lp_filt = filt_extracellular(v_lp)
v_lp_filt = v_lp

plt.plot(v_lp)
plt.plot(v_lp_filt)
plt.show()

v_pd_filt = filt_intracellular(v_pd)
plt.plot(v_pd)
plt.plot(v_pd_filt)
plt.show()


#invariants(v_lp_filt, v_pd_filt)


#v_pd = [x + 3 for x in v_pd]

interval_lppd = []
last_lp = 0
interval = 0
for k in range(len(i)):
	if (e_pd[k] == 1):
		interval = k - last_lp

	if (e_lp[k] == 1):
		last_lp = k

	interval_lppd.append(interval)

interval_lppd = [x / 10 / 1000 for x in interval_lppd]


period_single = []
interval_lppd_single = []
interval_pdlp_single = []
last_lp = 0
last_pd = 0

for k in range(len(i)):
	if (e_pd[k] == 1):
		interval = k - last_lp

		#if (len(period_single) > 0):
		if (last_lp != 0):
			interval_lppd_single.append(interval)

		last_pd = k


	if (e_lp[k] == 1):
		if (last_pd != 0):
			interval_pdlp_single.append(k - last_pd)

		if (len(interval_lppd_single) > 0):
			period_single.append(k - last_lp)
		last_lp = k


if (len(period_single) > len(interval_lppd_single)):
	period_single = period_single[:-1]

if (len(interval_lppd_single) > len(period_single)):
	interval_lppd_single = interval_lppd_single[:-1]

if (len(interval_pdlp_single) > len(period_single)):
	interval_pdlp_single = interval_pdlp_single[1:]


plt.plot(period_single)
plt.plot(interval_lppd_single)
plt.plot(interval_pdlp_single)
plt.show()

period_single = [x / 10000 for x in period_single]
interval_lppd_single = [x / np.max(interval_lppd_single) for x in interval_lppd_single]
interval_pdlp_single = [x / np.max(interval_pdlp_single) for x in interval_pdlp_single]

print(len(period_single))
print(len(interval_lppd_single))
print(len(interval_pdlp_single))

slope_interval, intercept_interval, r_interval, pvalue_interval, std_error_interval = stats.linregress(period_single, interval_lppd_single)
r2_interval = r_interval*r_interval

plt.figure(figsize=(7,5))
plt.scatter(period_single, interval_lppd_single, c=np.linspace(0, len(interval_lppd_single), len(period_single)), cmap=plt.get_cmap("Blues"))
plt.colorbar()
plt.plot(period_single, intercept_interval+(slope_interval*np.asarray(period_single)), alpha=0.5, color='blue', label="R2 LPPD=%f"%r2_interval)

plt.legend()

#plt.ylim(bottom=0.25, top=1.05)
#plt.xlim(left=0.65, right=1.5)

plt.xlabel('LP period [s]')
plt.ylabel('LPPD interval [s] (norm)')

plt.tight_layout()
plt.show()




slope_interval, intercept_interval, r_interval, pvalue_interval, std_error_interval = stats.linregress(period_single, interval_pdlp_single)
r2_interval = r_interval*r_interval

plt.figure(figsize=(7,5))
plt.scatter(period_single, interval_pdlp_single, c=np.linspace(0, len(interval_pdlp_single), len(period_single)), cmap=plt.get_cmap("Blues"))
plt.colorbar()
plt.plot(period_single, intercept_interval+(slope_interval*np.asarray(period_single)), alpha=0.5, color='blue', label="R2 LPPD=%f"%r2_interval)

plt.legend()

#plt.ylim(bottom=0.25, top=1.05)
#plt.xlim(left=0.65, right=1.5)

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

