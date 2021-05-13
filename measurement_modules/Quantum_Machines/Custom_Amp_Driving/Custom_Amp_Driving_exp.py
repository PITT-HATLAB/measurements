# -*- coding: utf-8 -*-
"""
Created on Wed May  5 13:03:50 2021

@author: Ryan Kaufman
"""

#%%
dll_path = r'C:\Users\Hatlab_3\Desktop\RK_Scripts\New_Drivers\HatDrivers\DLL\sc5511a.dll'
sig_gen = SC5
ref_gen = SC9
lo_freq = 12.09e9/2
mod_freq = 50e6
ref_freq = lo_freq + mod_freq
logging.basicConfig(level=logging.INFO)
sig_gen.frequency(lo_freq)
ref_gen.frequency(ref_freq)
config['elements']['amp']['mixInputs']['lo_frequency'] = lo_freq
#%%

#configuration
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
import logging
from hat_utilities.Helper_Functions import adjust_2, load_instrument
from qcodes.instrument.parameter import Parameter
from qcodes.instrument_drivers.tektronix.AWG5014 import Tektronix_AWG5014
from qcodes.instrument import Instrument
from hatdrivers.SignalCore_sc5511a import SignalCore_SC5511A
from hatdrivers.Keysight_MXA_N9020A import Keysight_MXA_N9020A
import numpy as np
import time

from hat_utilities.Quantum_Machines.Custom_Amp_Driving.configuration import config, long_readout_len, SWT_offset
total_pulse_len = long_readout_len+SWT_offset
qmm = QuantumMachinesManager()
qm1 = qmm.open_qm(config)

nAvg = 10000
# Demod_Clock_Cycles
dcc = 10
sample_num = total_pulse_len//(4*dcc)
# print(sample_num)
#%%
simulate = True
with program() as play_pulse_cont:
    Ip = declare(fixed, size = 75)
    Ip_stream = declare_stream()
    RIp = declare(fixed)
    RIp_stream = declare_stream()
    
    Qp = declare(fixed, size = 75)
    Qp_stream = declare_stream()
    RQp = declare(fixed)
    RQp_stream = declare_stream()
    
    Im = declare(fixed, size = 75)
    Im_stream = declare_stream()
    RIm = declare(fixed)
    RIm_stream = declare_stream()
    
    Qm = declare(fixed, size = 75)
    Qm_stream = declare_stream()
    RQm = declare(fixed)
    RQm_stream = declare_stream()
    
    m = declare(int)
    n = declare(int)
    a = 0.2
    with for_(n, 0, n < nAvg, n + 1):
        
        wait(100, "amp")  # wait 100 clock cycles (400ns) for letting resonator relax to vacuum
        play('Plus_Op'*amp(a), 'amp')
        measure(
            "readout_op",
            "readout",
            None,
            demod.sliced("long_integW1", Ip, dcc, "out1"),
            demod.sliced("long_integW2", Qp, dcc, "out1"),
            demod.full("long_integW1", RIp, "out2"),
            demod.full("long_integW2", RQp, "out2"),
        )
        
        wait(100, "amp")
        play('Minus_Op'*amp(a), 'amp')
        measure(
            "readout_op",
            "readout",
            None,
            demod.sliced("long_integW1", Im, dcc, "out1"),
            demod.sliced("long_integW2", Qm, dcc, "out1"),
            demod.full("long_integW1", RIm, "out2"),
            demod.full("long_integW2", RQm, "out2"),
        )
        
        with for_(m, 0, m<sample_num, m+1): 
            save(I[m], I_stream)
            save(Q[m], Q_stream)
        save(I1, I1_stream)
        save(Q1, Q1_stream)
        
    with stream_processing():
        I_stream.buffer(sample_num).save_all("I")
        Q_stream.buffer(sample_num).save_all("Q")
        I1_stream.save_all("I1")
        Q1_stream.save_all("Q1")

if simulate:
    job = qm1.simulate(play_pulse_cont, SimulationConfig(5000))
    samples = job.get_simulated_samples()
    samples.con1.plot()
else:
    job = qm1.execute(play_pulse_cont)
    res = job.result_handles
    res.wait_for_all_values()
    
    Ip_arr = res.Ip.fetch_all()['value']
    Qp_arr = res.Qp.fetch_all()['value']
    
    RIp_arr = res.RIp.fetch_all()['value']
    RQp_arr = res.RQp.fetch_all()['value']
    
    Im_arr = res.Im.fetch_all()['value']
    Qm_arr = res.Qm.fetch_all()['value']
    
    RIm_arr = res.RIm.fetch_all()['value']
    RQm_arr = res.RQm.fetch_all()['value']
#%%
from hat_utilities.signal_processing.Pulse_Processing import phase_correction
import matplotlib.pyplot as plt
from plottr.data import datadict_storage as dds, datadict as dd

I_c_p, Q_c_p, r_I_p, r_Q_p = phase_correction(Ip_arr, Qp_arr, np.repeat(RIp_arr, 75).reshape(nAvg,75), np.repeat(RQp_arr, 75).reshape(nAvg, 75))
I_c_m, Q_c_m, r_I_m, r_Q_m = phase_correction(Im_arr, Qm_arr, np.repeat(RIm_arr, 75).reshape(nAvg,75), np.repeat(RQm_arr, 75).reshape(nAvg, 75))

I_c_p_avg = np.average(I_c_p, axis = 0)
Q_c_p_avg = np.average(Q_c_p, axis = 0)

fig = plt.figure()
ax1 = fig.add_subplot(221)
ax1.set_aspect(1)
ax2 = fig.add_subplot(222)
ax2.set_aspect(1)
ax3 = fig.add_subplot(223)
ax4 = fig.add_subplot(224)
for i in range(np.size(I_c_p_avg)-1): 
    ax1.plot(I_c_p_avg[i:i+2], Q_c_p_avg[i:i+2], color=plt.cm.jet(i/np.size(I_c_p_avg)))
    ax2.plot(r_I_p[i:i+2], r_Q_p[i:i+2])
ax3.plot(I_c_p_avg, label = "I")
ax3.plot(Q_c_p_avg, label = "Q")

#load everything into a datadict and save the file
datadict = dd.DataDict(
    time = dict(unit = 'ns'),
    record_num = dict(unit = 'num'),
    I_plus = dict(axes=['record_num', 'time' ], unit = 'DAC'), 
    Q_plus = dict(axes=['record_num', 'time' ], unit = 'DAC'),
    I_minus = dict(axes=['record_num', 'time' ], unit = 'DAC'),
    Q_minus = dict(axes=['record_num', 'time' ], unit = 'DAC')
)

DATADIR = r'E:\Data\Cooldown_20210408\SNAIL_Amps\C1\Hakan_data\Quantum_Machines_Tests'
filename = 'TEST_01'
with dds.DDH5Writer(DATADIR, datadict, name=filename) as writer:
    s = np.shape(I_c_p)
    time_step = dcc*4 #ns
    writer.add_data(
            record_num = np.repeat(np.arange(s[0]), s[1]),
            time = np.tile(np.arange(int(s[1]))*time_step, s[0]),
            I_plus = I_c_p.flatten(),
            Q_plus = Q_c_p.flatten(),
            I_minus = I_c_m.flatten(),
            Q_minus = Q_c_m.flatten()
            )
    
    