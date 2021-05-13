# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 17:41:39 2021

@author: Hatlab_3
"""
import numpy as np
import matplotlib.pyplot as plt
import qcodes.instrument_drivers.AlazarTech.ATS9870 as ATSdriver

from hatdrivers.alazar_utilities.controller.ATSChannelController import ATSChannelController
from hatdrivers.alazar_utilities.controller.alazar_channel import AlazarChannel
#import qcodes.instrument_drivers.AlazarTech.acq_helpers as helpers
import logging
logging.basicConfig(level=logging.INFO)
from qcodes.utils.dataset.doNd import do0d

datapath = r'E:\Data\Testing'

#%%
# Create the ATS9360 instrument
alazar = ATSdriver.AlazarTech_ATS9870(name='Alazar')
#%%
# Print all information about this Alazar card
print(alazar.get_idn())
#%%
with alazar.syncing():    
    alazar.clock_source('EXTERNAL_CLOCK_10MHz_REF')
    alazar.decimation(1)
    alazar.coupling1('AC')
    alazar.coupling2('AC')
    alazar.channel_range1(0.4)
    alazar.channel_range2(0.4)
    alazar.impedance1(50)
    alazar.impedance2(50)
    alazar.trigger_operation('TRIG_ENGINE_OP_J')
    alazar.trigger_engine1('TRIG_ENGINE_J')
    alazar.trigger_source1('EXTERNAL')
    alazar.trigger_slope1('TRIG_SLOPE_POSITIVE')
    alazar.trigger_level1(160)
    alazar.trigger_engine2('TRIG_ENGINE_K')
    alazar.trigger_source2('DISABLE')
    alazar.trigger_slope2('TRIG_SLOPE_POSITIVE')
    alazar.trigger_level2(128)
    alazar.external_trigger_coupling('DC')
    alazar.external_trigger_range('ETR_1V')
    alazar.trigger_delay(0)
    alazar.timeout_ticks(0)
    alazar.aux_io_mode('AUX_IN_AUXILIARY') # AUX_IN_TRIGGER_ENABLE for seq mode on
    alazar.aux_io_param('NONE') # TRIG_SLOPE_POSITIVE for seq mode on
    #%%
# Create the acquisition controller which will take care of the data handling and tell it which 
# alazar instrument to talk to. Explicitly pass the default options to the Alazar.
# Dont integrate over samples but avarage over records
myctrl = ATSChannelController(name='my_controller', alazar_name='Alazar')
#%%
myctrl.int_delay(50e-7)
myctrl.int_time(1e-7)
print(myctrl.samples_per_record())
avg_num = 10000
chan1 = AlazarChannel(myctrl, 'ChanA', demod=False, integrate_samples=False)
chan1.num_averages(avg_num)
chan1.alazar_channel('A')
chan1.prepare_channel()
chan2 = AlazarChannel(myctrl, 'ChanB', demod=False, integrate_samples=False)
chan2.num_averages(avg_num)
chan2.alazar_channel('B')
chan2.prepare_channel()

myctrl.channels.append(chan1)
myctrl.channels.append(chan2)

#%%
# Measure this 
data = myctrl.channels.data()
print(np.shape(data))
fig = plt.figure()
ax1 = fig.add_subplot(211)
ax1.plot(data[0],'-')
ax2 = fig.add_subplot(212) 
ax2.plot(data[1])
#%%
def demod(signal_data, reference_data, mod_freq = 50e6, sampling_rate = 1e9): 
    #first demodulate both channels
    point_number = np.arange(np.size(signal_data))
    period = int(sampling_rate/mod_freq)
    print('Modulation period: ', period)
    SinArray = np.sin(2*np.pi/period*point_number)
    CosArray = np.cos(2*np.pi/period*point_number)
    sig_I = signal_data*SinArray
    sig_Q = signal_data*CosArray
    ref_I = reference_data*SinArray
    ref_Q = reference_data*CosArray
    
    #now you cut the array up into periods of the sin and cosine modulation, then sum within one period
    #the sqrt 2 is the RMS value of sin and cosine squared, period is to get rid of units of time
    
    sig_I_summed = np.sum(sig_I.reshape(np.size(sig_I)//period, period), axis = 1)*(np.sqrt(2)/period)
    sig_Q_summed = np.sum(sig_Q.reshape(np.size(sig_I)//period, period), axis = 1)*(np.sqrt(2)/period)
    ref_I_summed = np.sum(ref_I.reshape(np.size(sig_I)//period, period), axis = 1)*(np.sqrt(2)/period)
    ref_Q_summed = np.sum(ref_Q.reshape(np.size(sig_I)//period, period), axis = 1)*(np.sqrt(2)/period)
    
    return (sig_I_summed, sig_Q_summed, ref_I_summed, ref_Q_summed)

sI,sQ, rI, rQ = demod(data[0], data[1])
plt.figure()
plt.plot(sI, label = "Signal I")
plt.plot(sQ, label = "Signal Q")
plt.plot(sI**2+sQ**2, label = "Signal Mag")
plt.legend()
plt.figure()
plt.plot(rI, label = "Reference I")
plt.plot(rQ, label = "Reference Q")
plt.plot(np.power(rI, 2)+np.power(rQ, 2), label = "reference Mag")
plt.legend()

#%% Adding Phase correction
def phase_correction(sigI, sigQ, refI, refQ): 
    Ref_mag = np.sqrt(refI**2 + refQ**2)
    sigI_corrected = (sigI*refI + sigQ*refQ)/Ref_mag
    sigQ_corrected = (-sigI*refQ + sigQ*refI)/Ref_mag
    return sigI_corrected, sigQ_corrected

sI_c, sQ_c = phase_correction(sI, sQ, rI, rQ)
plt.figure()
plt.plot(sI_c, label = 'Signal I corrected')
plt.plot(sQ_c, label = 'Signal Q corrected')
plt.legend()