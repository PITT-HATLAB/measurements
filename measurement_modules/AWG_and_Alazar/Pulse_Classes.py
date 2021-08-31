# -*- coding: utf-8 -*-
"""
Created on Fri Jul  2 11:45:55 2021

@author: Hatlab_3
"""
import numpy as np
from qcodes.instrument_drivers.tektronix.AWG5014 import Tektronix_AWG5014
from dataclasses import dataclass
import broadbean as bb
from broadbean.plotting import plotter
import pandas as pd
import matplotlib.pyplot as plt


def phase_shifter(I_data, Q_data, phase_offset, plot = False): 
    '''
    This will take I as the perfect channel and some phase offset sin(theta_imbalance) offsetting Q towards I
    Assuming I to be the unit magnitude
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

def cavity_response_with_correction(amp, filepath, SR, npts, amp_corr = 1, phase_offset = 0):
    #find out what factor to scale the pulses by such that the voltage amplitude is the user input
    imag = pd.read_csv(filepath, usecols = ['imag']).to_numpy().T[0]
    real = pd.read_csv(filepath, usecols = ['real']).to_numpy().T[0]
    amp_scaling = amp/np.max(np.sqrt(imag**2+real**2))
    
    def cavity_response_Q_bb(amp, filepath, SR, npts):
        imag = pd.read_csv(filepath, usecols = ['imag']).to_numpy().T[0]
        return imag*amp_scaling
    
    def cavity_response_I_bb(amp, filepath, SR, npts, amp_corr = amp_corr, phase_corr = phase_offset):
        real = pd.read_csv(filepath, usecols = ['real']).to_numpy().T[0]
        scaled = real*amp_scaling
        amplitude_corrected = scaled*amp_corr
        Q_data = pd.read_csv(filepath, usecols = ['imag']).to_numpy().T[0]*amp
        # Q_data = np.ones(np.size(imag))
        phase_corrected = phase_shifter(amplitude_corrected, Q_data, phase_corr)
        return phase_corrected
    
    return cavity_response_I_bb, cavity_response_Q_bb

def cavity_response_with_correction_and_phase_rotation(theta, amp, filepath, SR, npts, amp_corr = 1, phase_offset = 0):
    cavity_response_I_bb, cavity_response_Q_bb = cavity_response_with_correction(amp, filepath, SR, npts, amp_corr = amp_corr, phase_offset = phase_offset)
    
    return lambda amp, filepath, SR, npts: cavity_response_I_bb(amp, filepath, SR, npts)*np.cos(theta)+cavity_response_Q_bb(amp, filepath, SR, npts)*np.sin(theta), lambda amp, filepath, SR, npts: cavity_response_Q_bb(amp, filepath, SR, npts)*np.cos(theta)-cavity_response_I_bb(amp, filepath, SR, npts)*np.sin(theta)

def cavity_response_with_correction_and_phase_rotation_and_DC_offsets(DC_offsets, theta, amp, filepath, SR, npts, amp_corr = 1, phase_offset = 0):
    cavity_response_I_bb, cavity_response_Q_bb = cavity_response_with_correction(amp, filepath, SR, npts, amp_corr = 1, phase_offset = 0)
    
    return lambda amp, filepath, SR, npts: cavity_response_I_bb(amp, filepath, SR, npts)*np.cos(theta)+cavity_response_Q_bb(amp, filepath, SR, npts)*np.sin(theta)+DC_offsets[0], lambda amp, filepath, SR, npts: cavity_response_Q_bb(amp, filepath, SR, npts)*np.cos(theta)-cavity_response_I_bb(amp, filepath, SR, npts)*np.sin(theta)+DC_offsets[1]

@dataclass
class cavity_mimicking_pulse_class: 
    name: str
    AWG_inst: Tektronix_AWG5014
    LO_frequency: float
    DC_offsets: tuple
    ch2_correction: float
    phase_correction: float
    amplitude: float
    phase_rotation: float
    sim_filepath_plus: str
    sim_filepath_minus: str
    SR: float
    npts: int
    only_plus: bool
    only_minus: bool
    
    def print_info(self):
        print("Phase Correction: ", self.phase_correction)
        print("Amplitude correction: ", self.ch2_correction)
    
    def setup_pulse(self, preview = False): 
        pulse_voltage = self.amplitude
        Ifunc_corrected, Qfunc_corrected = cavity_response_with_correction_and_phase_rotation(self.phase_rotation,pulse_voltage, self.sim_filepath_plus, self.SR, self.npts, amp_corr = self.ch2_correction, phase_offset = self.phase_correction)
        
        if preview: 
            #plot traces before correction
            Ifunc, Qfunc = cavity_response_with_correction(1, self.sim_filepath_plus, self.SR, self.npts, amp_corr = 1, phase_offset = self.phase_rotation)
            fig, ax = plt.subplots(figsize = (12, 10))
            fig.suptitle("Pulses")
            ax.set_aspect(1)
            t_arr = np.linspace(0, 4e-6, 4000)
            ax.plot(Ifunc(self.amplitude, self.sim_filepath_plus, 1e9, 4000), Qfunc(self.amplitude, self.sim_filepath_plus, 1e9, 4000), label = 'uncorrected G')
            ax.plot(Ifunc_corrected(self.amplitude, self.sim_filepath_plus, 1e9, 4000), Qfunc_corrected(self.amplitude, self.sim_filepath_plus,1e9, 4000), label = 'corrected G')
            
            ax.set_aspect(1)
            t_arr = np.linspace(0, 4e-6, 4000)
            ax.plot(Ifunc(1, self.sim_filepath_minus, 1e9, 4000), Qfunc(t_arr, self.sim_filepath_minus, 1e9, 4000), label = 'uncorrected E')
            ax.plot(Ifunc_corrected(1, self.sim_filepath_minus, 1e9, 4000), Qfunc_corrected(1, self.sim_filepath_minus,1e9, 4000), label = 'corrected E')
            ax.legend()
            ax.grid()

        #all in one box,
        wait_time = 1e-6
        rearm_time = 10e-6
        pulse_dur = 2e-6
        buffer = 300e-9
        #make element just for waiting for the trigger vefore each pulse
        bpTrigWait = bb.BluePrint()
        bpTrigWait.insertSegment(1, 'waituntil', rearm_time)
        bpTrigWait.setSR(1e9)
        
        #make the I channel for -detuning:
        I0_channel = Ifunc_corrected # args: ampl, filepath_to_cavity_sim
        bpI0 = bb.BluePrint()
        bpI0.setSR(1e9)
        bpI0.insertSegment(1, 'waituntil', (wait_time))
        bpI0.insertSegment(2, I0_channel, (pulse_voltage, self.sim_filepath_plus), name='Ig', dur=pulse_dur)
        bpI0.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
        bpI0.marker1 = [(0e-6,50e-9)]
        
        bpI0.marker2 = [(wait_time-buffer,pulse_dur+2*buffer)]
        
        
        #make the Q channel for -detuning:
        Q0_channel = Qfunc_corrected # args: ampl,filepath_to_cavity_sim
        bpQ0 = bb.BluePrint()
        bpQ0.setSR(1e9)
        bpQ0.insertSegment(1, 'waituntil', (wait_time))
        bpQ0.insertSegment(2, Q0_channel, (pulse_voltage, self.sim_filepath_plus), name='Qg', dur=pulse_dur)
        bpQ0.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
        bpQ0.marker1 = [(0e-6,50e-9)]
        
        #make the I channel for +detuning:
        I1_channel = Ifunc_corrected # args: ampl, filepath_to_cavity_sim
        bpI1 = bb.BluePrint()
        bpI1.setSR(1e9)
        bpI1.insertSegment(1, 'waituntil', (wait_time))
        bpI1.insertSegment(2, I1_channel, (pulse_voltage, self.sim_filepath_minus), name='Ie', dur=pulse_dur)
        bpI1.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
        bpI1.marker1 = [(0e-6,50e-9)]
        
        bpI1.marker2 = [(wait_time-buffer,pulse_dur+2*buffer)]
        
        #make the Q channel for +detuning:
        Q1_channel = Qfunc_corrected # args: ampl,filepath_to_cavity_sim
        bpQ1 = bb.BluePrint()
        bpQ1.setSR(1e9)
        bpQ1.insertSegment(1, 'waituntil', (wait_time))
        bpQ1.insertSegment(2, Q1_channel, (pulse_voltage, self.sim_filepath_minus), name='Qe', dur=pulse_dur)
        bpQ1.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
        bpQ1.marker1 = [(0e-6,50e-9)]
        
        ##############################################
        #put blueprints into elements
        waitEl = bb.Element()
        waitEl.addBluePrint(1, bpTrigWait)
        waitEl.addBluePrint(2, bpTrigWait)
        
        CavEl1 = bb.Element()
        CavEl1.addBluePrint(1,bpI0)
        CavEl1.addBluePrint(2,bpQ0)
        # plotter(CavEl1)
        
        CavEl2 = bb.Element()
        CavEl2.addBluePrint(1,bpI1)
        CavEl2.addBluePrint(2,bpQ1)
        # plotter(CavEl2)
        
        ###############################################
        #put elements into sequence
        CavSeq = bb.Sequence()
        
        #good values to kill leakage? 
        self.AWG_inst.ch1_amp(4.5)
        CavSeq.setChannelAmplitude(1, 4.5)  # Call signature: channel, amplitude (peak-to-peak)
        # CavSeq.setChannelOffset(1, self.AWG_inst.ch1_offset())
        #you would do the above if you actually wanted samples to be the voltage you want, but we WANT an offset in to cancel leakage, so we enter 0
        self.AWG_inst.ch1_offset(0)
        self.AWG_inst.ch2_offset(0)
        CavSeq.setChannelOffset(1, 0)
        self.AWG_inst.ch1_amp(4.5)
        CavSeq.setChannelAmplitude(2, 4.5)
        # CavSeq.setChannelOffset(2, self.AWG_inst.ch2_offset())
        CavSeq.setChannelOffset(2, 0)
        
        #now we have to prep it for the AWG
        CavSeq.addElement(1, waitEl)
        CavSeq.addElement(2, CavEl1)
        CavSeq.addElement(3, waitEl)
        CavSeq.addElement(4, CavEl2)
        
        CavSeq.setSR(1e9)
        # plotter(CavSeq)
        
        #set the sequencing
        # Here we repeat each element twice and then proceed to the next, wrapping over at the end
        if self.only_plus and not self.only_minus: 
            CavSeq.setSequencingTriggerWait(1, 1)
            CavSeq.setSequencingTriggerWait(2, 0)
            CavSeq.setSequencingTriggerWait(3, 1)
            CavSeq.setSequencingTriggerWait(4, 0)
            CavSeq.setSequencingGoto(2, 1)
        elif self.only_minus and not self.only_plus: 
            CavSeq.setSequencingTriggerWait(1, 1)
            CavSeq.setSequencingTriggerWait(2, 0)
            CavSeq.setSequencingTriggerWait(3, 1)
            CavSeq.setSequencingTriggerWait(4, 0)
            CavSeq.setSequencingGoto(4, 3)
        else: 
            CavSeq.setSequencingTriggerWait(1, 1)
            CavSeq.setSequencingTriggerWait(2, 0)
            CavSeq.setSequencingTriggerWait(3, 1)
            CavSeq.setSequencingTriggerWait(4, 0)
            CavSeq.setSequencingGoto(4, 1)
    
        CavSeq.checkConsistency()
        
        package = CavSeq.outputForAWGFile()
        package.channels
        self.AWG_inst.make_send_and_load_awg_file(*package[:])
        self.AWG_inst.ch1_amp(4.5)
        self.AWG_inst.ch2_amp(4.5)
        self.AWG_inst.ch1_offset(self.DC_offsets[0])
        self.AWG_inst.ch2_offset(self.DC_offsets[1])
        
        self.AWG_inst.ch1_state(1)
        self.AWG_inst.ch2_state(1)