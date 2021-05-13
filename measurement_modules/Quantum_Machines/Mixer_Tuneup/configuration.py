# -*- coding: utf-8 -*-
"""
Created on Wed May  5 13:03:50 2021

@author: Ryan Kaufman
"""
import numpy as np

pulse_len = 100
amp_IF = 0e6
amp_LO = 2e9
I_offset = -0.095
Q_offset = -0.09
# I_offset = 0
# Q_offset = 0

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
            "operations": {
                "Both_on": "All_on",
                "I_only": "I_on",
                "Q_only": "Q_on",
                "Both_off": "All_off"
            },
            "time_of_flight": 180,
            "smearing": 0,
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
        }
    },
    "waveforms": {
        "const_wf_off": {"type": "constant", "sample": 0},
        "const_wf": {"type": "constant", "sample": 0.1},
    },
    "digital_waveforms": {
        "ON": {"samples": [(1, 0)]},
        "trig": {"samples": [(1, 100)]},
        "stutter": {"samples": [(1, 100), (0, 200), (1, 76), (0, 10), (1, 0)]},
    },
    "mixers": {
        "mixer_amp": [
            {
                "intermediate_frequency": amp_IF,
                "lo_frequency": amp_LO,
                "correction": IQ_imbalance_correction(0, 0),
            }
        ],
    },
}