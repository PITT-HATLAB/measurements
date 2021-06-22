# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 17:41:39 2021

@author: Hatlab_3
"""
import numpy as np
import matplotlib.pyplot as plt
import qcodes.instrument_drivers.AlazarTech.ATS9870 as ATSdriver
import measurement_modules.AWG_and_Alazar.Pulse_Sweeping_utils as PU
from measurement_modules.dataclasses import Alazar_Channel_config, AWG_Config
import logging

from qcodes.instrument_drivers.tektronix.AWG5014 import Tektronix_AWG5014
from instrument_drivers.base_drivers.SignalCore_sc5511a import SignalCore_SC5511A
from instrument_drivers.base_drivers.Keysight_N5183B import Keysight_N5183B

from plottr.apps.autoplot import main

AWG = Tektronix_AWG5014('AWG', 'TCPIP0::169.254.116.102::inst0::INSTR')
alazar = ATSdriver.AlazarTech_ATS9870(name='Alazar')

dll_path = r'C:\Users\Hatlab_3\Desktop\RK_Scripts\New_Drivers\HatDrivers\DLL\sc5511a.dll'
SC4 = SignalCore_SC5511A('SigCore4', serial_number = '10001851', debug = False)
SC9 = SignalCore_SC5511A('SigCore9', serial_number = '1000190E', debug = False)
SigGen = Keysight_N5183B("SigGen", address = "TCPIP0::169.254.29.44::inst0::INSTR")
logging.basicConfig(level=logging.INFO)
#%%
DATADIR = r'E:\Data\Cooldown_20210611\SNAIL_Amps\C1\phase_preserving_checks\15dB\amp_on\33pt_sweep_with_switch'

amp_detuning = 1e6

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
AWG_config.Sig_freq = 6112083796.8+amp_detuning
AWG_config.Ref_freq = AWG_config.Sig_freq+AWG_config.Mod_freq
#%%
PS = PU.Pulse_Sweep(AWG, AWG_config, alazar, Al_config, SC4, SC9)
#%%
cmpc = PU.cavity_mimicking_pulse_class( 
    # name 
    'phase_pres_check',
    #AWG_inst
    AWG,
    # LO_frequency: 
    AWG_config.Sig_freq,
    # DC_offsets: 
    (-0.125, -0.081, 0.0, 0.0),
    # ch2_correction: 
    0.9988184173068773,
    # phase_offset: 
    0.07260407094218913,
    # phase_rotation: 
    0,
    #amplitude: 
    0.5,
    # sim_filepath_plus: 
    r'\\phyast-hatlab.univ.pitt.edu\HATLAB\RK\Transfer\kappa_2MHz_Chi_2MHz_-det_plus_ringdown.csv',
    # sim_filepath_minus: 
    r'\\phyast-hatlab.univ.pitt.edu\HATLAB\RK\Transfer\kappa_2MHz_Chi_2MHz_+det_plus_ringdown.csv',
    # SR: 
    1e9,
    # npts: 
    1000, 
    #only plus?
    False, 
    #only
    False, 
    )
p = PU.Phase_Parameter('rotation_phase', cmpc)
#%%
amp_pump = 1
SigGen.output_status(amp_pump)
PS.set_independent_parameter(p, 0, 2*np.pi, 33, arange = False, filename = f'15dB_Gain_pt_amp_{amp_pump}')
#%%
PS.sweep(DATADIR)


