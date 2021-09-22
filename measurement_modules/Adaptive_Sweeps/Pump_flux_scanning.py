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
from qcodes.instrument import VisaInstrument
from dataclasses import dataclass

@dataclass
class PS_dc: 
    datadir: str = ''
    name: str = ''
    VNA: object = None
    VNA_pstart: float = None
    VNA_pstop: float = None
    VNA_ppoints: int = 100
    VNA_avgs: int = 20
    VNA_att: int = 0
    VNA_detuning: float = 0.1e6
    
    Gen: object = None
    Gen_pstart: float = -20
    Gen_pstop: float = 20
    Gen_ppoints: int = 80
    Gen_detuning: float = 0
    Gen_att: int = 0
    
    CS: object = None
    c_start: float = None
    c_stop: float = None
    c_points: int = None
    c_ramp_rate: object = None
    
    fs_fit_path: str = ''
    
    def configure(self):
        #calculate the resonant_frequencies at each current using the fs_fit
        self.currents = np.linspace(self.c_start, self.c_stop, self.c_points)
        self.fs_fit_func = self.read_fs_data(self.fs_fit_path)
        
        self.res_freqs = self.fs_fit_func(self.currents)
        self.Gen_freqs = 2*(self.res_freqs+self.Gen_detuning)
        self.VNA_cw_freqs = self.Gen_freqs/2+self.VNA_detuning
        self.gen_powers = np.linspace(self.Gen_pstart, self.Gen_pstop, self.Gen_ppoints)
        
        #set VNA to power sweep mode
        self.VNA.sweep_type('POW')
        self.VNA.fcenter(self.res_freqs[0])
        self.VNA.math('NORM') #turning math off
        self.VNA.power_start(self.VNA_pstart)
        self.VNA.power_stop(self.VNA_pstop)
        self.VNA.num_points(self.VNA_ppoints)
        self.VNA.avgnum(self.VNA_avgs)
        
    def ETA(self): 
        time_per_combo = self.VNA.sweep_time()
        print(f"ETA: {np.round(time_per_combo*self.VNA.avgnum()*self.Gen_ppoints*self.c_points/60/60, 1)} hours")
        
    def read_fs_data(self, fs_filepath, interpolation = 'linear'):
        ret = all_datadicts_from_hdf5(fs_filepath)
        res_freqs = ret['data'].extract('base_resonant_frequency').data_vals('base_resonant_frequency')
        currents = ret['data'].extract('base_resonant_frequency').data_vals('current')
        fs_fit_func = interp1d(currents, res_freqs, interpolation)
        return fs_fit_func
    
    def preview(self): 
        plt.plot(self.currents, self.fs_fit_func(self.currents), label = "resonant frequencies")
        plt.plot(self.currents, 2*self.fs_fit_func(self.currents), '--',label = "2X resonant frequencies")
        plt.plot(self.currents, self.Gen_freqs, label = "Generator frequencies")
        plt.legend()
        plt.xlabel("current (A)")
        plt.ylabel("Frequency(Hz)")
        plt.title("Preview")
        plt.grid()
        
    
class Pump_flux_scan():
    
    def __init__(self, PS_dc): 
        self.dc = PS_dc
        
        self.datadict = dd.DataDict(
            current = dict(unit='A'),
            vna_input_power = dict(unit = 'dBm'),
            # vna_frequency = dict(unit='Hz'),
            
            gen_power = dict(unit = 'dBm'),
            gen_frequency = dict(unit = 'Hz'),
            
            vna_return_power = dict(axes=['current', 'vna_input_power', 'gen_power', 'gen_frequency'], unit = 'dBm'),
            vna_phase = dict(axes=['current', 'vna_input_power', 'gen_power', 'gen_frequency'], unit = 'Degrees'), 

        )
        
        self.datadict.validate()
        print('creating files')
        self.writer = dds.DDH5Writer(self.dc.datadir, self.datadict, name=self.dc.name)
        self.writer.__enter__()
        print('file created')

    def save_data(self): 
        vna_pows = self.dc.VNA.getSweepData()
        size_match = np.ones(np.size(vna_pows))
        vna_data = self.dc.VNA.average(self.dc.VNA_avgs)
        self.writer.add_data(
            current = self.dc.CS.current()*size_match, 
            vna_input_power = vna_pows - self.dc.VNA_att, 
            # vna_frequency = self.dc.VNA.fcenter()*size_match, 
            gen_frequency = self.dc.Gen.frequency()*size_match,
            gen_power = self.dc.Gen.power()*size_match-self.dc.Gen_att,
            
            vna_return_power = vna_data[0],
            vna_phase = vna_data[1],
            )
    
    def measure(self, debug = False):
        
        for i, bias_current in enumerate(self.dc.currents):
            
            self.dc.CS.change_current(bias_current, ramp_rate = self.dc.c_ramp_rate)
            self.dc.VNA.fcenter(self.dc.VNA_cw_freqs[i])
            self.dc.Gen.frequency(self.dc.Gen_freqs[i])
            for gen_power in self.dc.gen_powers: 
                self.dc.Gen.power(gen_power)
                self.dc.Gen.output_status(1)
                self.save_data()
            if i%5 == 0: 
                print(f'--------------------\nPROGRESS: {np.round((i+1)/self.dc.c_points*100)} percent  complete\n---------------------')
        print("Sweep, completed")
        self.writer.file.close()
            
            