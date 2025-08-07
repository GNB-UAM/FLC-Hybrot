import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from scipy.interpolate import interp1d



def get_amplitude_period(red_x):
	max_seno = []
	min_seno = []
	max_t = []
	min_t = []

	flag_subiendo = 0
	last_min_max = 0 # 1 si el ultimo ha sido un min, 2 si ha sido un max

	for i in range(1, len(t)-1):
		if (red_x[i] > red_x[i-1] and last_min_max != 2):
			flag_subiendo = 1

		if (red_x[i] < red_x[i-1] and last_min_max != 1):
			flag_subiendo = 0

		if (flag_subiendo == 1 and red_x[i] > red_x[i+1]):
			max_seno.append(red_x[i])
			max_t.append(t[i])
			last_min_max = 2


		if (flag_subiendo == 0 and red_x[i] < red_x[i+1]):
			min_seno.append(red_x[i])
			min_t.append(t[i])
			last_min_max = 1

	if len(min_t) > len(max_t): 
		ts = min_t
	else:
		ts = max_t

	periodo_seno = [ts[i] - ts[i-1] for i in range(1, len(ts))]


	plt.plot(max_t, max_seno)
	plt.plot(min_t, min_seno)
	plt.plot(t, red_x)
	plt.show()

	# print(len(ts))

	amplitud_seno = []
	if (len(max_seno) >= len(min_seno)):
		for i in range(len(min_seno)):
			amplitud_seno.append(max_seno[i] - min_seno[i])
	else:
		for i in range(len(max_seno)):
			amplitud_seno.append(max_seno[i] - min_seno[i])


	return amplitud_seno, periodo_seno, ts


obs_time = 10


# File with the signals recording
filename = "../data/intervals_data.txt"

start = 0
end = -1
print("Reading data ", filename)
dataset = pd.read_csv(filename, delimiter=' ', header=2)
data = dataset.values
index = [(x / 1000000) - obs_time for x in data[start:end,0]] # s
c = data[start:end,1]
v_pd = data[start:end,2]
v_lp = data[start:end,3]
e_pd = data[start:end,4]
e_lp = data[start:end,5]
p = [x / 1000 for x in data[start:end,6]]

period_times = []
period_first = []
for j in range(1, len(p)):
	if p[j] != p[j-1]:
		period_times.append(index[j])
		period_first.append(p[j])


interval_lppd = []
last_lp = 0
interval = 0
for k in range(len(index)):
	if (e_pd[k] == 1):
		interval = k - last_lp

	if (e_lp[k] == 1):
		last_lp = k

	interval_lppd.append(interval)

interval_lppd = [x / 10 for x in interval_lppd]


interval_times = []
interval_first = []
for j in range(1, len(interval_lppd)):
	if interval_lppd[j] != interval_lppd[j-1]:
		interval_times.append(index[j])
		interval_first.append(interval_lppd[j])



min_pd = np.min(v_pd[:15000])
max_pd = np.max(v_pd[:15000])
range_pd = max_pd - min_pd

v_pd_filt = []
for k in range(len(index)):
	if (k > 600 and k < len(index)-600 and v_pd[k] < (min_pd + range_pd * 0.7)):
		v_pd_filt.append(np.mean(v_pd[k-600:k+600]))
	elif (k > 100 and k < len(index)-100 and v_pd[k] >= (min_pd + range_pd * 0.7)):
		#v_pd_filt.append(np.mean(v_pd[k-10:k+10]))
		v_pd_filt.append(v_pd[k])
	else:
		v_pd_filt.append(v_pd[k])

	if (k % 15000 == 0 and k > 15000 and k < len(index)-15000):
		min_pd = np.min(v_pd[k-15000:k+15000])
		max_pd = np.max(v_pd[k-15000:k+15000])
		range_pd = max_pd - min_pd



# File with the video tracking
filename_video = "../data/legs-tracking.txt"
print("Reading video tracking ", filename_video)
dataset_video = pd.read_csv(filename_video, delimiter=' ', header=0)
data_video = dataset_video.values

start_video = 0
end_video = -1

t = [(x / 1000) for x in data_video[start_video:end_video,0]]
blue_x = data_video[start_video:end_video,1]
blue_y = data_video[start_video:end_video,2]
yellow_x = data_video[start_video:end_video,3]
yellow_y = data_video[start_video:end_video,4]
red_x = data_video[start_video:end_video,5]
red_y = data_video[start_video:end_video,6]

t = [(x - t[0]) for x in t]

from scipy import signal
plt.plot(t, red_x)
plt.show()
red_x = signal.detrend(red_x)
plt.plot(t, red_x)
plt.show()




f2 = interp1d(t, red_x, kind='cubic')
t_interpl = np.linspace(t[0], t[-1], num=10000000 , endpoint=True)
red_x_interpl = f2(t_interpl)

b, a = signal.butter(3, 0.2)
zi = signal.lfilter_zi(b, a)
z, _ = signal.lfilter(b, a, red_x, zi=zi*red_x[0])
z2, _ = signal.lfilter(b, a, z, zi=zi*z[0])
y = signal.filtfilt(b, a, red_x)

#plt.plot(t, red_x)
plt.plot(t, y)
plt.show()

red_x_old = red_x
red_x = y


b, a = signal.butter(3, 0.045, btype='highpass')
zi = signal.lfilter_zi(b, a)
z, _ = signal.lfilter(b, a, red_x, zi=zi*red_x[0])
z2, _ = signal.lfilter(b, a, z, zi=zi*z[0])
y = signal.filtfilt(b, a, red_x)

#plt.plot(t, red_x)
plt.plot(t, y)
plt.show()

#red_x = y
legs_oscillation_display = y

amplitud_seno, periodo_seno, ts = get_amplitude_period(legs_oscillation_display)

periodo_seno = [x for x in periodo_seno] # por que * 2? lo quito por ahora
amplitud_seno = [x / np.max(amplitud_seno) for x in amplitud_seno]
# print(len(periodo_seno))
# print(len(amplitud_seno))



# Use plot_record_video_shadows.py for invariants plot

# slope_interval, intercept_interval, r_interval, pvalue_interval, std_error_interval = stats.linregress(periodo_seno, amplitud_seno)
# r2_interval = r_interval*r_interval


# plt.figure(figsize=(7,5))
# plt.scatter(periodo_seno, amplitud_seno, c=np.linspace(0, t[-1], len(periodo_seno)), cmap=plt.get_cmap("Blues"))
# plt.colorbar()
# plt.plot(periodo_seno, intercept_interval+(slope_interval*np.asarray(periodo_seno)), alpha=0.5, color='blue', label="R2=%f"%r2_interval)

# plt.ylim(bottom=0.25, top=1.05)
# plt.xlim(left=0.65, right=1.5)

# plt.legend()

# plt.xlabel('Legs period [s]')
# plt.ylabel('Legs amplitude [cm] (norm)')

# plt.tight_layout()
# plt.show()


p = [x * 1000 for x in p]
plt.plot(np.divide(amplitud_seno, periodo_seno))
plt.show()



ve_lp = []
for i in range(len(e_lp)):
	if (e_lp[i] == 1):
		ve_lp.append(v_lp[i])
	else:
		ve_lp.append(-1)



# plot it
f, (a0, a1) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3, 3]}, sharex = True)
a0.plot(index[10000:70000], v_lp[10000:70000], "steelblue")
#a0.plot(index, ve_lp, "o")
a0.set_ylabel("Voltage (mV)")
#a0.set_ylim(bottom=0)


a1.plot(index[10000:70000], v_pd_filt[10000:70000], "darkolivegreen")
a1.set_ylabel("Voltage (mV)")

f.tight_layout()
f.show()
plt.show()


# plot it
f, (a0, a1, a2) = plt.subplots(3, 1, gridspec_kw={'height_ratios': [3, 3, 3]}, sharex = True)
a0.plot(index, v_lp, "steelblue")

a0.set_ylabel("Voltage (mV)")
a0.set_xlim(left=6, right=9)


a1.plot(index, v_pd_filt, "darkolivegreen")
a1.set_ylabel("Voltage (mV)")
a1.set_xlim(left=6, right=9)

a2.plot(t, red_x, "red")
a2.set_xlim(left=6, right=9)

f.tight_layout()
f.show()
plt.show()


first_index = 10 * 10000
last_index = int((46.28+10) * 10000)

# plot it
f, (a0, a1, a2, a3) = plt.subplots(4, 1, gridspec_kw={'height_ratios': [3, 3, 3, 3]}, sharex = True)


a0.plot(index[:last_index - first_index], v_pd_filt[first_index:last_index], "darkolivegreen")
a0.set_ylabel("Voltage (mV)")


a1.plot(index[:last_index - first_index], v_lp[first_index:last_index], "steelblue")
a1.set_ylabel("Voltage (mV)")

a2.plot(t, legs_oscillation_display, "red")


a3.plot(index[:last_index - first_index], c[first_index:last_index], "orange")

f.tight_layout()
f.show()
plt.show()


jump = 5



first_index = 10 * 10000
last_index = int((46.28+10) * 10000)


plt.figure(figsize=(12,3))
plt.plot(index[:last_index - first_index], v_lp[first_index:last_index], "steelblue")
plt.xlim(left=0, right=46.28)
plt.tight_layout()
plt.show()

plt.figure(figsize=(12,3))
plt.plot(index[:last_index - first_index], v_pd_filt[first_index:last_index], "darkolivegreen")
plt.xlim(left=0, right=46.28)
plt.tight_layout()
plt.show()


plt.figure(figsize=(12,1))
plt.plot(index[:last_index - first_index], c[first_index:last_index], "orange")
plt.xlim(left=0, right=46.28)
plt.tight_layout()
plt.show()



plt.figure(figsize=(12,3))
plt.plot(t, legs_oscillation_display, "red")
plt.xlim(left=0, right=46.28)
plt.tight_layout()
plt.show()



plt.figure(figsize=(12,5))
plt.plot(np.array(period_times)-10, period_first)
plt.plot(ts[:-1], periodo_seno)
plt.xlim(left=0, right=46.28)
plt.tight_layout()
plt.show()
