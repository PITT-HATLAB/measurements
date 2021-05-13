# -*- coding: utf-8 -*-
"""
Created on Wed May  5 13:03:50 2021

@author: Ryan Kaufman
"""

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
#%%
from hat_utilities.Quantum_Machines.Custom_Amp_Driving.configuration import config


config['elements']['amp']['mixInputs']['lo_frequency'] = lo_freq
qmm = QuantumMachinesManager()
qm1 = qmm.open_qm(config)

nAvg = 10000

simulate = True
with program() as play_pulse_cont:
    Ip = declare(fixed, size = 75)
    Ip_stream = declare_stream()
    I1p = declare(fixed)
    I1p_stream = declare_stream()
    
    Qp = declare(fixed, size = 75)
    Qp_stream = declare_stream()
    Q1p = declare(fixed)
    Q1p_stream = declare_stream()
    
    Im = declare(fixed, size = 75)
    Im_stream = declare_stream()
    I1m = declare(fixed)
    I1m_stream = declare_stream()
    
    Qm = declare(fixed, size = 75)
    Qm_stream = declare_stream()
    Q1m = declare(fixed)
    Q1m_stream = declare_stream()
    
    adc_data = declare_stream(adc_trace=True)
    # with infinite_loop_():
    #     play("Plus_Op"*amp(0.1), "amp")
    m = declare(int)
        
    n = declare(int)
    with for_(n, 0, n < nAvg, n + 1):
        # with for_(f, fMin, f < fMax, f + df):
        wait(
            100, "amp"
        )  # wait 100 clock cycles (400ns) for letting resonator relax to vacuum

        # update_frequency("qubit", f)
        play('Plus_Op'*amp(0.4), 'amp')
        measure(
            "readout_op",
            "readout",
            adc_data,
            demod.sliced("long_integW1", Ip, 10, "out1"),
            demod.sliced("long_integW2", Qp, 10, "out1"),
            demod.full("long_integW1", I1p, "out2"),
            demod.full("long_integW2", Q1p, "out2")
        )
        play('Minus_Op'*amp(0.4), 'amp')
        measure(
            "readout_op",
            "readout",
            adc_data,
            demod.sliced("long_integW1", Im, 10, "out1"),
            demod.sliced("long_integW2", Qm, 10, "out1"),
            demod.full("long_integW1", I1m, "out2"),
            demod.full("long_integW2", Q1m, "out2")
        )
        with for_(m, 0, m<75, m+1): 
            save(Ip[m], I_stream)
            save(Qp[m], Q_stream)
            save(Im[m], I_stream)
            save(Qm[m], Q_stream)
        save(I1p, I1_stream)
        save(Q1p, Q1_stream)
        save(I1m, I1_stream)
        save(Q1m, Q1_stream)
        
    with stream_processing():
        Ip_stream.buffer(75).save_all("Ip")
        Qp_stream.buffer(75).save_all("Qp")
        I1p_stream.save_all("I1p")
        Q1p_stream.save_all("Q1p")
        Im_stream.buffer(75).save_all("Im")
        Qm_stream.buffer(75).save_all("Qm")
        I1m_stream.save_all("I1m")
        Q1m_stream.save_all("Q1m")
        # adc_data.input1().save_all('adc1')
        # adc_data.input2().save_all('adc2')

if simulate:
    job = qm1.simulate(play_pulse_cont, SimulationConfig(500))
    samples = job.get_simulated_samples()
    #TODO: Can I get units in Volts here?
    samples.con1.plot()
else:
    job = qm1.execute(play_pulse_cont)
    res = job.result_handles
    res.wait_for_all_values()
    Ip_arr = res.Ip.fetch_all()['value']
    Qp_arr = res.Qp.fetch_all()['value']
    
    I1p_arr = res.I1p.fetch_all()['value']
    Q1p_arr = res.Q1p.fetch_all()['value']
    
    Im_arr = res.Im.fetch_all()['value']
    Qm_arr = res.Qm.fetch_all()['value']
    
    I1m_arr = res.I1m.fetch_all()['value']
    Q1m_arr = res.Q1m.fetch_all()['value']
    
#%%
from hat_utilities.signal_processing.Pulse_Processing import phase_correction
import matplotlib.pyplot as plt

I_c, Q_c, r_I, r_Q = phase_correction(I_arr, Q_arr, np.repeat(I1_arr, 75).reshape(nAvg,75), np.repeat(Q1_arr, 75).reshape(nAvg, 75))

I_c_avg = np.average(I_c, axis = 0)
Q_c_avg = np.average(Q_c, axis = 0)

fig = plt.figure()
ax1 = fig.add_subplot(221)
ax1.set_aspect(1)
ax2 = fig.add_subplot(222)
ax2.set_aspect(1)
ax3 = fig.add_subplot(223)
ax4 = fig.add_subplot(224)
for i in range(np.size(I_c_avg)-1): 
    ax1.plot(I_c_avg[i:i+2], Q_c_avg[i:i+2], color=plt.cm.jet(i/np.size(I_c_avg)))
    ax2.plot(r_I[i:i+2], r_Q[i:i+2])
ax3.plot(I_c_avg, label = "I")
ax3.plot(Q_c_avg, label = "Q")


    
    