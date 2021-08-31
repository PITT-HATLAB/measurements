# -*- coding: utf-8 -*-
"""
Created on Wed Jan  6 14:10:14 2021

@author: Hatlab_3
"""
import numpy as np
from plottr.data import datadict_storage as dds, datadict as dd
from plottr.data.datadict_storage import all_datadicts_from_hdf5
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

class Duffing_Test():
    
    def __init__(self, DATADIR, name, VNA_settings, CS_settings, Gen_Settings, fs_fit_filepath, mode_kappa = 15e7, mode_side = 4, ramp_rate = None): 
        [self.VNA, self.VNA_fstart, self.VNA_fstop, self.VNA_fpoints, self.VNA_avgs, self.VNA_power] = VNA_settings
        [self.CS, self.c_start, self.c_stop, self.c_points] = CS_settings
        [self.Gen, self.p_start, self.p_stop, self.p_points, self.attn] = Gen_Settings

        self.datadir = DATADIR
        self.name = name
        self.mode_kappa = mode_kappa
        self.mode_side = mode_side
        
        self.datadict = dd.DataDict(
            current = dict(unit='A'),
            gen_power = dict(unit = 'dBm'),
            vna_frequency = dict(unit='Hz'),
            
            gen_frequency = dict(axes = ['current'], unit = 'Hz'),
            
            undriven_vna_power = dict(axes=['current', 'vna_frequency'], unit = 'dBm'),
            undriven_vna_phase = dict(axes=['current', 'vna_frequency'], unit = 'Degrees'), 
            
            driven_vna_power = dict(axes=['current', 'vna_frequency', 'gen_power'], unit = 'dBm'),
            driven_vna_phase = dict(axes=['current', 'vna_frequency', 'gen_power'], unit = 'Degrees'), 
        )
        self.datadict.validate()
        print('creating files')
        self.writer = dds.DDH5Writer(self.datadir, self.datadict, name=self.name)
        self.writer.__enter__()
        print('file created')
        print("Generating Sweep arrays")
        self.currents = np.linspace(self.c_start, self.c_stop, self.c_points)
        self.gen_powers = np.linspace(self.p_start, self.p_stop, self.p_points)
        self.VNA.fstart(self.VNA_fstart)
        self.VNA.fstop(self.VNA_fstop)
        self.VNA.num_points(self.VNA_fpoints)
        self.VNA.avgnum(self.VNA_avgs)
        self.VNA.power(self.VNA_power)
        self.ramp_rate = ramp_rate
        self.ETA = self.VNA.sweep_time()*self.VNA_avgs*self.c_points*self.p_points
        print(f"Measurement configured, ETA = {self.ETA/60} minutes")

        #load in fluxsweep data
        self.fs_fit_func = self.read_fs_data(fs_fit_filepath)
    def preview(self): 
        plt.plot(self.currents, self.fs_fit_func(self.currents), label = "resonant frequencies")
        plt.plot(self.currents, self.fs_fit_func(self.currents) + self.mode_side*self.mode_kappa, label = "Generator frequencies")
        plt.legend()
        plt.xlabel("current (A)")
        plt.ylabel("Frequency(Hz)")
        plt.title("Preview")
        
        
        
    def read_fs_data(self, fs_filepath, interpolation = 'linear'):
        ret = all_datadicts_from_hdf5(fs_filepath)
        res_freqs = ret['data'].extract('base_resonant_frequency').data_vals('base_resonant_frequency')
        currents = ret['data'].extract('base_resonant_frequency').data_vals('current')
        fs_fit_func = interp1d(currents, res_freqs, interpolation)
        return fs_fit_func
    
    def save_data(self, bias_current, gen_power, gen_freq, vna_freqs, undriven_vna_phase, undriven_vna_power, driven_vna_phase, driven_vna_power): 
        self.writer.add_data(
            current = bias_current*np.ones(np.size(vna_freqs)), 
            gen_power = (gen_power-self.attn)*np.ones(np.size(vna_freqs)), 
            vna_frequency = vna_freqs, 
            
            gen_frequency = gen_freq*np.ones(np.size(vna_freqs)),
            
            undriven_vna_power = undriven_vna_power,
            undriven_vna_phase = undriven_vna_phase,
            
            driven_vna_power = driven_vna_power,
            driven_vna_phase = driven_vna_phase,
            )
    
    def measure(self, debug = False, adaptive_VNA_window = False):
        
        for i, bias_current in enumerate(self.currents):
            if adaptive_VNA_window: 
                self.VNA.fcenter(float(self.fs_fit_func(bias_current)))
                self.VNA.fspan(10*self.mode_kappa)
            self.CS.change_current(bias_current, ramp_rate = self.ramp_rate)
            vna_freqs = self.VNA.getSweepData() #1XN array, N in [1601,1000]
            vnadata = np.array(self.VNA.average(self.VNA_avgs)) #2xN array, N in [1601, 1000]
            undriven_vna_phase = vnadata[1, :]
            undriven_vna_power = vnadata[0,:]
            gen_freq = self.fs_fit_func(bias_current) + self.mode_side*self.mode_kappa
            self.Gen.frequency(gen_freq)
            for gen_power in self.gen_powers: 
                self.Gen.power(gen_power)
                self.Gen.output_status(1)
                vna_freqs = self.VNA.getSweepData() #1XN array, N in [1601,1000]
                driven_vnadata = np.array(self.VNA.average(self.VNA_avgs)) #2xN array, N in [1601, 1000]
                driven_vna_phase = driven_vnadata[1,:]
                driven_vna_power = driven_vnadata[0,:]
                self.Gen.output_status(0)
                if debug: 
                    print(f"Current: {np.round(bias_current, 6)}, Power: {np.round(gen_power, 2)}")
                
                self.save_data(bias_current, gen_power, gen_freq, vna_freqs, undriven_vna_phase, undriven_vna_power, driven_vna_phase, driven_vna_power)
            if i%5 == 0: 
                print(f'--------------------\nPROGRESS: {np.round((i+1)/self.c_points*100)} percent  complete\n---------------------')
        print("Sweep, completed")
        self.writer.file.close()
            
            