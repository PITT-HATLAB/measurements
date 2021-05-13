# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 16:04:53 2021

@author: Ryan Kaufman

"""

import numpy as np
from plottr.data import datadict_storage as dds, datadict as dd
from hat_utilities.fitting.QFit import fit, plotRes, reflectionFunc
from scipy.signal import savgol_filter
import inspect 

class Pump_Scan():
    '''
    Outline: 
        - move the pump frequency with the SNAIL to check where a pump can work
    '''
    def __init__(self, DATADIR, name, VNA_settings, CS_settings, Gen_Settings): 
    
        [self.VNA, self.VNA_fcenter, self.VNA_fspan, self.VNA_fpoints, self.VNA_avgs, self.VNA_power] = VNA_settings
        [self.CS, self.c_start, self.c_stop, self.c_points] = CS_settings
        [self.Gen, self.gen_power, self.attn, self.mode_freq] = Gen_Settings
        self.datadir = DATADIR
        self.name = name
        self.datadict = dd.DataDict(
            current = dict(unit='A'),
            gen_power = dict(unit = 'dBm'),
            vna_frequency = dict(unit='Hz'),
            
            gen_frequency = dict(axes = ['current'], unit = 'Hz'),
            
            undriven_vna_power = dict(axes=['current', 'vna_frequency'], unit = 'dBm'),
            undriven_vna_phase = dict(axes=['current', 'vna_frequency'], unit = 'Degrees'), 
            
            pumped_vna_power = dict(axes=['current', 'vna_frequency', 'gen_power'], unit = 'dBm'),
            pumped_vna_phase = dict(axes=['current', 'vna_frequency', 'gen_power'], unit = 'Degrees'), 
            
            resonant_frequency = dict(axes = ['current']),
            Qint = dict(axes = ['current']),
            Qext = dict(axes = ['current']),
            
            resonant_frequency_error = dict(axes = ['current']),
            Qint_error = dict(axes = ['current']),
            Qext_error = dict(axes = ['current']),
        )
        self.datadict.validate()
        print('creating files')
        self.writer = dds.DDH5Writer(self.datadir, self.datadict, name=self.name)
        self.writer.__enter__()
        print('file created')
        print("Generating Sweep arrays")
        self.currents = np.linspace(self.c_start, self.c_stop, self.c_points)
        self.VNA.fcenter(self.VNA_fcenter)
        self.VNA.fspan(self.VNA_fspan)
        self.VNA.num_points(self.VNA_fpoints)
        self.VNA.avgnum(self.VNA_avgs)
        self.VNA.power(self.VNA_power)
        self.Gen.power(self.gen_power)
        
        self.ETA = self.VNA.sweep_time()*self.VNA_avgs*self.c_points*self.p_points
        
        print(f"Measurement configured, ETA = {self.ETA/60} minutes")
        
    def save_data(self, bias_current, gen_freq, vna_freqs, undriven_vna_phase, undriven_vna_power, driven_vna_phase, driven_vna_power, popt, pconv): 
        [Qext, Qint, f0, magBack, phaseOff] = popt
        
        self.writer.add_data(
            current = bias_current*np.ones(np.size(vna_freqs)), 
            vna_frequency = vna_freqs, 
            
            gen_frequency = gen_freq*np.ones(np.size(vna_freqs)),
            
            undriven_vna_power = undriven_vna_power,
            undriven_vna_phase = undriven_vna_phase,
            
            driven_vna_power = driven_vna_power,
            driven_vna_phase = driven_vna_phase,
            
            base_resonant_frequency = f0*np.ones(np.size(vna_freqs))
            )
    def default_bounds(self, QextGuess, QintGuess, f0Guess, magBackGuess):
        return ([QextGuess / 1.1, QintGuess / 2, f0Guess-1e9, magBackGuess / 5.0, -2 * np.pi],
                [QextGuess * 1.1, QintGuess +40, f0Guess+1e9, magBackGuess * 5.0, 2 * np.pi])
    
    def fit_trace(self, freqs, phase, power, f0Guess, QextGuess = 50, QintGuess = 300, magBackGuess = 0.0001, bounds = None, smooth = False):
        f0Guess = f0Guess*2*np.pi
        if bounds == None: 
            bounds=self.default_bounds(QextGuess, QintGuess, f0Guess, magBackGuess)

        if smooth: 
            phase = savgol_filter(phase, 21, 3)
            power = savgol_filter(power, 21, 3)
        lin = 10**(power/20)
        
        imag = lin * np.sin(phase)
        real = lin * np.cos(phase)

        popt, pconv = fit(freqs, real, imag, power, phase, Qguess = (QextGuess,QintGuess), f0Guess = f0Guess, real_only = 0, bounds = bounds, magBackGuess = magBackGuess)
        
        print(f'f (Hz): {np.round(popt[2]/2/np.pi, 3)}', )
        fitting_params = list(inspect.signature(reflectionFunc).parameters.keys())[1:]
        for i in range(2):
            print(f'{fitting_params[i]}: {np.round(popt[i], 2)} +- {np.round(np.sqrt(pconv[i, i]), 3)}')
        Qtot = popt[0] * popt[1] / (popt[0] + popt[1])
        print('Q_tot: ', round(Qtot), '\nT1 (s):', round(Qtot/popt[2]), f"Kappa: {round(popt[2]/2/np.pi/Qtot)}", )
        
        plotRes(freqs, real, imag, power, phase, popt)
        
        return popt, pconv

    def get_resonant_freq(self, popt_guess, freqs, phase, power):
        
        return 
    
    def measure(self, debug = False):
        popts
        for i, bias_current in enumerate(self.currents):
            self.CS.change_current(bias_current)
            vna_freqs = self.VNA.getSweepData() #1XN array, N in [1601,1000]
            vnadata = np.array(self.VNA.average(self.VNA_avgs)) #2xN array, N in [1601, 1000]
            undriven_vna_phase = vnadata[1, :]
            undriven_vna_power = vnadata[0,:]
            popt, pcov = self.get_resonant_freq(vna_freqs, undriven_vna_phase, undriven_vna_power)
            gen_freq = undriven_res_freq + self.mode_freq
            self.Gen.frequency(gen_freq)
            self.Gen.output_status(1)
            vnadata = np.array(self.VNA.average(self.VNA_avgs)) #2xN array, N in [1601, 1000]
            driven_vna_phase = vnadata[1, :]
            driven_vna_power = vnadata[0,:]
            
            if debug: 
                print(f"Current: {np.round(bias_current, 6)}")
                
            self.save_data(bias_current, gen_freq, vna_freqs, undriven_vna_phase, undriven_vna_power, driven_vna_phase, driven_vna_power, undriven_res_freq)
            if i%5 == 0: 
                print(f'--------------------\nPROGRESS: {np.round((i+1)/self.c_points*100)} percent  complete\n---------------------')