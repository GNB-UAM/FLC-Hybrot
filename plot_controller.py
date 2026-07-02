import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def plot_single(filename):
	dataset = pd.read_csv(filename, delimiter=' ', header=2)
	data = dataset.values
	i = [x / 1000000 for x in data[:,0]] # s
	p = data[:,2]
	e = data[:,1]
	v = data[:,3]

	e2 = [x*10000 for x in e]
	v2 = [x*1000 for x in v]

	fig = plt.figure(figsize=(12,8))
	
	#Plots
	ax1 = plt.subplot(3, 1, 1)
	plt.ylabel("Voltage (V)")
	plt.plot(i, v)

	ax2 = plt.subplot(3, 1, 2, sharex=ax1)
	plt.ylabel("Current (nA)")
	plt.plot(i, e)

	ax3 = plt.subplot(3, 1, 3, sharex=ax1)
	plt.ylabel("Period (s)")
	plt.plot(i, p)
	
	#Details
	plt.xlabel("Time (s)")
	plt.tight_layout()
	plt.show()

	
	
	
	plt.show()



def plot_invariant(filename, th_lo_per, th_up_per, th_lo_per_lp=None, th_up_per_pd=None):
	start = 0
	end = -1
	dataset = pd.read_csv(filename, delimiter=' ', header=3)
	data = dataset.values
	t = np.array([x / 1000000 for x in data[start:end,0]]) # s
	c = data[start:end,1]
	v_pd = data[start:end,2]
	v_lp = data[start:end,3]
	e_pd = data[start:end,4]
	e_pd_end = data[start:end,5]
	e_lp = data[start:end,6]
	e_lp_end = data[start:end,7]
	first_interval = [x / 1000 for x in data[start:end,8]]
	second_interval = [x / 1000 for x in data[start:end,9]]

	#v_pd = [x + 3 for x in v_pd]

	fig = plt.figure(figsize=(12,8))

	#Plots
	ax1 = plt.subplot(5, 1, 1)
	plt.ylabel("Voltage (V)")
	plt.plot(t, v_lp)
	on_events = t[np.where(e_lp)]
	off_events = t[np.where(e_lp_end)]
	plt.plot(on_events, np.ones(on_events.shape)*np.max(v_lp), '.', markersize=10, color='green')
	plt.plot(off_events, np.ones(off_events.shape)*np.max(v_lp), '.', markersize=10, color='red')

	th_up = np.min(v_lp) + ((np.max(v_lp)-np.min(v_lp)) * th_up_per)
	plt.hlines(th_up, xmin=t[0], xmax=t[-1], label="th_up", linestyles="dashed", color='purple')

	if th_lo_per_lp is None:
		th_lo = np.min(v_lp) + ((np.max(v_lp)-np.min(v_lp)) * 0.4)
		plt.hlines(th_lo, xmin=t[0], xmax=t[-1], label="th_low (fixed)", linestyles="dashed", color='black')
	else:
		th_lo = np.min(v_lp) + ((np.max(v_lp)-np.min(v_lp)) * th_lo_per_lp)
		plt.hlines(th_lo, xmin=t[0], xmax=t[-1], label="th_low", linestyles="dashed", color='navy')


	plt.legend()
	
	ax2 = plt.subplot(5, 1, 2, sharex=ax1)
	plt.ylabel("Voltage (V)")
	plt.plot(t, v_pd)

	on_events = t[np.where(e_pd)]
	off_events = t[np.where(e_pd_end)]
	plt.plot(on_events, np.ones(on_events.shape)*np.max(v_pd), '.', markersize=10, color='green')
	plt.plot(off_events, np.ones(off_events.shape)*np.max(v_pd), '.', markersize=10, color='red')

	th_lo = np.min(v_pd) + ((np.max(v_pd)-np.min(v_pd)) * th_lo_per)
	plt.hlines(th_lo, xmin=t[0], xmax=t[-1], label="th_low", linestyles="dashed", color='navy')

	if th_up_per_pd is None:
		th_up = np.min(v_pd) + ((np.max(v_pd)-np.min(v_pd)) * 0.7)
		plt.hlines(th_up, xmin=t[0], xmax=t[-1], label="th_up (fixed)", linestyles="dashed", color='black')
	else:
		th_up = np.min(v_pd) + ((np.max(v_pd)-np.min(v_pd)) * th_up_per_pd)
		plt.hlines(th_up, xmin=t[0], xmax=t[-1], label="th_up", linestyles="dashed", color='purple')
	
	plt.legend()

	ax3 = plt.subplot(5, 1, 3, sharex=ax1)
	plt.ylabel("Current (nA)")
	plt.plot(t, c)

	ax4 = plt.subplot(5, 1, 4, sharex=ax1)
	plt.ylabel("First interval (s)")
	plt.plot(t, first_interval)

	ax4 = plt.subplot(5, 1, 5, sharex=ax1)
	plt.ylabel("Second interval (s)")
	plt.plot(t, second_interval)

	plt.xlabel("Time (s)")
	plt.tight_layout()
	plt.show()




filename = ""
if len(sys.argv) < 2:
	print("Filename missing!")
	sys.exit()
else:
	filename = sys.argv[1]

file = open(filename, 'r')
line = file.readline()		# primera línea
second_line = file.readline() # segunda línea
file.close()

# Extraer los dos parámetros de la segunda línea
# Formato esperado: "th_lo_per 0.40 th_up_per 0.70"
parts = second_line.split()
th_lo_per = float(parts[1])
th_up_per = float(parts[3])

try:
	th_lo_per_lp = float(parts[5])
	th_up_per_pd = float(parts[7])
except:
	th_lo_per_lp = None
	th_up_per_pd = None

print(th_lo_per_lp, th_up_per_pd)

line = line.strip('\n')
if line == "0":
	print("Single neuron experiment")
	plot_single(filename)
elif line == "1":
	print("Invariant experiment")
	plot_invariant(filename, th_lo_per, th_up_per, th_lo_per_lp, th_up_per_pd)
else:
	print("Unknown type of experiment.")
	sys.exit()