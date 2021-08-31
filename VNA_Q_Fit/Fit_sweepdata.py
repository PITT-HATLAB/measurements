# -*- coding: utf-8 -*-
"""
Created on Wed Jul 27 15:09:04 2016

@author: HatLab_Xi Cao
"""

# Try to fit from the real data on experiment



# import fluxplot 

# Plot = fluxplot.FluxSweepPlot()

# Plot.load_data_from_file(r'C:\Users\HatLab_Xi Cao\Box Sync\Data\Cooldown_2016_07_27\S_param\signal_sweep_7_27_2016_11_47')

# Plot.plot_data()

# test = Plot.get_data_point()


import h5py 
import Q_fit
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
# import easygui
from plottr.data import datadict_storage as dds, datadict as dd
from plottr.data.datadict_storage import all_datadicts_from_hdf5



#Data = h5py.File(r'C:\\Users\\HatLab_Xi Cao\\Box Sync\\Data\\Cooldown_2016_01_20\\2016_01_21\\01_measTZCcav_ S11_100avg.hdf5','r')
#Data.items()
#Sweep = Data.get('S21 set').value
#Freq = Data.get('freqvalues').value[0]
##Currents = Data.get('currents').value
##Freq = Data.get('measure_frequencies').value
##Sweep = Data.get('sweep_data').value
#Data.close()

#Data = h5py.File('C:\Users\HatLab_Xi Cao\Box Sync\Data\\Cooldown_2016_08_22\\JPC_0014\\Flux Sweep\\idler_sweep_forward_Sii_8_24_2016_17_29','r')
#Sweep = Data['sweep_data'].value
#Freq = Data['measure_frequencies'].value
#Data.close()

#Background_Mag = 10**(Sweep[36,0,:]/20.0)
#Background_Phase = Sweep[36,1,:]*np.pi/180.0

#Fitting_data_Mag = 10**((Sweep[581,0,:])/20.0)
#Fitting_data_Phase = (Sweep[581,1,:])*np.pi/180.0

#filename = 'C:\\Users\\HatLab_Xi Cao\\Box Sync\\Data\\Cooldown_2016_08_26\\2016_08_29\\Qubit_cavity\\02_Cooldown_Sstw_first_peak'

#filename = 'C:\\Users\\HatLab_Xi Cao\\Box Sync\\Data\\Cooldown_2016_08_13\\Resonator\\Resonator_Al_Span_50MHz'
##Data = h5py.File('C:\\Users\\HatLab_Xi Cao\\Box Sync\\Data\\Cooldown_2016_08_26\\2016_09_19\\JPC0014\\resonant sweep\\signal_sweep_current_0.996mA_01.hdf5','r')
#Data = h5py.File(filename, 'r')
#Sweep = Data['S21 set'].value
#Freq = Data['freqvalues'].value[0]
#Data.close()


#filename = 'C:\\Users\\HatLab_Xi Cao\\Box Sync\\Data\\Cooldown_2016_08_26\\2016_08_29\\JPC_0014\\Flux Sweep\\Signal_sweep_forward_Sss_FineSteps_8_29_2016_13_51'
#Data = h5py.File(filename, 'r')
#Currents =Data['currents'].value[298]
#Sweep = Data['sweep_data'].value[298,:,:]
#Freq = Data['measure_frequencies'].value
#Data.close()

#filename = 'C:\\Users\\HatLab_Xi Cao\\Box Sync\\Data\\Olivia_cable\\Test_cable02_2016_11_03.hdf5'
#Data = h5py.File(filename, 'r')
#Sweep = Data['S11 set'].value
#Freq = Data['freqvalues'].value[0]
#Data.close()

#filename = 'C:\\Users\\HatLab_Xi Cao\\Box Sync\\Data\\Cooldown_2016_11_18\\2016_11_18\\JPC0019\\Flux_sweep\\S_ss_1.0mA'

def getData_from_datadict(filepath, plot_data = None): 
    datadict = all_datadicts_from_hdf5(filepath)['data']
    powers_dB = datadict.extract('power')['power']['values']
    freqs = datadict.extract('power')['frequency']['values']*2*np.pi
    phase_rad = datadict.extract('phase')['phase']['values']
    
    lin = np.power(10, powers_dB/20)
    real = lin*np.cos(phase_rad)
    imag = lin*np.sin(phase_rad)
    
    print(np.size(phase_rad))
    print(np.size(phase_rad))
    
    if plot_data:
        plt.figure('mag')
        plt.plot(freqs, powers_dB)
        plt.figure('phase')
        plt.plot(freqs, phase_rad)
        
    return (freqs, real, imag, powers_dB, phase_rad)


filepath = r'\\136.142.53.51\data001\Data\HuntCollab2\hBN_cap\20210823_cooldown\2021-08-23\2021-08-23_0001_10_432_ghz_reso\2021-08-23_0001_10_432_ghz_reso.ddh5'
# Data = h5py.File(filename, 'r')

(freq, real, imag, mag, phase) = getData_from_datadict(filepath, plot_data=0)
ltrim = 200
rtrim = 200
freq = freq[ltrim:-rtrim]
real = real[ltrim:-rtrim]
imag = imag[ltrim:-rtrim]
mag = mag[ltrim:-rtrim]
phase = phase[ltrim:-rtrim]

# Sweep = Data['S21'].value
# Freq = Data['Freq'].value
# Data.close()  
#print Currents
# Fitting_data_Mag = 10**((mag)/20.0)
# Fitting_data_Phase = (phase)*np.pi/180.0

#B_real = Background_Mag*np.cos(Background_Phase)
#B_imag = Background_Phase*np.sin(Background_Phase)
# Fitting_data_real = Fitting_data_Mag*np.cos(Fitting_data_Phase) 
# Fitting_data_imag = Fitting_data_Mag*np.sin(Fitting_data_Phase) 

#Fitting_Params = {'Q_ext': 20000, 'Q_int': 10000, 'A': 3.6681889378123505e-10, 'B': -19.966263980082346, 'E': -1.0370950026119112e-09, 'D': 47}
Fitting_Params = {'Q_ext': 1000.0, 'Q_int':1000.0 , 'A': 0.0, 'B': 0.0, 'E': 0.0, 'D': 0}
#plt.plot(Freq, Fitting_data_real)
#result = Q_fit.fit(Freq,Fitting_data_real,Fitting_data_imag, Fitting_Params, plot = True, Method = 1)
result = Q_fit.fit(freq, real, imag, plot = True, method = 1)
