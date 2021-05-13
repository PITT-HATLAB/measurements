# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 09:47:58 2021

@author: Ryan Kaufman

Goal: Create dataclasses for various sweeps that make passing parameters into and out of sweeps faster and safer than lists
"""

class Alazar_Channel_config():
    def __init__(self): 
        self.ch1_range = 0.4
        self.ch2_range = 0.4
        self.record_time = 4e-6
        self.SR = 1e9
class AWG_Config():
    def __init__(self): 
        self.Sig_freq = 1e10
        self.Mod_freq = 50e6
        self.Ref_freq = 1e10+self.Mod_freq
        