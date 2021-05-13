# -*- coding: utf-8 -*-
"""
Created on Mon Jul 24 19:45:51 2017

@authors: TZC and YR
"""



import numpy as np
import h5py
import matplotlib.pyplot as plt
import matplotlib.colors as color
from matplotlib.widgets import Slider
import easygui
import time
import os


#enter initial parameters (in the server this would be handled by the parameter manager) 
#set current working directory to a particular folder
# G_power = np.arange(0,16,0.4)
# C_power = np.arange(-10,5,0.6)
G_power = np.arange(0,16,0.2)
C_power = np.arange(-10,10,0.2)
name = 'Bias_2.034mA_very_fine_smoothing_on'
try: 
    print(cwd)
except: 
    cwd = easygui.diropenbox('Select where you are working:')
os.chdir(cwd)

#======  obtain data  =======
r_gain = np.zeros((len(G_power), len(C_power)))
t_gain = np.zeros((len(G_power), len(C_power)))
avg_num = 10

#get reflection off of A first
SWT.set_mode_dict('5_to_B')
#first its a good idea to normalize to nothing
SigGen.output_status(0)
QGen.output_status(0)

print('Normalizing...')
VNA.math('NORM') #makes sure theres no data/mem
VNA.average_restart() 
VNA.average(avg_num)
VNA.data_to_mem()
VNA.math('DIV')
print('Normalization Completed')
#now we are normalized and ready to go
SigGen.output_status(1)
QGen.output_status(1)
C_equals_G_C_powers = []
C_equals_G_G_powers = []
C_equals_G_traces = []
for x in range(len(G_power)):    
    for y in range(len(C_power)):
        
        SigGen.power(C_power[y])
        QGen.power(G_power[x])
        
        print ("G_power : "+str(G_power[x])+"dBm and C_power : "+str(C_power[y])+"dBm")
        
        VNA.average_restart()
        trace = VNA.average(avg_num)[0]
        r_gain[x,y] = np.average(VNA.average(avg_num)[0])
        
        if np.isclose(r_gain[x,y],0,atol = 1): 
            print('C = G, taking extended trace...')
            C_equals_G_C_powers.append(C_power[y])
            C_equals_G_G_powers.append(G_power[x])
            VNA.math('NORM')
            VNA.fspan(100e6)
            VNA.average_restart()
            f_data = VNA.getfdata()
            eq_trace = VNA.average(avg_num)[0]
            C_equals_G_traces.append(eq_trace)
            VNA.fspan(0)
            VNA.math('NORM')
        
        
SigGen.output_status(0)
QGen.output_status(0)    

#======  save data  =======        
        
filename = name+'_ref'

Data = h5py.File(filename, 'w') 
Data.create_dataset('freqs', data = f_data)
Data.create_dataset('c_pump_freq', data = SigGen.frequency())
Data.create_dataset('g_pump_freq', data = QGen.frequency())
Data.create_dataset('sweep_data', data = r_gain)
Data.create_dataset('G_power', data = G_power)
Data.create_dataset('C_power', data = C_power)
Data.create_dataset('C=G_G_powers', data = np.array(C_equals_G_G_powers))
Data.create_dataset('C=G_C_powers', data = np.array(C_equals_G_C_powers))
Data.create_dataset('C=G_traces', data = np.array(C_equals_G_traces))

Data.close()



# Get transmission data (we want to use the transmission  SWT mode): 
print("Beginning transmission sweep...")
SWT.set_mode_dict('5_to_A_trans')

t_gain = np.zeros((len(G_power), len(C_power)))

#normalize to full conversion, which by my rough calibration is about 1dBm on SigGen at this frequency
SigGen.output_status(1)
QGen.output_status(0)

SigGen.power(1)
print('Normalizing...')
VNA.math('NORM') #makes sure theres no data/mem
VNA.average_restart() 
VNA.average(avg_num)
VNA.data_to_mem()
VNA.math('DIV')
print('Normalizing Completed')
QGen.output_status(1)
SigGen.output_status(1)

for x in range(len(G_power)):    
    for y in range(len(C_power)):   
        if r_gain[x,y] < 0: #would indicate conversion
            SigCore5.frequency(int(SigGen.frequency()))
        else: 
            SigCore5.frequency(int(QGen.frequency()))
            
        SigGen.power(C_power[y])
        QGen.power(G_power[x])
        
        print ("G_power : "+str(G_power[x])+"dBm and C_power : "+str(C_power[y])+"dBm")
        VNA.average_restart()
        t_gain[x,y] = np.average(VNA.average(avg_num)[0])
        
SigGen.output_status(0)
QGen.output_status(0)
#======  save data  =======        
        
filename = name+'_trans'   

Data = h5py.File(filename, 'w')
Data.create_dataset('c_pump_freq', data = SigGen.frequency())
Data.create_dataset('g_pump_freq', data = QGen.frequency())
Data.create_dataset('sweep_data', data = t_gain)
Data.create_dataset('G_power', data = G_power)
Data.create_dataset('C_power', data = C_power)
Data.close()

SigGen.output_status(0)
QGen.output_status(0)

