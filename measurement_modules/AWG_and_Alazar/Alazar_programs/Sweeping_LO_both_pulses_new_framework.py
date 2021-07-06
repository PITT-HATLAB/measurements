# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 17:41:39 2021

@author: Hatlab_3
"""
import numpy as np
import matplotlib.pyplot as plt
import qcodes.instrument_drivers.AlazarTech.ATS9870 as ATSdriver
import measurement_modules.AWG_and_Alazar.Pulse_Sweeping_utils as PU
import measurement_modules.AWG_and_Alazar.Pulse_Classes as PC
from measurement_modules.dataclasses import Alazar_Channel_config, AWG_Config
import logging

from qcodes.instrument_drivers.tektronix.AWG5014 import Tektronix_AWG5014
from instrument_drivers.base_drivers.SignalCore_sc5511a import SignalCore_SC5511A
from instrument_drivers.base_drivers.Keysight_N5183B import Keysight_N5183B

from plottr.apps.autoplot import main
#%%
AWG = Tektronix_AWG5014('AWG', 'TCPIP0::169.254.116.102::inst0::INSTR')
AWG.write("SOUR1:FREQ 1E+9")
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
DATADIR = r'Z:\Data\C1\C1_Hakan\Gain_pt_0.103mA\signal_power_sweeps\1'
mod_freq = 50e6
# Print all information about this Alazar card
print(alazar.get_idn())
#%%
cf = 6.151798714e9
# LO_freqs = np.arange(cf+1e6, cf+4.5e6, 0.5e6)
LO_freqs = [cf+1.5e6]
# pump_powers = np.linspace(-9.24, -7.24, 12)
# pump_powers = [-20]
print(np.size(LO_freqs))
# print(np.size(pump_powers))
#%%
amp_pump = 1
AWG_config = AWG_Config()
AWG_config.Mod_freq = 50e6
AWG_config.Sig_freq = LO_freqs[0]
AWG_config.Ref_freq = AWG_config.Sig_freq+AWG_config.Mod_freq

PS = PU.Pulse_Sweep(AWG, AWG_config, Alazar_ctrl, Al_config, SC4, SC9)

cmpc = PC.cavity_mimicking_pulse_class(
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
    #amplitude: 
    0.5,
    # phase_rotation:
    0,
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
    
P = PU.Phase_Parameter('rotation_phase', cmpc)
V = PU.Voltage_Parameter('Voltage', cmpc)
LO = PU.LO_Parameter('LO_frequency', PS.ref_gen, PS.sig_gen, AWG_config.Mod_freq)

SigGen.output_status(amp_pump)
SigGen.power(-7.42)
phase_points = np.linspace(0,2*np.pi, 3, endpoint = False)
voltage_points = np.arange(0, 2.5, 0.5)
#ind_par_dict{name: dict(parameter = actual_parameter_class, vals = [np_val_arr])}
amp_dict = dict(Amp = dict(parameter = SigGen.output_status, vals = np.array([0,1])))
phase_dict = dict(Phase = dict(parameter=P, vals = phase_points))
volt_dict = dict(Sig_Volt = dict(parameter=V, vals = voltage_points))
LO_dict = dict(LO_freq = dict(parameter=LO, vals = LO_freqs))

PS.add_independent_parameter(amp_dict)
PS.add_independent_parameter(LO_dict)
PS.add_independent_parameter(volt_dict)
PS.add_independent_parameter(phase_dict)


#%%
PS.sweep(DATADIR)


