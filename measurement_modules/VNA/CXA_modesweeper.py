# -*- coding: utf-8 -*-
"""
Created on Fri Aug 13 17:05:12 2021

@author: Hatlab_3
"""
import easygui 
import matplotlib.pyplot as plt
import numpy as np 
import h5py
import datetime as dt
from instrument_drivers.meta_instruments import Modes
from measurement_modules.VNA.Simple_Sweeps import Spec_frequency_sweep, Spec_power_sweep, Two_Tone

from plottr.data import datadict_storage as dds, datadict as dd
from datetime import datetime
from plottr.apps.autoplot import autoplotDDH5, script, main
from dataclasses import dataclass



    #%% frequency sweep
if __name__ == '__main__':    
    
    DATADIR = 'Z:\Data\SA_2X_B1\Hakan\Amplifier_idler_sweeps'
    name = 'idler_SC_10dBm' 
    
    CXA_fcenter = 6015000000.0
    CXA_fspan = 150e6
    CXA_avgs = 100
    
    Gen = SC4
    fstart = 7.81518e9
    fstop = 7.81518e9+10e6
    fpoints = 100
    
    CXA_settings = [CXA, CXA_fcenter, CXA_fspan, CXA_avgs]
    Gen_settings = [Gen, fstart, fstop, fpoints]
    Spec_frequency_sweep(DATADIR, name, CXA_settings, Gen_settings)

    #%% power sweep
    
    
if __name__ == '__main__': 
    
    DATADIR = r'Z:\Data\00_Calibrations\RT Equipment calibrations\XMW_interferometer_rev2_qubit_drive'
    name = r'Qubit_drive_module_LO_pwr_vs_sideband_with_splitter_4' 
    
    CXA_fcenter = 6015000000.0
    CXA_fspan = 150e6
    CXA_avgs = 100
    
    SC4.frequency(6015000000.0)
    Gen = SC4
    pstart = -5
    pstop = 15
    ppoints = 41
    
    CXA_settings = [CXA, CXA_fcenter, CXA_fspan, CXA_avgs]
    Gen_settings = [Gen, pstart, pstop, ppoints]
    Spec_power_sweep(DATADIR, name, CXA_settings, Gen_settings)
    

    #%% 2-Tone test for IIP3
    
if __name__ == '__main__':
    
    DATADIR = r'Z:\Data\Hakan\SH_5B1_SS_Gain_6.064GHz\IIP3_SA_sweep'
    name = r'6.064GHz_20dB_Gain_IIP3_test'
    
    CXA_fcenter = 6064000000.0
    CXA_fspan = 10e3
    CXA_avgs = 5
    f1 = CXA_fcenter+1e3
    f2 = CXA_fcenter-1e3
    SC4.frequency(CXA_fcenter+1e3)
    SC9.frequency(CXA_fcenter-1e3)
    pstart = -20
    pstop = -10
    ppoints = 41
    
    CXA_settings = [CXA, CXA_fcenter, CXA_fspan, CXA_avgs]
    Gen_settings = [SC4, SC9, f1, f2, pstart, pstop, ppoints]
    
    Two_Tone(DATADIR, name, CXA_settings, Gen_settings)
