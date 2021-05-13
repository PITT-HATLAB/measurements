# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 17:41:39 2021

@author: Hatlab_3
"""
import numpy as np
import matplotlib.pyplot as plt
import qcodes.instrument_drivers.AlazarTech.ATS9870 as ATSdriver
import hat_utilities.AWG_and_Alazar.Pulse_Sweeping_utils as PU
from hat_utilities.dataclasses import Alazar_Channel_config
import logging
from plottr.data import datadict_storage as dds, datadict as dd

from qcodes.instrument_drivers.tektronix.AWG5014 import Tektronix_AWG5014
from hatdrivers.SignalCore_sc5511a import SignalCore_SC5511A
from plottr.apps.autoplot import main

AWG = Tektronix_AWG5014('AWG', 'TCPIP0::169.254.116.102::inst0::INSTR')
alazar = ATSdriver.AlazarTech_ATS9870(name='Alazar')

dll_path = r'C:\Users\Hatlab_3\Desktop\RK_Scripts\New_Drivers\HatDrivers\DLL\sc5511a.dll'
SC5 = SignalCore_SC5511A('SigCore5', serial_number = '10001851', debug = False)
SC9 = SignalCore_SC5511A('SigCore9', serial_number = '1000190E', debug = False)

logging.basicConfig(level=logging.INFO)
#%%
DATADIR = r'E:\Data\Cooldown_20210408\SNAIL_Amps\C1\Hakan_data'
amp_detuning = 1e3
sig_f = 12.09e9/2+amp_detuning
mod_freq = 50e6

name = f"20dB_LO_{np.round(sig_f/1e9, 3)}"
# Print all information about this Alazar card
print(alazar.get_idn())

Al_config  = Alazar_Channel_config()
Al_config.ch1_range = 0.2
Al_config.ch2_range = 0.1
Al_config.record_time = 4e-6 #limit is about 15us
Al_config.SR = 1e9
 
myctrl = PU.Standard_Alazar_Config(alazar, Al_config)

####################### Set up the datadict 
datadict = dd.DataDict(
    time = dict(unit = 'ns'),
    record_num = dict(unit = 'num'),
    I_plus = dict(axes=['record_num', 'time' ], unit = 'DAC'), 
    Q_plus = dict(axes=['record_num', 'time' ], unit = 'DAC'),
    I_minus = dict(axes=['record_num', 'time' ], unit = 'DAC'),
    Q_minus = dict(axes=['record_num', 'time' ], unit = 'DAC')
)

#%%Measure
datadict.validate()

with dds.DDH5Writer(DATADIR, datadict, name=name) as writer:
    sI_c, sQ_c, ref_I, ref_Q = PU.acquire_one_pulse(AWG, myctrl, SC5, SC9, sig_f, mod_freq, Al_config.SR)
    s = list(np.shape(sI_c))
    s[0] = int(s[0]//2) #evenly divided amongst I_plus and I_minus
    writer.add_data(
            record_num = np.repeat(np.arange(s[0]), s[1]),
            time = np.tile(np.arange(int(s[1]))*Al_config.SR/mod_freq, s[0]),
            I_plus = sI_c[0::2].flatten(),
            Q_plus = sQ_c[0::2].flatten(),
            I_minus = sI_c[1::2].flatten(),
            Q_minus = sQ_c[1::2].flatten()
        )

#remove IQ offset? 
#TODO: is this legal?
sI_c = sI_c-np.average(sI_c[:,150:170])
sQ_c = sQ_c-np.average(sQ_c[:,150:170])

PU.Process_One_Acquisition(sI_c, sQ_c, 55, 120)
