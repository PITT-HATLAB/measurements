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
from measurement_modules.VNA.Simple_Sweeps import Spec_frequency_sweep, Spec_power_sweep

from plottr.data import datadict_storage as dds, datadict as dd
from datetime import datetime
from plottr.apps.autoplot import autoplotDDH5, script, main
from dataclasses import dataclass

#%% frequency sweep
DATADIR = 'Z:\Data\SA_2X_B1\Hakan\Amplifier_idler_sweeps'
name = 'idler_SC_10dBm' 

CXA_fcenter = 7.81518e9
CXA_fspan = 30e6
CXA_avgs = 100

Gen = SC4
fstart = 7.81518e9
fstop = 7.81518e9+10e6
fpoints = 100

CXA_settings = [CXA, CXA_fcenter, CXA_fspan, CXA_avgs]
Gen_settings = [Gen, fstart, fstop, fpoints]
Spec_frequency_sweep(DATADIR, name, CXA_settings, Gen_settings)

#%% power sweep
DATADIR = 'Z:\Data\00_Calibrations\RT Equipment calibrations\XMW_interferometer_2'
name = 'IR_mixer signal_power_vs_sid' 

CXA_fcenter = 50e6
CXA_fspan = 30e6
CXA_avgs = 100
SC4.frequency(7.5e9)
Gen = SC4
pstart = -18
pstop = 10
ppoints = 100

CXA_settings = [CXA, CXA_fcenter, CXA_fspan, CXA_avgs]
Gen_settings = [Gen, pstart, pstop, ppoints]
Spec_power_sweep(DATADIR, name, CXA_settings, Gen_settings)
