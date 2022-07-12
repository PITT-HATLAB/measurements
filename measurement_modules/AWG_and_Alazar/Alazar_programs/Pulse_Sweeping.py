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

import logging
# log_loc = r'C:\Users\Hatlab_3\test.log'
# logging.basicConfig(filename = log_loc)
# logger = logging.getLogger('test')
# logger.setLevel(logging.DEBUG)
# fh = logging.FileHandler(log_loc)
# fh.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# fh.setFormatter(formatter)
#%%
AWG = Tektronix_AWG5014('AWG', 'TCPIP0::169.254.116.102::inst0::INSTR')
AWG.write("SOUR1:FREQ 1E+9")

Al_config  = Alazar_Channel_config()
Al_config.record_num = 7686
# Al_config.record_num = 11529 
Al_config.ch1_range = 0.4
Al_config.ch2_range = 0.1
# Al_config.record_time = 4e-6 #limit is about 15us 
Al_config.record_time = 4e-6
Al_config.SR = 1e9
alazar = ATSdriver.AlazarTech_ATS9870(name='Alazar')
Alazar_ctrl = PU.Standard_Alazar_Config(alazar, Al_config)

dll_path = r'C:\Users\Hatlab_3\Desktop\RK_Scripts\New_Drivers\HatDrivers\DLL\sc5511a.dll'
SigGen = Keysight_N5183B("SigGen", address = "TCPIP0::169.254.29.44::inst0::INSTR")
# SC5 = SignalCore_SC5511A('SigCore5', serial_number = '10001852', debug = True)
# SigGen = SC5
logging.basicConfig(level=logging.INFO)
SC4 = SignalCore_SC5511A('SigCore4', serial_number = '10001851', debug = False)
SC9 = SignalCore_SC5511A('SigCore9', serial_number = '1000190E', debug = False)

#%%

DATADIR = r'Z:\Data\N25_L3_SP_3\time_domain\bp1\ps'

# mod_freq = -50e6
mod_freq = -50e6
# Print all information about this Alazar card
print(alazar.get_idn())
# cf = 6.066e9
# target_freq = 6.7999e9
SG_freq = 11282400000.0
target_freq = SG_freq/2

SC4.frequency(target_freq)
SC9.frequency(target_freq+mod_freq)
sig_freqs = np.array([target_freq, target_freq+10e6, target_freq+20e6, target_freq+25e6])
detuning = 25e6
ref_freqs = np.arange(mod_freq-detuning, mod_freq+4*detuning, detuning)
# LO_freqs = np.arange(cf+0.5e6, cf+7.5e6, 0.2e6)

# SG_pow = 9.9
# SG_pow = 7.39
# SG_pow = 10.32
# SG_pow = 8.21
SG_pow = 10.7

# SG_freq = 11.322e9
# SG_freq = 11.2038e9
# SG_freq = 11.2128e9
# SG_freq = 11.323e9

pump_powers = np.array([SG_pow])
# pump_powers = [-20]
# print(np.size(LO_freqs))
# print(np.size(pump_powers))


AWG_config = AWG_Config()
AWG_config.Mod_freq = mod_freq
AWG_config.Sig_freq = target_freq
AWG_config.Ref_freq = target_freq+mod_freq

name = 'pwr_swp'
# name = 'loopback_test_at_idler'
num_reps = 10
amp_pump = 1


phase_points = -np.pi/2+0.25+np.arange(0,2*np.pi, np.pi)
# voltage_points = np.sqrt(np.power(10, np.arange(-30-20, 0-14, 3)/10)*50)*np.sqrt(2)
# voltage_points = np.sqrt(np.power(10, np.arange(-50, -40, 1)/10)*50)*np.sqrt(2)
voltage_points = np.arange(0.1, 1, 0.1)
phase_correction_points = np.linspace(-0.3, 0.3, 16)
rep_array = np.arange(num_reps)
wait_times = np.arange(0, 500, 10)  
phase_vals = np.arange(0, 2*np.pi, np.pi/8)[12:]

cmpc = PC.cavity_mimicking_pulse_class_3_state(
    # name 
    name,
    #AWG_inst
    AWG,
    # LO_frequency: 
    AWG_config.Sig_freq,
    # DC_offsets: 
        #lsb
    #(-0.124, -0.062, 0.0, 0.0),
    # (-0.128, -0.063, 0.0, 0.0), #usb
    #imd product testing
    # (-0.136, -0.164, 0.0, 0.0), 
    (-0.125, -0.054, 0.0, 0.0), 
    # ch2_correction: 
    # 0.9911,
    0.986, 
    # 1,
    # phase_correction_on_I: 
    # 0.072,
    # 0.0426,
    -0.059,
    #amplitude: 
    # 0.311, #about 0dBm steady state
    0.3,
    # phase_rotation:
    0,
    #wait time before alazar is triggered
    0, 
    # sim_filepath_g: 
    r'Z:/Data/SA_2X_B1/Hakan/simulated_cavity_states/kappa_2MHz_Chi_2MHz_and_ringdown_G.csv',
    # sim_filepath_e: 
    r'Z:/Data/SA_2X_B1/Hakan/simulated_cavity_states/kappa_2MHz_Chi_2MHz_and_ringdown_E.csv',
    # sim_filepath_f: 
    r'Z:/Data/SA_2X_B1/Hakan/simulated_cavity_states/kappa_2MHz_Chi_2MHz_and_ringdown_F.csv',
    # SR: 
    1e9,
    # npts: 
    4000,
    #only plus? 
    False, 
    #only minus? 
    False, 
    )

PS = PU.Pulse_Sweep_3_state_raw_data(name, AWG, AWG_config, Alazar_ctrl, Al_config, SC4, SC9, gen_power=15)
    
P = PU.Phase_Parameter('rotation_phase', cmpc)
V = PU.Voltage_Parameter('Voltage', cmpc)
sig = PU.signalParameter('LO_frequency', PS.ref_gen, PS.sig_gen, AWG_config.Mod_freq)
ref = PU.refParameter('ref_det', PS.ref_gen, PS.sig_gen)
PCor = PU.Phase_Correction_Parameter('Iphase_corr', cmpc)
rep = PU.repitition_parameter('Rep')
Wait = PU.wait_time_parameter("Trigger_wait", cmpc)

SigGen.output_status(amp_pump)
SigGen.frequency(SG_freq)
SigGen.power(SG_pow)

#ind_par_dict{name: dict(parameter = actual_parameter_class, vals = [np_val_arr])}
amp_dict = dict(Amp = dict(parameter = SigGen.output_status, vals = np.array([0,1])))
pump_pwr_dict = dict(pump_pwr = dict(parameter = SigGen.power, vals = pump_powers))
phase_dict = dict(Phase = dict(parameter=P, vals = phase_points))
volt_dict = dict(Sig_Volt = dict(parameter=V, vals = voltage_points))
sig_dict = dict(sig_freq = dict(parameter=sig, vals = sig_freqs))
ref_dict = dict(ref_det = dict(parameter=ref, vals = ref_freqs))
phase_corr_dict = dict(I_Ph_corr = dict(parameter=PCor, vals = phase_correction_points))
rep_dict = dict(Rep = dict(parameter=rep, vals = rep_array))
wait_dict = dict(Trigger_wait = dict(parameter = Wait, vals = wait_times))
gen_phase_dict = dict(gen_phase = dict(parameter = SigGen.phase, vals = phase_vals))
# PS.add_independent_parameter(phase_corr_dict)
# PS.add_independent_parameter(amp_dict)
# PS.add_independent_parameter(pump_pwr_dict)
# PS.add_independent_parameter(sig_dict)
PS.add_independent_parameter(volt_dict)
# PS.add_independent_parameter(ref_dict)
# PS.add_independent_parameter(phase_dict)
# PS.add_independent_parameter(rep_dict)
# PS.add_independent_parameter(gen_phase_dict)

# PS.add_independent_parameter(wait_dict)
# 
# V(1.5) #will run pulse setup
cmpc.setup_pulse(preview = True)
# V(2)
#%%
# V(2)
fp = PS.sweep(DATADIR, debug = True)
print(fp)
#%%
cmpc.print_info()
cmpc.setup_pulse(preview = True)


