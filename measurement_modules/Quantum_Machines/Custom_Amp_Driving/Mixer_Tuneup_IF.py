# -*- coding: utf-8 -*-
"""
Created on Thu May  6 10:13:56 2021

@author: Hatlab_3
"""

#configuration
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
import logging
from hat_utilities.Helper_Functions import adjust_2
from qcodes.instrument.parameter import Parameter
from qcodes.instrument_drivers.tektronix.AWG5014 import Tektronix_AWG5014
from hatdrivers.SignalCore_sc5511a import SignalCore_SC5511A
from hatdrivers.Keysight_MXA_N9020A import Keysight_MXA_N9020A
from qcodes import Station
import numpy as np
import time
#%%
sig_gen = SC5
ref_gen = SC9
#%%
lo_freq = 12.09e9/2
mod_freq = 50e6
ref_freq = lo_freq + mod_freq

logging.basicConfig(level=logging.INFO)

sig_gen.frequency(lo_freq)
ref_gen.frequency(ref_freq)
#%%
from hat_utilities.Quantum_Machines.Custom_Amp_Driving.configuration import config, pulse_len

config['elements']['amp']['mixInputs']['lo_frequency'] = lo_freq
qmm = QuantumMachinesManager()
qm1 = qmm.open_qm(config)

I_par = Parameter("I_offset", 
                  set_cmd= lambda a : qm1.set_output_dc_offset_by_element('amp', 'I', a), 
                  get_cmd = lambda: qm1.get_output_dc_offset_by_element('amp', 'I'), 
                  unit = 'V')

Q_par = Parameter("Q_offset", 
                  set_cmd= lambda a : qm1.set_output_dc_offset_by_element('amp', 'Q', a), 
                  get_cmd = lambda: qm1.get_output_dc_offset_by_element('amp', 'Q'), 
                  unit = 'V')
#%%
simulate = False
with program() as play_pulse_cont:
    with infinite_loop_():
        play("I_only", "amp")

if simulate:
    job = qm1.simulate(play_pulse_cont, SimulationConfig(1000))
    samples = job.get_simulated_samples()
    samples.con1.plot()
else:
    job = qm1.execute(play_pulse_cont)
    
#%%
adjust_2([Q_par, I_par], [0.01, 0.01])