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
from hat_utilities.Helper_Functions import adjust_2
from qcodes.instrument.parameter import Parameter
from qcodes.instrument_drivers.tektronix.AWG5014 import Tektronix_AWG5014
from hatdrivers.SignalCore_sc5511a import SignalCore_SC5511A
from hatdrivers.Keysight_MXA_N9020A import Keysight_MXA_N9020A
import numpy as np
import time
#%%
dll_path = r'C:\Users\Hatlab_3\Desktop\RK_Scripts\New_Drivers\HatDrivers\DLL\sc5511a.dll'
SC5 = SignalCore_SC5511A('SigCore5', serial_number = '10001851', debug = False)
SC9 = SignalCore_SC5511A('SigCore9', serial_number = '1000190E', debug = False)
CXA = Keysight_MXA_N9020A("CXA", address = 'TCPIP0::169.254.110.116::INSTR')
lo_freq = 12.09e9/2
mod_freq = 50e6
ref_freq = lo_freq + mod_freq
logging.basicConfig(level=logging.INFO)
#%%
from hat_utilities.Quantum_Machines.Custom_Amp_Driving.configuration import config

SC5.frequency(lo_freq)
SC9.frequency(ref_freq)
config['elements']['amp']['mixInputs']['lo_frequency'] = lo_freq
qmm = QuantumMachinesManager()
qm1 = qmm.open_qm(config)

nAvg = 10000

simulate = False
with program() as play_pulse_cont:
    I = declare(fixed, size = 75)
    I_stream = declare_stream()
    I1 = declare(fixed)
    I1_stream = declare_stream()
    
    Q = declare(fixed, size = 75)
    Q_stream = declare_stream()
    Q1 = declare(fixed)
    Q1_stream = declare_stream()
    
    # with infinite_loop_():
    #     play("Plus_Op"*amp(0.1), "amp")
    m = declare(int)
        
    n = declare(int)
    f = declare(int)
    a = declare(fixed)
    p_ext = declare(int)
    with for_(n, 0, n < nAvg, n + 1):
        with for_(p_ext, 0, p_ext<10, p_ext+1):  # Need to add a buffer(10) at the end of the stream processing
            #pause()
            #wait_for_trigger()
            play('dig_out', 'external_pwr')
            wait(10e6, "amp")
            with for_(f, fMin, f < fMax, f + df):  # 10e6 < f <30e6
                update_frequency("amp", f)
                update_frequency("readout", f + 50e6)
                with for_(a, aMin, a < aMax + da/2, a + da):
                    
                    wait(
                        100, "amp"
                    )  # wait 100 clock cycles (400ns) for letting resonator relax to vacuum
            
                    # update_frequency("qubit", f)
                    play('Plus_Op'*amp(a), 'amp')
                    measure(
                        "readout_op",
                        "readout",
                        None,
                        demod.sliced("long_integW1", I, 10, "out1"),
                        demod.sliced("long_integW2", Q, 10, "out1"),
                        demod.full("long_integW1", I1, "out2"),
                        demod.full("long_integW2", Q1, "out2"),
                    )
                    with for_(m, 0, m<75, m+1): 
                        save(I[m], I_stream)
                        save(Q[m], Q_stream)
                    save(I1, I1_stream)
                    save(Q1, Q1_stream)
        
    with stream_processing():
        I_stream.buffer(75).buffer(num_a).buffer(num_f).save_all("I")
        Q_stream.buffer(75).buffer(num_a).buffer(num_f).save_all("Q")
        I1_stream.buffer(num_a).buffer(num_f).save_all("I1")
        Q1_stream.buffer(num_a).buffer(num_f).save_all("Q1")

if simulate:
    job = qm1.simulate(play_pulse_cont, SimulationConfig(500))
    samples = job.get_simulated_samples()
    #TODO: Can I get units in Volts here?
    samples.con1.plot()
else:
    job = qm1.execute(play_pulse_cont)
    res = job.result_handles
    res.wait_for_all_values()
    I_arr = res.I.fetch_all()['value']
    Q_arr = res.Q.fetch_all()['value']
    
    I1_arr = res.I1.fetch_all()['value']
    Q1_arr = res.Q1.fetch_all()['value']
    
#%%
from hat_utilities.signal_processing.Pulse_Processing import phase_correction

outs = phase_correction(I_arr, Q_arr, np.repeat(I1_arr, 75).reshape(10000, 75), np.repeat(Q1_arr, 75).reshape(10000, 75))
    