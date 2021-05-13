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

SC5.frequency(lo_freq)
SC9.frequency(ref_freq)
#%%
from hat_utilities.Quantum_Machines.Mixer_Tuneup.configuration import config, pulse_len
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
        play("Both_off", "amp")
        

if simulate:
    job = qm1.simulate(play_pulse_cont, SimulationConfig(1000))
    samples = job.get_simulated_samples()
    samples.con1.plot()
else:
    job = qm1.execute(play_pulse_cont)
#%%
# adjust_2([I_par, Q_par], [0.01, 0.01])
#%%
# adjust_2([I_par, Q_par], [0.001, 0.001])
#%%
job.halt()
#print offsets
offsets = I_par(), Q_par()
print(f'I_offset = {I_par()}\nQ_offset = {Q_par()}')
#%%amplitude correction
#turning on channel 1
#TODO: I need a way to adjust channel amplitudes on the fly

with program() as play_pulse_cont:
    with infinite_loop_():
        play("I_only", "amp")
job = qm1.execute(play_pulse_cont)

time.sleep(0.5)
I_pow = CXA.plot_trace(avgnum = 500)
job.halt()
with program() as play_pulse_cont:
    with infinite_loop_():
        play("Q_only", "amp")
job = qm1.execute(play_pulse_cont)
time.sleep(0.5)
Q_pow = CXA.plot_trace(avgnum = 500)
job.halt()
#calculate amplitude imbalance
def amplitude_correction(ch1_amp, ch2_amp, perfect_channel = 1): 
    '''
    this function will do the log linear conversion from dbm 
    to voltage and do the division to determine the amplitude correction factor
    '''
    perfect_channel -=1 #change to array notation
    channels = np.array([ch1_amp, ch2_amp])
    linear_power = np.power(np.array([10,10]), channels/20)*1e-3 #dB(milliwatt)
    voltage = np.sqrt(linear_power)
    correction_factor = voltage[perfect_channel]/voltage[(perfect_channel+1) % 2]
    return correction_factor

ch2_correction = amplitude_correction(I_pow,Q_pow, perfect_channel = 1)    
print(f"Ch2_correction: {ch2_correction}")
#add a pulse type that has the corrected amplitude in order to get phase correction
config['waveforms']['const_wf_corr'] = {"type": "constant", "sample": 0.1*ch2_correction}
#create another pulse type, and add an operation to amp to include it

#%%Get phase correction
#create a new pulse and new operation in amp that uses it
config['pulses']['All_on_corrected'] = {"operation": "control",
                                       "length": pulse_len,
                                       "waveforms": {"I": "const_wf", "Q": "const_wf_corr"},
                                       "digital_marker": "ON"
                                       }

config['elements']['amp']['operations']['Both_on_corrected'] = "All_on_corrected"

#%%

qm1 = qmm.open_qm(config) #TODO: Is there an easier way to refresh this? It seems like overkill
with program() as play_pulse_cont:
    with infinite_loop_():
        play("Both_on_corrected", "amp")
job = qm1.execute(play_pulse_cont)
time.sleep(0.5)
combined_pow = CXA.plot_trace(avgnum = 500)
#when you're done, run this cell to print a summary: 
print(f"Ch1 by itself: {I_pow} dBm")
print(f"Combined Power: {combined_pow} dBm")
print(f"Difference In Power: {combined_pow-I_pow} dBm")
linear_ratio = np.sqrt(np.power(10, (combined_pow-I_pow)/10))
print(f"Difference In Power (linear voltage ratio): {linear_ratio}")

def calculate_phase_offset(linear_ratio): 
    phi_offset = -np.arccos(-0.5*np.sqrt(-linear_ratio**2*(-4+linear_ratio**2)))
    #we want the smallest change, so we can check this value +-2pi
    phi_array = [phi_offset, phi_offset+np.pi, phi_offset-np.pi]
    return phi_array[np.abs(phi_array).argmin()]

phase_offset = calculate_phase_offset(linear_ratio)
print(f"Phase Offset: {phase_offset} rad ({phase_offset*360/(2*np.pi)} deg)")
#%%
#print a total summary: 
print(f"DC Offsets: {offsets}")
print(f"Ch2 voltage correction factor: {ch2_correction}")
print(f"Phase Offset: {phase_offset}")