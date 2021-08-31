# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 09:47:58 2021

@author: Ryan Kaufman

Goal: Create dataclasses for various sweeps that make passing parameters into and out of sweeps faster and safer than lists
"""
import numpy as np
from dataclasses import dataclass
from measurement_modules.Adaptive_Sweeps.Gain_Power_vs_Flux import Gain_Power_vs_Flux
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

@dataclass
class GPF_dataclass: 
    cwd: str = None
    filename: str = None
    inst_dict: dict = None
    
    bias_current: float = None
    vna_att: float = None
    gen_att: float = None
    
    #SigGen settings
    gen_freqs: np.ndarray = None
    
    #VNA settings
    vna_start: float = None
    vna_stop: float = None
        
    vna_points: float = 1601
    vna_avg_number: float = 10
    vna_power: float = -43
    
    #power sweep VNA settings
    vna_p_start: float = -43
    vna_p_stop: float = 0
    vna_p_steps: float = 1600
    vna_p_avgs: float = 100
    
    gen_freq_start_set: int = 0
    gen_freq_stop_set: int = 0
    
    def set_start(self): 
        self.vna_start = self.inst_dict['VNA'].fstart()
        self.vna_stop = self.inst_dict['VNA'].fstop()
        self.gen_freq_start = self.inst_dict['Gen'].frequency()
        self.gen_power_start = self.inst_dict['Gen'].power()
        self.gen_freq_start_set = 1
        self.c_start = self.inst_dict['CS'].current()
    
    def goto_stop(self, gen_freq_offset = 30e6, gen_power_offset = 0):
        try: 
            if self.stop_set: 
                self.inst_dict['Gen'].frequency(self.gen_freq_stop)
                self.inst_dict['Gen'].power(self.gen_power_stop)
        except: 
            pass
        if self.gen_freq_start_set: 
            self.inst_dict['Gen'].frequency(self.gen_freq_start+gen_freq_offset)
            self.inst_dict['Gen'].power(self.gen_power_start - gen_power_offset)
        else: 
            raise Exception('Set start first')
        
    def set_stop(self, gen_pts = 20, gen_power_offset = 0): 
        self.vna_start = self.inst_dict['VNA'].fstart()
        self.vna_stop = self.inst_dict['VNA'].fstop()
        self.gen_freq_stop = self.inst_dict['Gen'].frequency()
        self.gen_power_stop = self.inst_dict['Gen'].power()
        self.stop_set = 1
        if self.gen_freq_start_set: 
            self.gen_freqs = np.linspace(self.gen_freq_start, self.gen_freq_stop, gen_pts)
        else: 
            raise Exception('set start first')
        
    def goto_start(self):
        self.inst_dict['CS'].change_current(self.bias_current)
        self.inst_dict['Gen'].power(self.gen_power_start)
        self.inst_dict['Gen'].frequency(self.gen_freq_start)
        self.inst_dict['Gen'].output_status(1)
        self.inst_dict['VNA'].fstart(self.vna_start)
    
    def print_info(self): 
        print(self.__dict__)
        
    def init_sweep_class(self):
        self.GP_F = Gain_Power_vs_Flux(self.inst_dict['CS'],
                                       self.inst_dict['Gen'],
                                       self.inst_dict['VNA'],
                                       self.cwd,
                                       self.filename, 
                                       gen_att = self.gen_att, 
                                       vna_att = self.vna_att)
        
    def renormalize(self, power = -43, avgnum = 50): 
        self.goto_start()
        self.inst_dict['Gen'].output_status(0)
        # self.inst_dict['VNA'].smoothing(1)
        self.inst_dict['VNA'].power(power)
        self.inst_dict['VNA'].renormalize(avgnum)
        self.inst_dict['VNA'].power(self.vna_power)
        # self.inst_dict['VNA'].smoothing(0)
        self.inst_dict['Gen'].output_status(1)
        
        
    def set_sweep_settings(self, 
                           peak_width_minimum = 0.2, 
                           vna_avgs = 10, 
                           stepsize = 0.1, 
                           block_size = 10,
                           limit = 6,
                           target_gain = 20,
                           threshold = 0.5, 
                           gain_tracking = 'max_point', 
                           gain_detuning = 500e3):
        self.peak_width_minimum = peak_width_minimum
        self.vna_avgs = vna_avgs
        self.stepsize = stepsize
        self.block_size = block_size
        self.limit = limit
        self.target_gain = target_gain
        self.threshold = threshold
        self.sweep_configured = 1
        self.gain_tracking = gain_tracking
        self.gain_detuning = gain_detuning
        
    def sweep(self): 
        self.init_sweep_class()
        self.inst_dict['CS'].change_current(self.c_start)
        self.inst_dict['VNA'].fstart(self.vna_start)
        self.inst_dict['VNA'].fstart(self.vna_stop)
        self.renormalize(power = -30, avgnum = 40)
        self.GP_F.VNA_avg_number = self.vna_avgs
        self.datasets = self.GP_F.sweep_gain_vs_freq(
                                   self.gen_freqs, 
                                   stepsize = self.stepsize, 
                                   block_size =self. block_size,
                                   limit = self.limit,
                                   target_gain = self.target_gain,
                                   threshold = self.threshold,
                                   saturation_sweep = True,
                                   vna_p_start = self.vna_p_start, 
                                   vna_p_stop = self.vna_p_stop, 
                                   vna_p_steps = self.vna_p_steps, 
                                   vna_p_avgs = self.vna_p_avgs, 
                                   peak_width_minimum = self.peak_width_minimum, 
                                   gain_tracking = self.gain_tracking, 
                                   gain_detuning = self.gain_detuning)
    def queue(self): 
        return self.sweep
        
        
        
        
        
        