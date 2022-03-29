# -*- coding: utf-8 -*-
"""
Created on Tue Sep 21 15:42:05 2021

@author: Hatlab_3
"""

import easygui 
import matplotlib.pyplot as plt
import numpy as np 
import h5py
import datetime as dt
from instrument_drivers.meta_instruments import Modes
import time
import pickle
# from measurement_modules.VNA.Simple_Sweeps import Flux_Sweep, Frequency_Sweep, Power_Sweep, saturation_gen_power_sweep
from measurement_modules.Adaptive_Sweeps.Gain_Power_vs_Flux import Gain_Power_vs_Flux
# from measurement_modules.Adaptive_Sweeps.Duffing_Test import Duffing_Test
from measurement_modules.dataclasses import GPF_dataclass

from plottr.data import datadict_storage as dds, datadict as dd
from datetime import datetime
from plottr.apps.autoplot import autoplotDDH5, script, main
from dataclasses import dataclass

#%%Minimum Gain pwr vs flux
GP_F_dc = GPF_dataclass(
    cwd = r'Z:\Data\SA_3B1_1131\tacos\2s',
    filename = f'{yoko2.current()}mA_TACO',
    inst_dict = dict(VNA = pVNA, CS = yoko2, Gen = SigGen),
    bias_current = yoko2.current(),
    #SigGen settings
    gen_att = 3,
    #VNA settings
    vna_att = 53,
    vna_p_avgs = 30,
    vna_power = -35
    )
#%% go to your start point then run this
GP_F_dc.set_start()
#%% #jump to  a possible stop point
GP_F_dc.goto_stop(gen_freq_offset = 30e6, gen_power_offset = -5)
#%%tune, then run this
GP_F_dc.set_stop(gen_pts = 30)
#%%check: 
GP_F_dc.goto_start()
#%%
GP_F_dc.set_sweep_settings(
                           peak_width_minimum = 1, #MHz
                           vna_avgs = test123, 
                           stepsize = 0.1,  #power step in dBm
                           block_size = 10,
                           limit = 8,
                           target_gain = 20,
                           threshold = 1, 
                           gain_tracking = 'gen_frequency', 
                           gain_detuning = 300e3)
#%%if you only want one, just run this
GP_F_dc.sweep()
#%%
sweeps = []
#%%
sweeps.append(GP_F_dc)
#%%
for sweep in sweeps: 
    sweep.sweep()
#%%
for sweep in sweeps: 
    sweep.threshold = 1
#%% Set up a sweep of currents based off of the known taco (be sure it is a decent minimum)
from hat_utilities.ddh5_Plotting.utility_modules.FS_utility_functions import fit_fluxsweep
from scipy.interpolate import interp1d

datadir = r'E:\Data\Cooldown_20210104\fluxsweep\2021-01-04_0003_Recentering_FS.ddh5'
savedir = r'E:\Data\Cooldown_20210104\fluxsweep'

FS = fit_fluxsweep(datadir, savedir, '2021-01-04_0004_Recentering_FS_fit')
FS.initial_fit(5.5e9, QextGuess = 50, magBackGuess = 0.001)
#%% Automatic Fitting (be sure initial fit is good!)
currents, res_freqs, Qints, Qexts, magBacks = FS.semiauto_fit(FS.currents, FS.vna_freqs/(2*np.pi), FS.undriven_vna_power, FS.undriven_vna_phase, FS.initial_popt, debug = False, savedata = False)
#Finding and plotting flux quanta and flux variables, interpolating resonance frequencies to generate resonance functions wrt bias current and flux
res_func = interp1d(currents, res_freqs, 'quadratic')
plt.figure(2)
plt.plot(currents, res_freqs, label = 'fitted data')
plt.plot(currents, res_func(currents), label = 'quadratic interpolation')
plt.legend()
#%%
#ALSO NEED A FITTED FLUXSWEEP for res_func
cwd = r'E:\Data\Cooldown_20210104'

if cwd == None: 
    raise Exception("CWD not chosen!")
filename = 's41s_pVNA_TACO_-0.16mAto-0.163mA_-20MHz_to_+20MHz_res_func_guessing'

VNA = pVNA
vna_att = 30
Gen = SigGen
gen_att = 10
CS = yoko2
mode = None

c_start = -0.16e-3
c_stop = -0.163e-3
c_stepsize = -0.001e-3
current_settings = [c_start, c_stop, c_stepsize]

#these should starting for the 1st taco
gen_freq_known = float(res_func(-0.16e-3))*2
gen_pow_known = -3.2
gen_init_freq_range = 40e6
gen_init_freq_stepsize = 2e6
Gen_settings = [gen_freq_known, gen_init_freq_range, gen_init_freq_stepsize, gen_pow_known]

VNA_fcenter = float(res_func(-0.16e-3))
VNA_fspan = 100e6
VNA_favgs = 40
VNA_fpower = -40
VNA_fpoints = 1601
VNA_settings = [VNA_fcenter, VNA_fspan, VNA_favgs, VNA_fpower, VNA_fpoints]

GP_F = Gain_Power_vs_Flux(CS, Gen, VNA, cwd, filename, gen_att = gen_att, vna_att = vna_att)
GP_F.VNA_avg_number = VNA_favgs
GP_F.sweep_min_power_and_saturation_vs_current(current_settings, res_func, VNA_settings, Gen_settings, 
                                               stepsize = 0.1, limit = 10, target_gain = 20, threshold = 2, 
                                               saturation_sweep = True, 
                                               vna_p_start = -43, vna_p_stop = 10, vna_p_steps = 1000, vna_p_avgs = 100)