# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 14:42:02 2020

@author: HatLab_Xi Cao
"""

# Basic qubit measurement

# take data when there is multiple sequence

import numpy as np
import time
import matplotlib.pyplot as plt
import h5py
from hatdrivers.alazar_utilities import atsapinew as ats
from hatdrivers import AlazarTech_ATS9870 as Alazar
#from optimize_measurement_parameters import data_rotate, get_IQ_pair
# import sys
# sys.path.append(r'E:\HatLabCode\HatCode\Qubit\PXIe\SeriousCode\\')
# import fit_all as FA


def get_data(measurement_parameters, weight_function, use_AWG, AWG, AWG2):
    
    # Record data form board
    board = ats.Board(systemId = 1, boardId = 1)
    Alazar.ConfigureBoard(board)
    
    t1 = time.time()
    (I_data, Q_data) = Alazar.AcquireData(board, measurement_parameters, weight_function, use_AWG=use_AWG, AWG=AWG, AWG2= AWG2)
    t2 = time.time()

    print('It takes ' + str(t2 - t1) + ' seconds.')
    
    return (I_data, Q_data)

def save_data(filename, I_data, Q_data):
    Data = h5py.File(filename, 'w-')
    Data.create_dataset('I_data', data = I_data)
    Data.create_dataset('Q_data', data = Q_data)
    Data.close()

def plot_data(index, I_data, Q_data):
#    plt.close('all')    
    plt.figure(1)
    plt.plot(I_data[index, :])
    plt.plot(Q_data[index, :])
    plt.xlabel('points (1 pt  = 20 ns)')
    plt.ylabel('I/Q')
    plt.legend(['I', 'Q'])


    plt.figure(2)
    xlim = np.max(np.abs(I_data[index, :]))
    ylim = np.max(np.abs(Q_data[index, :]))
    lim = 1.1*np.max((xlim, ylim)) 
    plt.plot(I_data[index, :], Q_data[index, :], '*-')
    plt.xlabel('I')
    plt.ylabel('Q')
    plt.xlim([-lim, lim])
    plt.ylim([-lim, lim])
   

if __name__ == "__main__":    
    msmt_name = 'pi_pulse'
    savedata = True
    
    if msmt_name == 'pi_pulse':
        num_sequences = 81
    elif msmt_name == 'T1':
        num_sequences = 41
    elif msmt_name == 'allXY':
        num_sequences = 42
    elif msmt_name == 'T2_R':
        num_sequences = 201
    elif msmt_name == 'T2_E':
        num_sequences = 201
        
    num_sequences = 1#1
    
    
    
    
    measurement_parameters = {'t_avg': 20,  # do not change if you do not know what is this
                              'points_per_record': 4800,#24000,  # how many points you want to take in one record
                              'num_records': 80000, # how many records you want to take in total
                              'num_sequences': num_sequences, # how many different measurement sequencesG
                              'record_average': True # decide if you want to do average of different record
                              } 

    weight_function = {'use_weight_function': False,  # decide if you need to use a weight function
                       'filename': r'H:\Data\Fridge Texas\Cooldown_20180812\20180817\Interferometric readout\qubit\cavity reponse\\weight_function_at_7.5506GHz_JPC54_off_JPC55_on', # your weight funciton file
                       'demode_window_length': 150, # how long do you want to use your weight function make sure you have enough points in your weight function file
                       'demode_window_start': np.array([0, 160]) # where does each demode window starts
                       }

    use_AWG = True # if do not use AWG, then we can run the code in the spyder. Hopefully we do not need this with the new "qtlab in spyder" project
#    reload(Alazar)

#    plt.close('all')
    # import qt
    import gc
    gc.collect()
    # AWG = qt.instruments['AWG']
    # AWG2 = qt.instruments['AWG2']
#    summation_pump_generator = qt.instruments['BatGen']
#    summation_pump_generator.set_output_status(0)    
#    AWG.stop()

#    ## inside the loop    
##    pump_amps= np.linspace(2.0, 4.5, 6) #for ge summation pump
##    pump_amps = np.linspace(0.5, 3.5, 7) for upper left quad
##    pump_amps = np.linspace(0.5, 1.5, 3)
###    pump_frequencies = np.linspace(15e6, 20e6, 11) + 11.26223e9 #for ge suummation pump 
##    pump_frequencies = np.linspace(-10e6, 0e6, 21) + 11.26223e9    
#    pump_amps= np.linspace(1.5, 4.5, 7) #for ge summation pump
##    pump_frequencies = np.linspace(5e6, 10e6, 11) + 11.26223e9 #for ge suummation pump
#    pump_frequencies = np.linspace(0e6, 20e6, 41) + 11.26223e9 #for ge suummation pump
#    avg = 1    
#    xdata= np.linspace(0, 74750, 300) + 50
#    for i in range(len(pump_amps)):    
#        AWG2.set_ch3amp(pump_amps[i])
#        AWG2.set_ch4amp(pump_amps[i])
#        for j in range(len(pump_frequencies)):
#            summation_pump_generator.set_frequency(pump_frequencies[j])        
#            (I_data, Q_data) = get_data(measurement_parameters, weight_function, use_AWG, AWG, AWG2)
#            if measurement_parameters['record_average']:
#                testI = np.mean(I_data, axis=1)
#                testQ = np.mean(Q_data, axis=1)
#                
#            for k in range(avg):
#                path = r'M:\Data\Fridge Cool Runnings\Cooldown_20200121\MAser\20200217\ge_difference_pump_frequency_3.5613725GHz\\'
##                name = '02_init_g_ge_summation_DAC_7000_pump_power_' + str(pump_amps[i]) + '_pump_frequency_' + str(pump_frequencies[j]) + '_avg_' + str(k)
#                name = 'ge_pi_poulse_tuneup_2'
#                datafile = h5py.File(path+name, 'w-')
#                datafile.create_dataset('I_data', data=testI)
#                datafile.create_dataset('Q_data', data=testQ)
#                datafile.create_dataset('x_data', data=xdata)
#                datafile.close()
#    ##    
###    
#    print (SC2.get_output_status())
#    freq = 6.97277e9
#    detune = 0.0e6
#    SC1.set_frequency(freq+detune)
#    SC0.set_frequency(freq+detune-50e6)
    (I_data, Q_data) = get_data(measurement_parameters, weight_function, use_AWG, AWG, None)
#    testI = np.mean(I_data, axis=1) 
#    testQ = np.mean(Q_data, axis=1)   
#
##    plt.plot(I_data[0])
##    plt.plot(Q_data[0])
#    plt.figure()
#    plt.hist2d(testI, testQ, bins=101, range=[[-20, 20], [-20, 20]])
#    plt.colorbar()

#    testI1 = np.mean(I_data[:, 0:200], axis=1)
#    testQ1 = np.mean(Q_data[:, 0:200], axis=1)
#
#    testI2 = np.mean(I_data[:, 210::], axis=1)
#    testQ2 = np.mean(Q_data[:, 210::], axis=1)
#    
#    plt.figure()
#    plt.hist2d(testI1, testQ1, bins=101, range=[[-30, 30], [-30, 30]])
#    plt.colorbar()
#
#    
#    plt.figure()
#    plt.hist2d(testI2, testQ2, bins=101, range=[[-30, 30], [-30, 30]])
#    plt.colorbar()

    
#    plt.figure()
#    plt.plot(I_data[0])
#    plt.plot(Q_data[0])

#    plt.figure()
#    plt.plot(I_data[0], Q_data[0])
#    msmt_time = 20*np.arange(np.size(I_data))

#%%

    if measurement_parameters['record_average']:
        testI = np.mean(I_data, axis=1)
        testQ = np.mean(Q_data, axis=1)


    if msmt_name == 'pi_pulse':

        gaussian_num = 81
        xdata = np.linspace(-7000, 7000, gaussian_num) 
        FA.pi_pulse_tune_up(testI, testQ, xdata)
    elif msmt_name == 'T1':
#        pass
        xdata = np.linspace(0, 120000, 41) #+ 50
        FA.t1_fit(testI, testQ, xdata/1e3)
        
    elif msmt_name == 'allXY':
        xdata = np.linspace(1, 42, 42)
        FA.allxy(testI, testQ, xdata)
#            
    elif msmt_name == 'T2_R':
        xdata = np.linspace(1, 32, 201)
        FA.t2_ramsey_fit(testI, testQ, xdata)
        
    elif msmt_name == 'T2_E':
        xdata = np.linspace(1, 32, 201)
        FA.t2_echo_fit(testI, testQ, xdata)
            
        
        
#        
#    plt.figure()
#    plt.plot(testI)
#    plt.plot(testQ)
#    pump_amp = 1.0
#    AWG2.set_ch1amp(pump_amp)
#    AWG2.set_ch2amp(pump_amp)
    
#    freq = np.linspace(-60e6, -41e6, 20) + 4.4262307e9+3e6+212e6
#    freq = np.linspace(-20e6, 20e6, 41) + 11.143999e9
    
#    for j in range(len(freq)):
#        sum_freq = freq[j]#4.4262307e9+3e6+212e6
#        SC4.set_frequency(sum_freq)
    
    
#    
#    for i in range(5):
#        (I_data, Q_data) = get_data(measurement_parameters, weight_function, use_AWG, AWG, AWG2)
#        testI = np.mean(I_data, axis=1)
#        testQ = np.mean(Q_data, axis=1)
#        path = r'M:\Data\Fridge Cool Runnings\Cooddown_20200610\Chemical Potential\20200615\Qubit_msmt\Pulsed_Spectroscopy\\'
#        if savedata:
##            name = '001_init_e_summation_pump_on_DAC1000_2.0V_'+str(sum_freq)+'GHz_'+ str(i)
##                    name = '001_init_e_summation_pump_on_DAC1000_2.0V_'+ str(i)
#            name = '001_pi_pulse_' + str(i)
#            datafile = h5py.File(path+name, 'w-')
#            datafile.create_dataset('I_data', data=I_data)
#            datafile.create_dataset('Q_data', data=Q_data)
##            datafile.create_dataset('x_data', data=xdata)
#            datafile.close()
#        #    summation_pump_generator.set_output_status(0)            
#               
#            
            
        
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            