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
#%%

AWG = Tektronix_AWG5014('AWG', 'TCPIP0::169.254.116.102::inst0::INSTR')
#%%
Al_config  = Alazar_Channel_config()
Al_config.ch1_range = 0.1
Al_config.ch2_range = 0.1
Al_config.record_time = 4e-6 #limit is about 15us
Al_config.SR = 1e9
alazar = ATSdriver.AlazarTech_ATS9870(name='Alazar')
Alazar_ctrl = PU.Standard_Alazar_Config(alazar, Al_config)

dll_path = r'C:\Users\Hatlab_3\Desktop\RK_Scripts\New_Drivers\HatDrivers\DLL\sc5511a.dll'
SC4 = SignalCore_SC5511A('SigCore4', serial_number = '10001851', debug = False)
SC9 = SignalCore_SC5511A('SigCore9', serial_number = '1000190E', debug = False)
SigGen = Keysight_N5183B("SigGen", address = "TCPIP0::169.254.29.44::inst0::INSTR")
logging.basicConfig(level=logging.INFO)
#%%
DATADIR = r'Z:\Data\C1\C1_Hakan\phase_preserving_checks\20dB\Multi_LO_Multi_power'
mod_freq = 50e6
# Print all information about this Alazar card
print(alazar.get_idn())
#%%
cf = 6.19665e9
LO_freqs = np.arange(cf+1e6, cf+4.5e6, 0.5e6)
pump_powers = np.linspace(1.63, 2.63, 6)
print(np.size(LO_freqs))
print(np.size(pump_powers))
#%%
amp_pump = 1
for LO_freq in LO_freqs: 
    for pump_power in pump_powers: 
        AWG_config = AWG_Config()
        AWG_config.Mod_freq = 50e6
        AWG_config.Sig_freq = LO_freq
        AWG_config.Ref_freq = AWG_config.Sig_freq+AWG_config.Mod_freq
        
        
        PS = PU.Pulse_Sweep(AWG, AWG_config, Alazar_ctrl, Al_config, SC4, SC9)
        
        cmpc = PU.cavity_mimicking_pulse_class( 
            # name 
            'phase_pres_check',
            #AWG_inst
            AWG,
            # LO_frequency: 
            AWG_config.Sig_freq,
            # DC_offsets: 
            (-0.111, -0.074, 0.0, 0.0),
            # ch2_correction: 
             0.9904003724571333,
            # phase_offset: 
            0.07228873642636158,
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
            #only minus?
            False, 
            )
        p = PU.Phase_Parameter('rotation_phase', cmpc)
        SigGen.output_status(amp_pump)
        SigGen.power(pump_power)
        phase_points = np.linspace(0,2*np.pi, 3, endpoint = False)
        PS.set_independent_parameter(p, phase_points, filename = f'LO_{LO_freq}_pwr_{np.round(pump_power, 2)}_amp_{amp_pump}')
        PS.sweep(DATADIR)


