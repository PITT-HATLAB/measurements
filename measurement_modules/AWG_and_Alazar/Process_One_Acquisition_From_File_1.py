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
from mpl_toolkits.axes_grid1 import make_axes_locatable

datapath = r'E:\Data\Cooldown_20210408\SNAIL_Amps\C1\Hakan_data\Sweeps\Amplifier_Pump_Power\2021-05-04\2021-05-04_0005_power_1.5\2021-05-04_0005_power_1.5.ddh5'

def histogram(fig, ax, start_pt, stop_pt, sI, sQ, Ioffset = 0, Qoffset = 0, scale = 1, num_bins = 100, boxcar = True, I_weights = None, Q_weights = None):
    I_bground = Ioffset
    Q_bground = Qoffset
    if boxcar:
        weights = np.zeros(np.shape(sI)[1])
        weights[start_pt:stop_pt] = 1
        I_weights = weights.copy()
        Q_weights = weights.copy()
    # print(I_bground, Q_bground)
    I_pts = []
    Q_pts = []
    for I_row, Q_row in zip(sI, sQ): 
        I_pts.append(np.average(I_row-I_bground, weights = I_weights))
        Q_pts.append(np.average(Q_row-Q_bground, weights = Q_weights))
    # plt.imshow(np.histogram2d(np.array(I_pts), np.array(Q_pts))[0])
    divider = make_axes_locatable(ax)
    ax.set_aspect(1)
    bins = np.linspace(-1,1, num_bins)*scale
    (h, xedges, yedges, im) = ax.hist2d(I_pts, Q_pts, bins = [bins, bins])
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax = cax, orientation = 'vertical')
    # ax.hexbin(I_pts, Q_pts, extent = np.array([-1,1,-1,1])*scale)
    # ax.set_xticks(np.array([-100,-75,-50,-25,0,25,50,75,100])*scale/100)
    # ax.set_yticks(np.array([-100,-75,-50,-25,0,25,50,75,100])*scale/100)
    ax.grid()
    
def generate_weight_function(IorQ1_avg, IorQ2_avg, start, stop):
    wf = np.zeros(np.size(IorQ1_avg)) #or Q_c_avg, they should be the same
    wf[start:stop] = np.sqrt((IorQ1_avg-IorQ2_avg)**2)[start:stop]
    return wf

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

#generate histogram weight functions from average traces
I_wf = generate_weight_function(I_plus_avg, I_minus_avg, 50,150)
Q_wf = generate_weight_function(Q_plus_avg, Q_minus_avg, 50,150)

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

#plotting the weight functions
ax4 = fig.add_subplot(224)
ax4.set_title("Weight functions")
ax4.plot(I_wf, label = 'I weight func')
ax4.plot(Q_wf, label = 'Q_weight_func')
ax4.legend()
ax4.plot()

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

histfig = plt.figure()
ax21 = histfig.add_subplot(221)
ax21.set_aspect(1)
ax21.set_title("Plus waveform, weights off")
histogram(fig, ax21, 50, 150, I_plus.reshape((7500, 208)), Q_plus.reshape((7500, 208)), scale = 1000, boxcar = True)

ax22 = histfig.add_subplot(222)
ax22.set_title("Minus waveform, weights off")
ax22.set_aspect(1)
histogram(fig, ax22, 50, 150, I_minus.reshape((7500, 208)), Q_minus.reshape((7500, 208)), scale = 1000, boxcar = True)

ax23 = histfig.add_subplot(223)
ax23.set_aspect(1)
ax23.set_title("Both waveforms, weights off")
histogram(histfig, ax23, 50, 150, np.append(I_plus, I_minus).reshape((15000, 208)), np.append(Q_plus, Q_minus).reshape((15000, 208)), scale = 1000, boxcar = True)

ax24 = histfig.add_subplot(224)
ax24.set_aspect(1)
ax24.set_title("Both waveforms, weights on")
histogram(histfig, ax24, 50, 150, np.append(I_plus, I_minus).reshape((15000, 208)), np.append(Q_plus, Q_minus).reshape((15000, 208)), scale = 1000, I_weights = I_wf, Q_weights = Q_wf)
