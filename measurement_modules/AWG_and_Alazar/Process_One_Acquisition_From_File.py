# -*- coding: utf-8 -*-
"""
Created on Thu Apr 29 14:18:59 2021

@author: Ryan Kaufman - Hatlab
"""
from plottr.apps.autoplot import main
from plottr.data.datadict_storage import all_datadicts_from_hdf5
from hat_utilities.AWG_and_Alazar.Pulse_Sweeping_utils import boxcar_histogram
import numpy as np
import matplotlib.pyplot as plt

datapath = r'E:\Data\Cooldown_20210408\SNAIL_Amps\C1\Hakan_data\Sweeps\Amplifier_Pump_Power\2021-05-04\2021-05-04_0002_power_-2.0\2021-05-04_0002_power_-2.0.ddh5'

#autoplot, easiest way to see data if you dont need access to values 
# main(datapath, 'data')

#extracting individual arrays
dd = all_datadicts_from_hdf5(datapath)['data']

time_unit = dd['time']['unit']
time_vals = dd['time']['values']

rec_unit = dd['record_num']['unit']
rec_num = dd['record_num']['values']

I_plus = dd['I_plus']['values']
I_minus = dd['I_minus']['values']

Q_plus = dd['Q_plus']['values']
Q_minus = dd['Q_minus']['values']

#plotting averages
I_plus_avg = np.average(np.reshape(I_plus, (7500, 208)), axis = 0)
I_minus_avg = np.average(np.reshape(I_minus, (7500, 208)), axis = 0)
Q_plus_avg = np.average(np.reshape(Q_plus, (7500, 208)), axis = 0)
Q_minus_avg = np.average(np.reshape(Q_minus, (7500, 208)), axis = 0)

fig = plt.figure()
ax1 = fig.add_subplot(221)
ax1.set_title("I(t) averaged over records")
ax1.plot(time_vals[rec_num == 0], I_plus_avg, label = 'Positive Detuning')
ax1.plot(time_vals[rec_num == 0], I_minus_avg, label = 'Negative Detuning')
ax1.set_xlabel('Time (ns)')
ax1.set_ylabel('Voltage (DAC Value)')
ax1.legend()

ax2 = fig.add_subplot(222)
ax2.set_title("Q(t) averaged over records")
ax2.set_xlabel('Time (ns)')
ax2.set_ylabel('Voltage (DAC Value)')
ax2.plot(time_vals[rec_num == 0], Q_plus_avg, label = 'Positive Detuning')
ax2.plot(time_vals[rec_num == 0], Q_minus_avg, label = 'Negative Detuning')
ax2.legend()

ax3 = fig.add_subplot(223)
ax3.set_title("Trajectories")
ax3.set_aspect(1)
ax3.plot(I_minus_avg, Q_minus_avg, label = 'Negative')
ax3.plot(I_plus_avg, Q_plus_avg, label = 'Positive')
ax3.legend()

# ax4 = fig.add_subplot(224)
# #plot just one record, record 1000 for example
# ex_num = 1000
# filt = rec_num == ex_num #generates boolean array
# ax4.set_title(f'Record number {ex_num}')
# ax4.plot(time_vals[filt], I_plus[filt], label = 'I_plus')
# ax4.plot(time_vals[filt], I_minus[filt], label = 'I_minus')
# ax4.plot(time_vals[filt], Q_plus[filt], label = 'Q_plus')
# ax4.plot(time_vals[filt], Q_minus[filt], label = 'Q_minus')
# ax4.legend()
# ax4.set_xlabel('Time (ns)')
# ax4.set_ylabel('Voltage (DAC Value)')

ax4 = fig.add_subplot(224)
ax4.set_aspect(1)
boxcar_histogram(fig, ax4, 50, 150, I_plus, Q_plus)

