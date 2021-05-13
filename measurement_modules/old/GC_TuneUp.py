# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 11:18:18 2020

@author: Ryan Kaufman

This file is an attempt to systemize the tuneup of GC at a given bias point

Assumptions: instruments have been separately initialized. 
"""
#%%Step 0: import dependencies and set cwd, device name, all that good stuff!
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as color
#E:\HatCode\Fitting_code\Q_cal\Q_fit.py

#because we dont yet install our modules from a repo package, you need to import by first adding the location of Q_fit.py to the System PATH, then importing it. Yes, it's janky. -YR
import sys
import os
sys.path.insert(0,r"E:\HatCode\Fitting_code\Q_cal")
import Q_fit as Qf
sys.path.insert(0, r'C:\Users\Hatlab_3\Desktop\RK Scripts\Measurement_Scripts')
cwd = r'H:\Data\Fridge Texas\Cooldown_20200607\SHARC23\20200623'
dev_name = 'SHARC23'
from datetime import date
import time
import h5py
#%% Mode Details: 
modea_settings = {'power': -75, 'fcenter': 5511822974, 'fspan': 200000000.0, 'electrical_delay': 8.2e-08, 'phase_offset': 90.0}
modec_settings = {'fcenter': 8527717435, 'fspan': 1000000000.0, 'electrical_delay': 7.5e-08, 'power': -60.0, 'phase_offset': -50.0}
conv_pump = modec_settings['fcenter']-modea_settings['fcenter']
gain_pump = modec_settings['fcenter']+modea_settings['fcenter']

#%%Step one: acquire mode frequencies, set pumps, get best trace for each (highest peak (or 20dB) for gain, lowest dip (-20dB) for conversion)

#Starting point: pumps off and mode centered in middle of VNA trace in reflection. 

def get_mode(cwd, device_name, mode_name, averages = None): 
    '''
    takes in a VNA trace (manually set dip point to center)
    with an estimate to Q_int vs. Q_ext and fit to the data
    
    inputs: CENTERED VNA trace (array), Q_int guess (float), Q_ext guess (float)
    
    outputs(explicit): mode-> dict("res": fcenter(GHz),"kap":(MHz))
    
    outputs(implicit): plot of fits, saves trace
    
    '''
    savedir = cwd
    #Get the trace and save it to a file, where the Q_fit module will pick up after it
    power = VNA.get_power()
    VNA.set_trform('PLOG')
    VNA.set_trigger_source('BUS')
    freqs = VNA.getfdata()
    S21 = VNA.gettrace()
    phase = S21[1, :]
    pwr = S21[0,: ]
    #resetting
    VNA.set_trform('PHAS')
    VNA.set_trigger_source('INT')
    
    fcenter = VNA.get_fcenter()
    
    name = '{mode_name}_Ref_{center:.3f}GHz_{power:.2f}dBm.hdf5'.format(date = str(date.today()),device_name = device_name,mode_name = mode_name, center = VNA.get_fcenter()/1e9, power = VNA.get_power())
    #Check if path exists: 
    if os.path.exists(savedir): 
        pass
    else: 
        os.mkdir(savedir)
    
    os.chdir(savedir)
    
    with h5py.File(name, 'w') as f: 
        f['Freq'] = freqs
        f['S21'] = S21
        f.close()
    return savedir+'\\'+name, fcenter
#%% test
        mode_path = get_mode(cwd+r'\modes', dev_name, 'Aref')

#%%
    
def sweep_conv_pump(cwd, device_name, sweep_name, modea_freq, modeb_freq, conv_power_arr, Generator): 
    '''
    takes in two mode frequencies, sets to conversion frequency and sets power in steps
    
    inputs: (modea_freq, modeb_freq), (conv_power_arr)
    
    outputs: plot of highest peak/lowest dip wrt to frequency for arrays of pump powers
    '''
    #set conversion frequency: 
    conv_freq = np.abs(modea_freq-modeb_freq)
    Generator.set_frequency(conv_freq)
    Generator.set_output_status(1)
    
    #perform the sweep, grab all the traces and save them individually
    for power in conv_power_arr: 
        Generator.set_power(power)
        time.sleep(2)
        get_mode(cwd, device_name+'_{cpower}'.format(cpower = power), "Aref")
        
def compile_traces(cwd, device_name, sweep_name, conv_power_arr): 
    #Check if path exists: 
    if os.path.exists(cwd): 
        pass
    else: 
        os.mkdir(cwd)
    
    os.chdir(cwd)    
    #go back through the files and collect all the data
    freqs = []
    sweep_data = []
    for filename in os.listdir(cwd): 
        with h5py.File(filename, 'r') as f: 
            if freqs == []:             
                freqs = np.array(f['Freq'])
            print(f.keys())
            S21 = np.array(f['S21'])
            sweep_data.append(S21)
            f.close()
    
    #write one big file that has it all: 
    filename = 'COMPILED_{device_name}_{sweep_name}.hdf5'.format(device_name = device_name, sweep_name = sweep_name)
    with h5py.File(cwd+'\\'+filename, 'w') as f: 
        f['S21_data'] = np.array(sweep_data)
        f['powers'] = np.array(conv_power_arr)
        f['freqs'] = np.array(freqs)
        f.close()
#%% test
#modea_settings and mode_b_settings are acquired by using VNA.get_bundle and VNA.set_bundle
powers = np.arange(-20,6,1)
detuning = 0
sweep_name = '{detuning}MHz_detuning_A_Ref_Conv'.format(detuning = detuning)
savepath = cwd+'\\{detuning}MHz'.format(detuning = detuning)
sweep_conv_pump(savepath, dev_name, sweep_name, modea_settings['fcenter'],modec_settings['fcenter']+detuning, powers, SigGen)

#%%
compile_traces(savepath, dev_name, sweep_name, powers)

    
#%%Plot function
def plot_sweep(filepath): 
    with h5py.File(filepath, 'r') as f: 
        #print(f.keys())
        sweep_data = f['S21_data'][()]
        powers = f['powers'][()]
        freqs = f['freqs'][()]      
        f.close()
        
    colors = [color.hex2color('#FF0000'), color.hex2color('#FFFFFF'), color.hex2color('#0000FF')]        
    _cmap = color.LinearSegmentedColormap.from_list('my_cmap', colors)
    _norm = color.Normalize(vmin = -20, vmax =5)
    plt.pcolormesh(np.array(powers), freqs, sweep_data[:,0,:].T, cmap = _cmap, norm = _norm)
    plt.colorbar(label = 'Mag (dB)')
    plt.gca().get_xaxis().get_major_formatter().set_useOffset(False)
    plt.gca().get_yaxis().get_major_formatter().set_useOffset(False)
    plt.xlabel('Power (dBm)')
    plt.ylabel('frequency (GHz)')
    
#%%
plot_sweep(r'H:\Data\Fridge Texas\Cooldown_20200607\SHARC23\20200623\2020-06-23_SHARC23_-20MHz_detuning_A_Ref_Conv.hdf5')
    
#%%Step two: both pumps at once