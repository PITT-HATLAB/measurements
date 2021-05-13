# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 17:41:39 2021

@author: Hatlab_3
"""
import numpy as np
import matplotlib.pyplot as plt
import qcodes.instrument_drivers.AlazarTech.ATS9870 as ATSdriver
import hat_utilities.AWG_and_Alazar.Pulse_Sweeping_utils as PU
from hat_utilities.dataclasses import Alazar_Channel_config, AWG_Config
import logging

from qcodes.instrument_drivers.tektronix.AWG5014 import Tektronix_AWG5014
from hatdrivers.SignalCore_sc5511a import SignalCore_SC5511A
from hatdrivers.Keysight_N5183B import Keysight_N5183B

from plottr.apps.autoplot import main

AWG = Tektronix_AWG5014('AWG', 'TCPIP0::169.254.116.102::inst0::INSTR')
alazar = ATSdriver.AlazarTech_ATS9870(name='Alazar')

dll_path = r'C:\Users\Hatlab_3\Desktop\RK_Scripts\New_Drivers\HatDrivers\DLL\sc5511a.dll'
SC5 = SignalCore_SC5511A('SigCore5', serial_number = '10001851', debug = False)
SC9 = SignalCore_SC5511A('SigCore9', serial_number = '1000190E', debug = False)
SigGen = Keysight_N5183B("SigGen", address = "TCPIP0::169.254.29.44::inst0::INSTR")
logging.basicConfig(level=logging.INFO)
#%%
DATADIR = r'E:\Data\Cooldown_20210408\SNAIL_Amps\C1\Hakan_data\Sweeps\Amplifier_Pump_Power'

amp_detuning = 1e3

mod_freq = 50e6

# Print all information about this Alazar card
print(alazar.get_idn())

Al_config  = Alazar_Channel_config()
Al_config.ch1_range = 0.2
Al_config.ch2_range = 0.1
Al_config.record_time = 4e-6 #limit is about 15us
Al_config.SR = 1e9
 
AWG_config = AWG_Config()
AWG_config.Mod_freq = 50e6
AWG_config.Sig_freq = 12.09e9/2+amp_detuning
AWG_config.Ref_freq = AWG_config.Sig_freq+AWG_config.Mod_freq

PS = PU.Pulse_Sweep(AWG, AWG_config, alazar, Al_config, SC5, SC9)
PS.set_independent_parameter(SigGen.power, -10.5+10, -8.5+10.5, 0.5, arange = True)
PS.sweep(DATADIR)

#%%Measure
PU.Process_One_Acquisition(sI_c, sQ_c, 55, 120)
