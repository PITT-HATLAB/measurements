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
from measurement_modules.VNA.Simple_Sweeps import Flux_Sweep, Frequency_Sweep, Power_Sweep, saturation_gen_power_sweep
from measurement_modules.Adaptive_Sweeps.Gain_Power_vs_Flux import Gain_Power_vs_Flux

from measurement_modules.dataclasses import GPF_dataclass

from plottr.data import datadict_storage as dds, datadict as dd
from datetime import datetime
from plottr.apps.autoplot import autoplotDDH5, script, main
from dataclasses import dataclass
#%%
# from measurement_modules.remote_module import controller_adjust
#%% fluxsweep
from measurement_modules.VNA.Simple_Sweeps import Flux_Sweep
DATADIR = r'Z:\Data\SH6F1_1141\fluxsweep'
name='half_quanta_A_mode_-73dBm_fine'
#instruments
VNA = pVNA
# CS = YROKO1
CS = yoko2
#starting parameters
c_start = 0e-3
c_stop = 0.1e-3
c_points = 300

VNA_fcenter, VNA_fspan, VNA_fpoints, VNA_avgs = pVNA.fcenter(), pVNA.fspan(), 1500, 10
VNA_settings = [VNA, VNA_fcenter, VNA_fspan, VNA_fpoints, VNA_avgs]

CS_settings = [CS, c_start, c_stop, c_points]
print(f"Estimated time: {VNA.sweep_time()*VNA_avgs*c_points/60} minutes")
#%%
Flux_Sweep(DATADIR, name, VNA_settings, CS_settings, ramp_rate = None)

#%% Frequency Sweep
DATADIR = r'Z:\Data\SA_2X_B1\Hakan\Amplifier_idler_sweeps'

#instruments
VNA = pVNA
Gen = SC4
#starting parameters
pows = [SC4.power()]
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
from measurement_modules.VNA.Simple_Sweeps import Power_Sweep
DATADIR = r'Z:\Data\SH6F1_1141\gp7\gen_power_sweep'
#instruments
VNA = pVNA
pVNA.rfout(1)
Gen = SigGen
#starting parameters
VNA_fcenter, VNA_fspan, VNA_fpoints = SigGen.frequency()/2, 100e6, 2000
VNA_avgs = 30
p_start, p_stop, p_points = -10, 5, 41 #wi!h -40dB on RT atten
# p_start, p_stop, p_points = -20, 20, 41 #with 0 dB on RT atten
# name = f'vna_trace_vs_vna_power_40dBatten_{temp}mK'
name = f'gain_vs_gen_power_10dBatten'
SigGen.output_status(1)
VNA_settings = [VNA, VNA_fcenter, VNA_fspan, VNA_fpoints, VNA_avgs]
Gen_settings = [SigGen, p_start, p_stop, p_points]
Power_Sweep(DATADIR, name, VNA_settings, Gen_settings)
#%% Duffing Test
#v2: uses a file with a pre-fitted fluxsweep to help out
from measurement_modules.Adaptive_Sweeps.Duffing_Test import Duffing_Test
DATADIR = r'Z:\Data\SH6F1_1141\duffing'
name = "SH6F1_SNAIL_Duffing"
fs_fit_file = r'Z:/Data/SH6F1_1141/fluxsweep/fits/2021-11-29/2021-11-29_0004_SH_6F1_A_mode_full_fit/2021-11-29_0004_SH_6F1_A_mode_full_fit.ddh5'
[VNA, VNA_fstart, VNA_fstop, VNA_fpoints, VNA_avgs, VNA_power] = [pVNA, 7.5e9, 7.8e9, 1500, 10, -30]
#-0.04457831325301205 mA to  0.05180722891566265 mA
[CS, c_start, c_stop, c_points] = [yoko2, 0.089e-3, 0.093e-3, 15]
[Gen, p_start, p_stop, p_points, attn] = [SigGen, -10.0, 20, 40, 40]

VNA_Settings = [VNA, VNA_fstart, VNA_fstop, VNA_fpoints, VNA_avgs, VNA_power]
CS_Settings = [CS, c_start, c_stop, c_points]
Gen_Settings = [Gen, p_start, p_stop, p_points, attn]

DT = Duffing_Test(DATADIR, name, VNA_Settings, CS_Settings, Gen_Settings, fs_fit_file, mode_kappa = 35e6, mode_side = 5, ramp_rate = None)
DT.preview()
#%%Run the msmt
DT.measure(adaptive_VNA_window = True)
#%%Saturation over cw_frequencies
from measurement_modules.VNA.Simple_Sweeps import Saturation_freq_Sweep
DATADIR = r'Z:\Data\SA_3C1_3221\Pulse_data_7GHz\saturation_over_CW_freqs'
name = 'SA_C1_3221_sat_test_gen-21dBm_total'

VNA = pVNA 
vna_avgs = 30 
vna_cw_start = pVNA.fstart()
vna_cw_stop = pVNA.fstop()
vna_cw_points = 30
vna_p_start = -43
vna_p_stop = -10
vna_p_pts = 1000 
vna_att = 40

Gen = SigGen 
gen_freq = SigGen.frequency()
gen_power = SigGen.power()
gen_att = 10

VNA_settings = [VNA, vna_avgs, vna_cw_start, vna_cw_stop, vna_cw_points, vna_p_start, vna_p_stop, vna_p_pts, vna_att]
Gen_settings = [Gen, gen_freq, gen_power, gen_att]

Saturation_freq_Sweep(DATADIR, name, VNA_settings, Gen_settings)


#%%Saturation vs generator power
DATADIR = r'Z:\Data\Hakan\SH_5B1_SS_Gain_6.064GHz\vna_saturation_sweep'
name = 'SH_5B1_saturation_sweep_offres_+500kHz'

VNA = pVNA 
vna_avgs = 30 
vna_cw_freq = 6.06464e9+500e3
gen_power_points = 10
vna_p_start = -43
vna_p_stop = 0 
vna_p_pts = 1000 
vna_att = 50

Gen = SigGen 
gen_freq = 12131300000.0
gen_power_start = -7
gen_power_stop = -6 
gen_power_points = 5
gen_att = 20

VNA_settings = [VNA, vna_cw_freq, vna_avgs, vna_p_start, vna_p_stop, vna_p_pts, vna_att]
Gen_settings = [Gen, gen_freq, gen_power_start, gen_power_stop, gen_power_points, gen_att]

saturation_gen_power_sweep(DATADIR, name, VNA_settings, Gen_settings)
#%% Pump_FS
from measurement_modules.Adaptive_Sweeps.Pump_flux_scanning import PS_dc, Pump_flux_scan
dc = PS_dc(
    datadir = r'Z:\Data\SH_5B1_4141\pump_scanning', 
    name = 'A_mode_10dB_att',
    VNA = pVNA,
    VNA_pstart = -43,
    VNA_pstop =  -10,
    VNA_ppoints = 500,
    VNA_avgs = 30,
    VNA_att = 50,
    VNA_detuning = 0.1e6,
    
    Gen = SigGen,
    Gen_pstart = -11,
    Gen_pstop =  19,
    Gen_ppoints = 31,
    Gen_detuning = 0,
    Gen_att = 0,
    
    CS = YROKO1,
    c_start = -3e-3,
    c_stop = -5e-3,
    c_points = 20,
    c_ramp_rate = None,
    
    fs_fit_path = r'Z:/Data/SH_5B1_4141/fluxsweep/A_mode/fits/2021-09-22/2021-09-22_0001_SH_5B1_YROKO_fit_A_mode/2021-09-22_0001_SH_5B1_YROKO_fit_A_mode.ddh5',
    )

#%%
dc.configure()
dc.ETA()
dc.preview()
#%% send into measurement class
PFS = Pump_flux_scan(dc)
 #%%
PFS.measure()

