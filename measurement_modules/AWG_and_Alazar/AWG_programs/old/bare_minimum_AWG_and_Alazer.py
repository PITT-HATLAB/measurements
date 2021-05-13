# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 14:42:02 2020

@author: HatLab_Xi Cao then Ryan Kaufman

RRK: the idea here is to simplify the old code as much as possible to make it 
understandable from first principles

send a pulse straight into the alazar and look at the result in time domain in python. That's it.

"""

# Basic qubit measurement

# take data when there is multiple sequence
import numpy as np
import time
import matplotlib.pyplot as plt
import h5py
from hatdrivers.alazar_utilities import atsapinew as ats
import hatdrivers.AlazarTech_ATS9870_old_copy as Alazar
# import fit_all as FA

def get_data(measurement_parameters, weight_function, use_AWG, AWG, AWG2, demodulation = False):
    
    # Record data form board
    board = ats.Board(systemId = 1, boardId = 1)
    Alazar.ConfigureBoard(board)
    
    t1 = time.time()
    (I_data, Q_data) = Alazar.AcquireData(board, measurement_parameters, weight_function, use_AWG=use_AWG, AWG=AWG, AWG2=AWG)
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
    
    num_sequences = 100
    
    measurement_parameters = {'t_avg': 20,  # do not change if you do not know what is this
                              'points_per_record': 1600,#24000,  # how many points you want to take in one record
                              'num_records': 2, # how many records you want to take in total
                              'num_sequences': 1, # how many different measurement sequences
                              'record_average': False # decide if you want to do average of different record
                              #at the moment, averaging here does NOT work
                              }

    weight_function = {'use_weight_function': False,  # decide if you need to use a weight function
                       'filename': r'H:\Data\Fridge Texas\Cooldown_20180812\20180817\Interferometric readout\qubit\cavity reponse\\weight_function_at_7.5506GHz_JPC54_off_JPC55_on', # your weight funciton file
                       'demode_window_length': 200, # how long do you want to use your weight function make sure you have enough points in your weight function file
                       'demode_window_start': np.array([0]) # where does each demode window starts
                       }
    

    use_AWG = True
    AWG = AWG
    AWG2 = None
    
    # SC4 = qt.instruments['SC4']
    
    tempI = np.zeros(num_sequences)
    tempQ = np.zeros(num_sequences)
    filenum = 1
    demodulation = False
    for i in range(filenum):
        I_data, Q_data = get_data(measurement_parameters, weight_function, use_AWG, AWG, AWG2)
    
        msmt_time = 20*np.arange(np.size(I_data))
    
        if measurement_parameters['record_average']:
            testI = np.mean(I_data[:, 20:140], axis=1)
            testQ = np.mean(Q_data[:, 20:140], axis=1)
            
            tempI += testI
            tempQ += testQ
    
            testI = tempI/filenum
            testQ = tempQ/filenum
            
            plt.figure()
            plt.title('I(t)')
            plt.plot(testI)
            plt.figure()
            plt.title('Q(t)')
            plt.plot(testQ)
            
        if not measurement_parameters['record_average']:
            plt.figure()
            plt.imshow(I_data, aspect = 'auto')
            plt.title('I_data')
            plt.colorbar()
            print(np.size(I_data))
            print(np.shape(Q_data))
            plt.figure()
            plt.title('Q_data')
            plt.imshow(Q_data, aspect = 'auto')
            plt.colorbar()
            plt.figure()
            plt.title("I averaged over records")
            plt.plot(np.average(I_data, axis = 0))
            plt.figure()
            plt.title("Q averaged over records")
            plt.plot(np.average(Q_data, axis = 0))
            plt.figure()
            plt.title("Magnitude Averaged over records")
            plt.plot(np.sqrt(np.average(Q_data, axis = 0)**2+np.average(I_data, axis = 0)**2))
                
                # plt.figure()
                # plt.imshow(ref_I, aspect = 'auto')
                # plt.title('ref_I_data')
                # plt.colorbar()
                # plt.figure()
                # plt.title('ref_Q_data')
                # plt.imshow(ref_Q, aspect = 'auto')
                # plt.colorbar()
                
            # if not demodulation: 
            #     plt.figure()
            #     plt.imshow(I_data, aspect = 'auto')
            #     plt.title('Ch1_data')
            #     plt.colorbar()
            #     plt.figure()
            #     plt.title('Ch2_data')
            #     plt.imshow(ref_I, aspect = 'auto')
            #     plt.colorbar()
            #     plt.figure()
            #     plt.title("Ch1 data averaged over records")
            #     plt.plot(np.average(I_data, axis = 0))
            #     plt.figure()
            #     plt.title("Ch2 data averaged over records")
            #     plt.plot(np.average(ref_I, axis = 0))
            
            
    # # attempt manual demodulation
    # #create 2d array to multiply data by
    
    # t_arr = np.arange(np.size(I_data[1])) #gets size of data
    # SinArr = np.sin(2*np.pi/20*t_arr)
    # CosArr = np.cos(2*np.pi/20*t_arr) #demod arrays on the assumption that one point is 20ns, and 20pts is the period (so 50MHz is the frequency) 
    # # Ref_mag = np.sqrt(ref_I**2 + ref_Q**2)
    # # demod_I = (I_data*ref_I + Q_data*ref_Q)/Ref_mag
    # # demod_Q = (I_data*ref_Q + Q_data*ref_I)/Ref_mag  
    
    # demod_I = (I_data*SinArr)
    # demod_Q = (I_data*CosArr)
    
    # #the I and Q data are actually the exact same before the demodulation, before that its just voltage vs time
    
    # plt.figure()
    # plt.title('Demodulated: I_data')
    # plt.imshow(demod_I)
    # plt.colorbar()
    
    # plt.figure()
    # plt.title('Demodulated: Q_data')
    # plt.imshow(demod_Q)
    # plt.colorbar()
    
    
    
    
    # savedata = False
    # path = r'C:\Users\Hatlab_3'
    # if savedata:         
    #         name = 'TEST'
    #         datafile = h5py.File(path+name, 'w-')
    #         datafile.create_dataset('I_data', data=testI)
    #         datafile.create_dataset('Q_data', data=testQ)
    #         datafile.create_dataset('x_data', data=xdata)
    #         datafile.close()
            