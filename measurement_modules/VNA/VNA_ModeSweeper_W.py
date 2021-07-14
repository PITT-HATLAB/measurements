# -*- coding: utf-8 -*-
"""
Created on Wed Nov 18 09:37:59 2020

@author: Hatlab_3

Create a similar file to modesweeper, but usign the data-saving framework from
Plottr
"""
import easygui 
import matplotlib.pyplot as plt
import numpy as np 
import h5py
import datetime as dt
from instrument_drivers.meta_instruments import Modes
import time
import pickle
from measurement_modules.VNA.Simple_Sweeps import Flux_Sweep, Frequency_Sweep, Power_Sweep, Saturation_Sweep
from measurement_modules.Adaptive_Sweeps.Gain_Power_vs_Flux import Gain_Power_vs_Flux
from measurement_modules.Adaptive_Sweeps.Duffing_Test import Duffing_Test
from measurement_modules.dataclasses import GPF_dataclass

from plottr.data import datadict_storage as dds, datadict as dd
from datetime import datetime
from plottr.apps.autoplot import autoplotDDH5, script, main
from dataclasses import dataclass

#%% fluxsweep

DATADIR = r'Z:\Data\SA_2X_B1\fluxsweep'
name='B1_FS1'
#instruments
VNA = pVNA
CS = yoko2
#starting parameters
c_start = -0.00013356
c_stop = 0.00035616
c_points = 500

VNA_fcenter, VNA_fspan, VNA_fpoints, VNA_avgs = pVNA.fcenter(), pVNA.fspan(), 1600, 3
VNA_settings = [VNA, VNA_fcenter, VNA_fspan, VNA_fpoints, VNA_avgs]

CS_settings = [CS, c_start, c_stop, c_points]
print(f"Estimated time: {VNA.sweep_time()*VNA_avgs*c_points/60} minutes")
#%%
Flux_Sweep(DATADIR, name, VNA_settings, CS_settings)

#%% Frequency Sweep
DATADIR = r'E:\Data\Cooldown_20210408\SNAIL_Amps\C1\pump_freq_sweeps\subharmonic'

#instruments
VNA = pVNA
Gen = SigGen
#starting parameters
pows = [SigGen.power()]
names = [f'C1_Subharmonic_Sweep{power}dbm' for power in pows]

for (name, sgpow) in list(zip(names, pows)): 
    SigGen.power(sgpow)
    
    VNA_fcenter, VNA_fspan, VNA_fpoints, VNA_avgs, VNA_power = 6230428564.61, 100e6, 1601, 30, -40
    VNA.power(VNA_power)
    fcenter = 2076809521.537
    fstart, fstop, fpoints = fcenter-1*160e6, fcenter+160e6, 160
    
    VNA_settings = [VNA, VNA_fcenter, VNA_fspan, VNA_fpoints, VNA_avgs]
    Gen_settings = [Gen, fstart, fstop, fpoints]
    
    Frequency_Sweep(DATADIR, name, VNA_settings, Gen_settings)
SigGen.output_status(0)
            
#%%power sweep

#instruments
VNA = pVNA
pVNA.rfout(1)
# Gen = SigGen
# mode = CuCav
mode = AlCav
#ifbw = 200 for low power, 500 high power

mode.push(VNA = pVNA)
VNA_avgs = mode.avgnum()
# AlCav.push(VNA = pVNA)
temp = 820
if mode.name == 'AlCav': 
    DATADIR = r'Z:\Texas\Cooldown_20210525\PC_HPAl_etch_3'

elif mode.name == 'CuCav': 
    DATADIR = r'Z:\Texas\Cooldown_20210525\PC_CuCollar'
else: 
    raise Exception("AAAAAHHHHH")
#starting parameters
VNA_fcenter, VNA_fspan, VNA_fpoints = VNA.fcenter(), VNA.fspan(), VNA.num_points()
# 
p_start, p_stop, p_points = -43, 20, 64 #wi!h -40dB on RT atten
# p_start, p_stop, p_points = -20, 20, 41 #with 0 dB on RT atten
# name = f'vna_trace_vs_vna_power_40dBatten_{temp}mK'
name = f'vna_trace_vs_vna_power_40dBatten_{temp}mK'

VNA_settings = [VNA, VNA_fcenter, VNA_fspan, VNA_fpoints, VNA_avgs]
Gen_settings = [VNA, p_start, p_stop, p_points]
Power_Sweep(DATADIR, name, VNA_settings, Gen_settings)
#%% Duffing Test
#v2: uses a file with a pre-fitted fluxsweep to help out

DATADIR = r'E:\Data\Cooldown_20210104'
name = "Chempot_Duffing_wide"
fs_fit_file = r'E:\Data\Cooldown_20210104\20210330_MariaChemPot_Processing\2021-03-30\2021-03-30_0006_20210330_Chempot_FS_Fit\2021-03-30_0006_20210330_Chempot_FS_Fit.ddh5'
#fs_fit_file = "E:\Data\h5py_to_csv test\2021-02-22_0045_2021-02-22_0001_CPP_FS_fit.ddh5"
[VNA, VNA_fstart, VNA_fstop, VNA_fpoints, VNA_avgs, VNA_power] = [pVNA, 6.5e9, 9.5e9, 1601, 30, -30]
[CS, c_start, c_stop, c_points] = [yoko2, -1.2e-3, -3.2e-3, 100]
[Gen, p_start, p_stop, p_points, attn] = [SigGen, -20, 15, 35, 30]

VNA_Settings = [VNA, VNA_fstart, VNA_fstop, VNA_fpoints, VNA_avgs, VNA_power]
CS_Settings = [CS, c_start, c_stop, c_points]
Gen_Settings = [Gen, p_start, p_stop, p_points, attn]

DT = Duffing_Test(DATADIR, name, VNA_Settings, CS_Settings, Gen_Settings, fs_fit_file, mode_kappa = 20e6, mode_side = 10)
#%%Run the msmt
DT.measure(adaptive_VNA_window = True)
#%%Saturation over cw_frequencies
DATADIR = r'E:\Data\Cooldown_20210408\SNAIL_Amps\C1\saturation_over_band'
name = 'SA_C1_0mA_sat_test_gen10.1dBm'

VNA = pVNA 
vna_avgs = 30 
vna_cw_start = pVNA.fstart()
vna_cw_stop = pVNA.fstop()
vna_cw_points = 100
vna_p_start = -43
vna_p_stop = 0 
vna_p_pts = 1000 
vna_att = 30

Gen = SigGen 
gen_freq = SigGen.frequency()
gen_power = SigGen.power()
gen_att = 0

VNA_settings = [VNA, vna_avgs, vna_cw_start, vna_cw_stop, vna_cw_points, vna_p_start, vna_p_stop, vna_p_pts, vna_att]
Gen_settings = [Gen, gen_freq, gen_power, gen_att]

Saturation_Sweep(DATADIR, name, VNA_settings, Gen_settings)
#%%Minimum Gain pwr vs flux

GP_F_dc = GPF_dataclass(
    cwd = r'Z:\Data\SA_2X_B1\tacos',
    filename = f'{yoko2.current()}mA_TACO',
    inst_dict = dict(VNA = pVNA, CS = yoko2, Gen = SigGen),
    bias_current = yoko2.current(),
    #SigGen settings
    gen_att = 0,
    #VNA settings
    vna_att = 30
    )

#%% go to your start point then run this
yoko2.change_current(2.3e-5)
SigGen.frequency(15996691322.3)
SigGen.power(10.45)
GP_F_dc.set_start()
#%% #jump to  a possible stop point
GP_F_dc.goto_stop(gen_freq_offset = 75e6)
#%%tune, then run this
GP_F_dc.set_stop()
#%%check: 
GP_F_dc.goto_start()
#%%
GP_F_dc.renormalize(power = -30)
#%%
GP_F_dc.init_sweep_class()
GP_F_dc.sweep(
              peak_width_minimum = 1,
              vna_avgs = 10,
              stepsize = 0.1,
              block_size = 10,
              limit = 6,
              target_gain = 20,
              threshold = 0.5)
#%%
GP_F_dc.GP_F.plot_powers(gen_freqs, datasets[0], datasets[2], datasets[3])
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
