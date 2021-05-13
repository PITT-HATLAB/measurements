# -*- coding: utf-8 -*-
"""
Created on Tue Jun 30 09:44:52 2020

@author: Ryan Kaufman and TZC
"""
import easygui
import matplotlib.pyplot as plt
import numpy as np
import h5py
import matplotlib.colors as color

#%%
#======  read a single datum  =======
try: 
    print(readname)
except:  
    readname = easygui.fileopenbox("Select the file you would like to read:") 
Data = h5py.File(readname, 'r') 
traces = Data['sweep_data'][()]
G_power = Data['G_power'][()]
C_power = Data['C_power'][()]
GC_G_powers = Data['C=G_G_powers']
GC_C_powers = Data['C=G_C_powers']
GC_traces = Data['C=G_traces']

#%%Show the colorplot on res

plt.close('all')
plt.figure(1)
colors = [color.hex2color('#0000FF'), color.hex2color('#FFFFFF'), color.hex2color('#FF0000')]        
_cmap = color.LinearSegmentedColormap.from_list('my_cmap', colors)
_norm = color.Normalize(vmin = -20, vmax = 20)
plt.pcolormesh(G_power, C_power, traces.T, cmap = _cmap, norm = _norm) 
plt.xlim([G_power[0], G_power[-1]])
plt.ylim([C_power[0],C_power[-1]])
plt.colorbar(label = 'Gain (dB)')
plt.gca().get_xaxis().get_major_formatter().set_useOffset(False)
plt.gca().get_yaxis().get_major_formatter().set_useOffset(False)
plt.xlabel('G power (dBm)')
plt.ylabel('C power (dBm)')
#%%
#this visualizes the values that are around a flat reflection, which should be GC balanced. 
#If the indices are greater than these indices, then we should change the SC frequency 
plt.figure(2)
comp_arr = np.isclose(traces, np.zeros(np.shape(traces)), atol = 1)
plt.pcolormesh(G_power, C_power, comp_arr.T)
#%%
#plot a fluxsweep-esque plot of the G = C traces at higher conversion power
colors = [color.hex2color('#0000FF'), color.hex2color('#FFFFFF'), color.hex2color('#FF0000')]        
_cmap = color.LinearSegmentedColormap.from_list('my_cmap', colors)
_norm = color.Normalize(vmin = -5, vmax = 5)
plt.pcolormesh(range(0,1601),GC_C_powers,GC_traces, cmap = _cmap, norm = _norm)
plt.colorbar(label = 'Reflection (dB)')
#%% Same thing for gain power
colors = [color.hex2color('#0000FF'), color.hex2color('#FFFFFF'), color.hex2color('#FF0000')]        
_cmap = color.LinearSegmentedColormap.from_list('my_cmap', colors)
_norm = color.Normalize(vmin = -5, vmax = 5)
plt.pcolormesh(range(0,1601),GC_G_powers,GC_traces, cmap = _cmap, norm = _norm)
plt.colorbar(label = 'Reflection (dB)')
#%%Look at individual traces
plt.plot(GC_traces[-5])