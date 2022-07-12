# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 17:41:39 2021

@author: RRK

Purpose: troubleshoot CW sweeps class
"""
import numpy as np
import matplotlib.pyplot as plt
import measurement_modules.VNA.CW_Sweeping_Utils as CW
import logging
from plottr.data.datadict_storage import all_datadicts_from_hdf5
from plottr.apps.autoplot import main

import time
#%%
#set up an amp bias parameter to help me keep track of things
fs_fit_fp = r'Z:/Data/N25_L3_SQ/FS_fits/2022-04-25/2022-04-25_0003_N25_L3_2Pcooldown_2/2022-04-25_0003_N25_L3_2Pcooldown_2.ddh5'
current_par = CW.wrapped_current(yoko2.current, yoko2.change_current, ramp_rate = 0.2e-3)
amp_par = CW.amplifier_bias(current_par, SigGen.frequency, fs_fit_fp, gen_offset = -0.5e9, gen_factor = 1)

#%%fluxsweep with or without the generator on

DATADIR = r'Z:/Data/N25_L3_SP_3/fluxsweeps'

name = 'FS_-30dBm_wider'

CWSWP = CW.CW_sweep(name, "VNA", VNA_inst = pVNA, SA_inst = None, Gen_arr = [])
CWSWP.setup_VNA('FREQ',4.5e9, 6.5e9, 1000) #start, stop, points
current_par = CW.wrapped_current(yoko2.current, yoko2.change_current, ramp_rate = 1e-3)
current_dict = dict(name = 'bias_current', parameter = current_par, vals = np.linspace(-10e-3, 10e-3, 2001))
# pump_dict = dict(name = 'pumpONOFF', parameter = SigGen.power, vals = [-20, 9, 12, 15])
CWSWP.add_independent_parameter(current_dict)
# CWSWP.add_independent_parameter(pump_dict)
CWSWP.eta()
#%%
vna_fp, sa_fp = CWSWP.sweep(DATADIR, debug = True, VNA_avgnum = 5, SA_avgnum = 500)


#%%
vna_fp, sa_fp = CWSWP.sweep(DATADIR, debug = True, VNA_avgnum = 15, SA_avgnum = 500)

#%%hardcore duffing test, requires a filepath to a fluxsweep fit file

DATADIR = r'Z:\Data\N25_L3_SP_3\duffing'

name = 'N25_L3_SP_3_Duff'
fs_fit_fp = r'Z:/Data/N25_L3_SP_3/fluxsweeps/fits/2022-06-17_0001_N25_L3_SP.ddh5'

Gen = SigGen

CWSWP = CW.CW_sweep(name, "VNA", VNA_inst = pVNA, SA_inst = None, Gen_arr = [Gen])

current_par = CW.wrapped_current(yoko2.current, yoko2.change_current, ramp_rate = 1e-3)
current_vals = np.linspace(0, 1e-3, 100)

amp_par = CW.amplifier_bias(current_par, Gen.frequency, fs_fit_fp, gen_offset = 7e9)
amp_par.preview_range(current_vals, show_pump= 1)
CWSWP.setup_VNA('FREQ', 4e9, 7e9, 200) #start, stop, points
duff_tone_dict = dict(name = 'gen_power', parameter = Gen.power, vals = np.linspace(0, 18, 19))
amp_bias_dict = dict(name = 'amp_bias', parameter = amp_par, vals = current_vals)
CWSWP.add_independent_parameter(amp_bias_dict)
CWSWP.add_independent_parameter(duff_tone_dict)

CWSWP.eta()
#%%
vna_fp, sa_fp = CWSWP.sweep(DATADIR, debug = True, VNA_avgnum = 3, SA_avgnum = 500)

#%%scanning possible pump points like a taco, requires a filepath to a fluxsweep fit file

DATADIR = r'Z:\Data\N25_L3_SP_3\pump_scans'

name = 'N25_L3_SP_3_Pump'
fs_fit_fp = r'Z:/Data/N25_L3_SP_3/fluxsweeps/fits/2022-06-17_0001_N25_L3_SP.ddh5'

CWSWP = CW.CW_sweep(name, "both", VNA_inst = pVNA, SA_inst = CXA, Gen_arr = [SigGen])
CWSWP.setup_VNA('FREQ', 5e9, 6.5e9, 400) #start, stop, points
CWSWP.setup_SA(5e9, 6.5e9) #start, stop, points
current_vals = np.linspace(0e-3, 1e-3, 10)
pump_det_vals = np.linspace(-400e6, 400e6, 41)
pump_power_vals = np.linspace(-5, 15, 41)

amp_par = CW.amplifier_bias(current_par, SigGen.frequency, fs_fit_fp, gen_offset = 0, gen_factor = 2, norm = 0, VNA_inst = pVNA)
amp_par.preview_range(current_vals, show_pump = 0)

gen_detuning = CW.generator_detuning(SigGen.frequency)

amp_bias_dict = dict(name = 'amp_bias', parameter = amp_par, vals = current_vals)
pump_det_dict = dict(name = 'Generator_detuning', parameter = gen_detuning, vals = pump_det_vals)
pump_power_dict = dict(name = 'gen_power', parameter = SigGen.power, vals = pump_power_vals)

CWSWP.add_independent_parameter(amp_bias_dict)
CWSWP.add_independent_parameter(pump_det_dict)
CWSWP.add_independent_parameter(pump_power_dict)

CWSWP.eta()
#%%
vna_fp, sa_fp = CWSWP.sweep(DATADIR, debug = True, VNA_avgnum = 10, SA_avgnum = 100)
 #%% power sweep
DATADIR = r'Z:\Data\N25_L3_SP_2\time-domain\pump_downconv_sweep\SA_pwr_sweep'

name = 'pow_sweep_VNA_signal_src'

CWSWP = CW.CW_sweep(name, "SA", VNA_inst = pVNA, SA_inst = CXA, Gen_arr = [SigGen])
CWSWP.setup_SA(5578900000, 5628900000) #start, stop, points
# CWSWP.setup_SA( 7.575e9, 7.675e9)
# vna_power_dict = dict(name = 'vna_input_power', parameter = pVNA.power, vals = np.linspace(-30, -10, 21))
vna_power_dict = dict(name = 'Signal Power (dBm RT)', parameter = pVNA.power, vals = np.linspace(-20, 0, 21))

CWSWP.add_independent_parameter(vna_power_dict)
# CWSWP.add_independent_parameter(pump_power_dict)

CWSWP.eta()
#%%
vna_fp, sa_fp = CWSWP.sweep(DATADIR, debug = True, VNA_avgnum = 3, SA_avgnum = 500)
#%%
 #%% CW sweep
DATADIR = r'Z:\Data\NIST_Amp_Qubit_msmts\N25_L3_SP_2\cavity_msmts\CW_spec\using_avg_over_freq'

name = 'CW_qubit_sweep_0dBm_20dBatt_right_freq'

CWSWP = CW.CW_sweep(name, "VNA", VNA_inst = pVNA, SA_inst = None, Gen_arr = [SC4])
CWSWP.setup_VNA('FREQ', 5.52107e9, 5.52107e9, 100, avg_over_freq=True) #start, stop, points
# CWSWP.setup_SA( 7.575e9, 7.675e9)
# vna_power_dict = dict(name = 'vna_input_power', parameter = pVNA.power, vals = np.linspace(-30, -10, 21))
freq_dict = dict(name = 'Signal Freq (Hz)', parameter = SC4.frequency, vals = np.linspace(3e9, 5e9, 4001))

CWSWP.add_independent_parameter(freq_dict)
# CWSWP.add_independent_parameter(pump_power_dict)

CWSWP.eta()
#%%
vna_fp, sa_fp = CWSWP.sweep(DATADIR, debug = True, VNA_avgnum = 1, SA_avgnum = 500)
#%%
SigGen.print_info()
#%%Stability measurements 
DATADIR = r'Z:\Data\SA_3B1_1131\gain_stability'

name = 'gain_pt_1'

CWSWP = CW.CW_sweep(name, "VNA", VNA_inst = pVNA, SA_inst = None, Gen_arr = [SigGen])
CWSWP.setup_VNA('POW', -43, 0, 1000) #start, stop, points
time_par = CW.Time()
time_dict = dict(name = 'time', parameter = time_par, vals = np.tile(43.2, 1000))
# pump_power_dict = dict(name = 'pump_power', parameter = SigGen.power, vals = np.linspace(14.5, 15.5, 11))
CWSWP.add_independent_parameter(time_dict)
# CWSWP.add_independent_parameter(pump_power_dict)
CWSWP.eta()