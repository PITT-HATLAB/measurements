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
from qcodes.instrument.parameter import Parameter
from plottr.apps.autoplot import main

#%% quick bias-point duffing

DATADIR = r'Z:\Data\SH6F1_1141\gp7\duffing'

name = 'Gen_Sweep_VNA_quickDuff_vnaAtt40dB_genAtt40dB'

CWSWP = CW.CW_sweep(name, "VNA", VNA_inst = pVNA, SA_inst = CXA, Gen_arr = [SC9])

CWSWP.setup_VNA('FREQ', 7.739e9-200e6, 8.140e9, 2000) #start, stop, points
# CWSWP.setup_SA(7.111e9, 8.111e9)
# vna_power_dict = dict(name = 'vna_input_power', parameter = pVNA.power, vals = np.linspace(-35, -25, 10))
duff_tone_dict = dict(name = 'gen_power', parameter = SC9.power, vals = np.linspace(-20, 15, 36))

# CWSWP.add_independent_parameter(vna_power_dict)
CWSWP.add_independent_parameter(pump_power_dict)

#%%
# V(2)
CWSWP.sweep(DATADIR, debug = True, VNA_avgnum = 10, SA_avgnum = 500)
#%%
DATADIR = r'Z:\Data\SH6F1_1141\gp7\gen_power_sweep'

name = 'Gen_Sweep_VNA_and_SA_probe_S_vnaAtt40dB_genAtt10dB'

CWSWP = CW.CW_sweep(name, "both", VNA_inst = pVNA, SA_inst = CXA, Gen_arr = [SigGen])
# CWSWP.setup_VNA('FREQ', 7.511e9, 7.711e9, 2000) #start, stop, points
# CWSWP.setup_SA(7.511e9, 7.711e9)
CWSWP.setup_VNA('FREQ', 7.111e9, 8.111e9, 2000) #start, stop, points
CWSWP.setup_SA(7.111e9, 8.111e9)
# vna_power_dict = dict(name = 'vna_input_power', parameter = pVNA.power, vals = np.linspace(-35, -25, 10))
pump_power_dict = dict(name = 'pump_power', parameter = SigGen.power, vals = np.linspace(-7, -3, 30))

# CWSWP.add_independent_parameter(vna_power_dict)
CWSWP.add_independent_parameter(pump_power_dict)

#%%
# V(2)
CWSWP.sweep(DATADIR, debug = True, VNA_avgnum = 10, SA_avgnum = 500)




