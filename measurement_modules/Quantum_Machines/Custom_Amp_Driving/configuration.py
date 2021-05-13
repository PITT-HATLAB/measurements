# -*- coding: utf-8 -*-
"""
Created on Wed May  5 13:03:50 2021

@author: Ryan Kaufman
"""
import numpy as np
import matplotlib.pyplot as plt
long_readout_len = 3000
SWT_offset = 100
pulse_len = 100
amp_IF = 0e6
amp_LO = 6045000000
I_offset = -0.095
Q_offset = -0.09
ch2_correction = 1.0637067110144105
phase_offset = 0.028958647982968877
# I_offset = 0
# Q_offset = 0

sim_filepath1 = r'H:\RK\Transfer\kappa_2MHz_Chi_2MHz_-det_plus_ringdown.csv'
sim_filepath2 = r'H:\RK\Transfer\kappa_2MHz_Chi_2MHz_+det_plus_ringdown.csv'

def phase_shifter(I_data, Q_data, phase_offset, plot = False): 
    '''
    This will take I as the perfect channel and some phase offset sin(theta_imbalance) offsetting Q towards I
    Assuming I and Q to be unit magnitude
    '''
    
    Q_res = Q_data
    I_res = (I_data-np.sin(phase_offset)*Q_data)/np.cos(phase_offset)
    if plot: 
        plt.figure()
        plt.title("Before phase correction: ")
        plt.plot(I_data)
        plt.plot(Q_data)
        plt.figure()
        plt.title("After phase correction: ")
        plt.plot(I_res)
        plt.plot(Q_res)

    return I_res

#make the custom function first
import pandas as pd
def cavity_response_Q_uncorrected(amp, filepath): 
    imag = pd.read_csv(filepath, usecols = ['imag']).to_numpy().T[0]
    return imag*amp
    
def cavity_response_I_uncorrected(amp, filepath): 
    real = pd.read_csv(filepath, usecols = ['real']).to_numpy().T[0]
    return real*amp
    
def cavity_response_with_correction(amp, filepath, SR, npts, amp_corr = 1, phase_offset = 0, beginning_buffer = 100):
    def cavity_response_Q_bb(amp, filepath, SR, npts, buffer = beginning_buffer):
        buffer = np.zeros(buffer)
        imag = np.append(buffer, pd.read_csv(filepath, usecols = ['imag']).to_numpy().T[0])
        return imag*amp
    
    def cavity_response_I_bb(amp, filepath, SR, npts, amp_corr = amp_corr, phase_corr = phase_offset, buffer = beginning_buffer):
        buffer = np.zeros(buffer)
        real = np.append(buffer, pd.read_csv(filepath, usecols = ['real']).to_numpy().T[0])
        scaled = real*amp
        amplitude_corrected = scaled*amp_corr
        Q_data = np.append(buffer, pd.read_csv(filepath, usecols = ['imag']).to_numpy().T[0]*amp)
        phase_corrected = phase_shifter(amplitude_corrected, Q_data, phase_corr)
        return phase_corrected
    
    return cavity_response_I_bb, cavity_response_Q_bb

Ifunc_corrected, Qfunc_corrected = cavity_response_with_correction(1, sim_filepath1, 1e9, 1000, amp_corr = ch2_correction, phase_offset = phase_offset, buffer = SWT_offset)
I0_c = Ifunc_corrected(1, sim_filepath1, 1e9, 3000)
Q0_c = Qfunc_corrected(1, sim_filepath1, 1e9, 3000)
I1_c = Ifunc_corrected(1, sim_filepath2, 1e9, 3000)
Q1_c = Qfunc_corrected(1, sim_filepath2, 1e9, 3000)

#%%

def IQ_imbalance_correction(g, phi):
    c = np.cos(phi)
    s = np.sin(phi)
    N = 1 / ((1 - g ** 2) * (2 * c ** 2 - 1))
    return [float(N * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]]


config = {
    "version": 1,
    "controllers": {
        "con1": {
            "type": "opx1",
            "analog_outputs": {
                1: {"offset": +I_offset},  # I
                2: {"offset": +Q_offset},  # Q
            },
            "digital_outputs": {
                1: {},
            },
            "analog_inputs": {
                1: {"offset":0},  # I
                2: {"offset":0},  # Q
                }
        }
    },
    "elements": {
        "amp": {
            "mixInputs": {
                "I": ("con1", 1),
                "Q": ("con1", 2),
                "lo_frequency": amp_LO,
                "mixer": "mixer_amp",
            },
            'digitalInputs': {
                'digital_input1': {
                    'port': ('con1', 1),
                    'delay': 0,
                    'buffer': 0,
                },
            },
            "intermediate_frequency": amp_IF,
            "operations": {
                "Both_on": "All_on",
                "I_only": "I_on",
                "Q_only": "Q_on",
                "Both_off": "All_off",
                "Plus_Op": "Plus_Pulse",
                "Minus_Op": "Minus_Pulse"
            },
        },
        "readout":{
            "mixInputs": {
                "I": ("con1", 1),
                "Q": ("con1", 2),
                "lo_frequency": amp_LO,
                "mixer": "mixer_amp",
            },
            "time_of_flight": 80,
            "smearing": 0,
            "outputs": {
                'out1': ('con1', 1),
                'out2': ('con1', 2),
                },
            "intermediate_frequency": 50e6,
            "operations": {
                "readout_op": "readout_pulse",
            },
        },
    },
    "pulses": {
        "All_on": {
            "operation": "control",
            "length": pulse_len,
            "waveforms": {"I": "const_wf", "Q": "const_wf"},
            "digital_marker": "ON"
        },
        "I_on": {
            "operation": "control",
            "length": pulse_len,
            "waveforms": {"I": "const_wf", "Q": "const_wf_off"},
            "digital_marker": "ON"
        },
        "Q_on": {
            "operation": "control",
            "length": pulse_len,
            "waveforms": {"I": "const_wf_off", "Q": "const_wf"},
            "digital_marker": "ON"
        },
        "All_off": {
            "operation": "control",
            "length": pulse_len,
            "waveforms": {"I": "const_wf_off", "Q": "const_wf_off"},
            "digital_marker": "ON"
        },
        "Plus_Pulse": {
            "operation":"control",
            "length": 3100,
            "waveforms": {"I": "I_plus", "Q":"Q_plus"},
            "digital_marker": "ON",
        },
        "Minus_Pulse": {
            "operation":"control",
            "length": 3100,
            "waveforms": {"I": "I_minus", "Q":"Q_minus"},
            "digital_marker": "ON",
        },
        "readout_pulse": {
            "operation":"measurement",
            "length": 3100,
            "waveforms": {"I": "const_wf_off", "Q":"const_wf_off"},
            "digital_marker": "ON",
            'integration_weights': {
                'long_integW1': 'long_integW1',
                'long_integW2': 'long_integW2',
                }
        }
    },
    "waveforms": {
        "const_wf_off": {"type": "constant", "sample": 0},
        "const_wf": {"type": "constant", "sample": 0.4},
        "I_plus": {"type": "arbitrary", "samples": I0_c}, 
        "Q_plus": {"type": "arbitrary", "samples": Q0_c}, 
        "I_minus": {"type": "arbitrary", "samples": I1_c}, 
        "Q_minus": {"type": "arbitrary", "samples": Q1_c}
    },
    "digital_waveforms": {
        "ON": {"samples": [(1, 0)]},
        "trig": {"samples": [(1, 100)]},
        "stutter": {"samples": [(1, 100), (0, 200), (1, 76), (0, 10), (1, 0)]},
    },
    'integration_weights': {

        'long_integW1': {
            'cosine': [1.0] * int(long_readout_len / 4),
            'sine': [0.0] * int(long_readout_len / 4)
        },

        'long_integW2': {
            'cosine': [0.0] * int(long_readout_len / 4),
            'sine': [1.0] * int(long_readout_len / 4)
        },

    },
    "mixers": {
        "mixer_amp": [
            {
                "intermediate_frequency": amp_IF,
                "lo_frequency": amp_LO,
                "correction": IQ_imbalance_correction(0, 0), #TODO: is g the multiplicative factor in amplitude correction?
            },
            {
                "intermediate_frequency": 50e6,
                "lo_frequency": amp_LO,
                "correction": IQ_imbalance_correction(0, 0), #TODO: is g the multiplicative factor in amplitude correction?
            }
        ],
    },
}