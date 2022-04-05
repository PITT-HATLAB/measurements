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

        
    
#%%fluxsweep with or without the generator on

DATADIR = r'Z:\Data\N10_L2_2P\cooldown_2\FS'

name = 'wide_cal_sweep'

CWSWP = CW.CW_sweep(name, "VNA", VNA_inst = pVNA, SA_inst = None, Gen_arr = [])

CWSWP.setup_VNA('FREQ',5e9, 7.5e9, 500) #start, stop, points
current_par = CW.wrapped_current(yoko2.current, yoko2.change_current, ramp_rate = 0.05e-3)
current_dict = dict(name = 'bias_current', parameter = current_par, vals = np.linspace(-3e-3, 3e-3, 300))
# pump_dict = dict(name = 'pumpONOFF', parameter = SigGen.power, vals = [-20, 9, 12, 15])
CWSWP.add_independent_parameter(current_dict)
# CWSWP.add_independent_parameter(pump_dict)
CWSWP.eta()
#%%
vna_fp, sa_fp = CWSWP.sweep(DATADIR, debug = True, VNA_avgnum = 1, SA_avgnum = 500)

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
#%%
vna_fp, sa_fp = CWSWP.sweep(DATADIR, debug = True, VNA_avgnum = 15, SA_avgnum = 500)

#%% quick bias-point duffing

DATADIR = r'Z:\Data\SH6F1_1141\gp7\duffing'

name = 'Gen_Sweep_VNA_quickDuff_vnaAtt40dB_genAtt30dB'

CWSWP = CW.CW_sweep(name, "VNA", VNA_inst = pVNA, SA_inst = CXA, Gen_arr = [SC9])

CWSWP.setup_VNA('FREQ', pVNA.fcenter()-500e6, pVNA.fcenter()+500e6, 2000) #start, stop, points
# CWSWP.setup_SA(7.111e9, 8.111e9)
# vna_power_dict = dict(name = 'vna_input_power', parameter = pVNA.power, vals = np.linspace(-35, -25, 10))
duff_tone_dict = dict(name = 'gen_power', parameter = SC9.power, vals = np.linspace(-20, 15, 36))

# CWSWP.add_independent_parameter(vna_power_dict)
CWSWP.add_independent_parameter(duff_tone_dict)

#%%
vna_fp, sa_fp = CWSWP.sweep(DATADIR, debug = True, VNA_avgnum = 10, SA_avgnum = 500)

#%%hardcore duffing test, requires a filepath to a fluxsweep fit file

DATADIR = r'Z:\Data\N10_L2_SQ\cooldown_2\Duffing'

name = 'N10_L2_2P_Duff'
fs_fit_fp = r'Z:/Data/N10_L2_SQ/FS_Fits/2022-04-04/2022-04-04_0003_N10_L2_2P/2022-04-04_0003_N10_L2_2P.ddh5'

CWSWP = CW.CW_sweep(name, "VNA", VNA_inst = pVNA, SA_inst = None, Gen_arr = [SigGen])

current_par = CW.wrapped_current(yoko2.current, yoko2.change_current, ramp_rate = 1e-3)
current_vals = np.linspace(-4e-3, -2e-3, 50)

amp_par = CW.amplifier_bias(current_par, SigGen.frequency, fs_fit_fp, gen_offset = -0.1e9)
amp_par.preview_range(current_vals)
CWSWP.setup_VNA('FREQ', pVNA.fcenter()-1e9, pVNA.fcenter()+1e9, 200) #start, stop, points
duff_tone_dict = dict(name = 'gen_power', parameter = SigGen.power, vals = np.linspace(-20, -10, 11))
amp_bias_dict = dict(name = 'amp_bias', parameter = amp_par, vals = current_vals)
CWSWP.add_independent_parameter(amp_bias_dict)
CWSWP.add_independent_parameter(duff_tone_dict)

CWSWP.eta()
#%%
vna_fp, sa_fp = CWSWP.sweep(DATADIR, debug = True, VNA_avgnum = 1, SA_avgnum = 500)
 #%%
DATADIR = r'Z:\Data\SH6F1_1141\gp8\high_sat_pwr_gen_swp'

name = 'pow_sweep_vna_pow'

CWSWP = CW.CW_sweep(name, "both", VNA_inst = pVNA, SA_inst = CXA, Gen_arr = [SigGen])
CWSWP.setup_VNA('FREQ', 7.575e9, 7.675e9, 200) #start, stop, points
CWSWP.setup_SA( 7.575e9, 7.675e9)
vna_power_dict = dict(name = 'vna_input_power', parameter = pVNA.power, vals = np.linspace(-30, -10, 21))
pump_power_dict = dict(name = 'pump_power', parameter = SigGen.power, vals = np.linspace(14.5, 15.5, 11))

CWSWP.add_independent_parameter(vna_power_dict)
CWSWP.add_independent_parameter(pump_power_dict)
CWSWP.eta()
#%%
vna_fp, sa_fp = CWSWP.sweep(DATADIR, debug = True, VNA_avgnum = 50, SA_avgnum = 500)

#%% adjusting current, gen power, and gen frequency around a known point. Like a taco, but also varying current by small steps
DATADIR = r'Z:\Data\SH6F1_1141\gp9\2a_sweep'

name = 'gen_pow_and_freq_sweep'

CWSWP = CW.CW_sweep(name, "both", VNA_inst = pVNA, SA_inst = CXA, Gen_arr = [SigGen])
# CWSWP.setup_VNA('FREQ', 7.511e9, 7.711e9, 2000) #start, stop, points
# CWSWP.setup_SA(7.511e9, 7.711e9)
CWSWP.setup_VNA('FREQ', 7657581971.94, 7687581971.94, 100) #start, stop, points
CWSWP.setup_SA(7657581971.94, 7687581971.94)
# vna_power_dict = dict(name = 'vna_input_power', parameter = pVNA.power, vals = np.linspace(-45, -10, 36))
pump_power_dict = dict(name = 'pump_power', parameter = SigGen.power, vals = np.linspace(8, 12, 9))
pump_fc= 15345000000.94
pump_freq_dict = dict(name = 'pump_frequency', parameter = SigGen.frequency, vals = np.linspace(pump_fc-2e6, pump_fc+2e6, 11))


# CWSWP.add_independent_parameter(vna_power_dict)
CWSWP.add_independent_parameter(pump_power_dict)
CWSWP.add_independent_parameter(pump_freq_dict)
#%%
vna_fp, sa_fp = CWSWP.sweep(DATADIR, debug = True, VNA_avgnum = 10, SA_avgnum = 500)

#%%flux CW sweep

DATADIR = r'Z:\Data\SH6F1_1141\fluxweep\2A_pump'

name = 'FS_2A_Gen_pwr_0dBm_freq10'

CWSWP = CW.CW_sweep(name, "VNA", VNA_inst = pVNA, SA_inst = None, Gen_arr = [SigGen])

fcenter = something

CWSWP.setup_VNA('FREQ',fcenter, fcenter, 100) #start, stop, points
current_par = wrapped_current(yoko2.current, yoko2.change_current)
current_dict = dict(name = 'bias_current', parameter = current_par, vals = np.linspace(-0.025e-3, 0.013e-3, 51))
pump_dict = dict(name = 'pump freq', parameter = SigGen.frequency, vals = np.linspace(,,))
CWSWP.add_independent_parameter(current_dict)
CWSWP.add_independent_parameter(pump_dict)
CWSWP.eta()