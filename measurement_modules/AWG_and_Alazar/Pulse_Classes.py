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
from data_processing.Helper_Functions import find_all_ddh5

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

def cavity_response_Q_bb(amp, filepath, SR, npts):
    imag = pd.read_csv(filepath, usecols = ['imag']).to_numpy().T[0]
    return imag*amp

def cavity_response_I_bb(amp, filepath, SR, npts):
    real = pd.read_csv(filepath, usecols = ['real']).to_numpy().T[0]
    return real*amp

def cavity_response_with_correction_and_phase_rotation(theta, amp, filepath, SR, npts, amp_corr = 1, phase_offset = 0):
    I_rot = lambda amp, filepath, SR, npts: cavity_response_I_bb(amp, filepath, SR, npts)*np.cos(theta)+cavity_response_Q_bb(amp, filepath, SR, npts)*np.sin(theta)
    
    Q_rot = lambda amp, filepath, SR, npts: amp_corr*(cavity_response_Q_bb(amp, filepath, SR, npts)*np.cos(theta)-cavity_response_I_bb(amp, filepath, SR, npts)*np.sin(theta))
    
    I_corr = lambda amp, filepath, SR, npts: I_rot(amp, filepath, SR, npts)-Q_rot(amp, filepath, SR, npts)*np.sin(phase_offset)
    
    Q_corr = lambda amp, filepath, SR, npts: Q_rot(amp, filepath, SR, npts)/np.cos(phase_offset)
    
    return I_corr, Q_corr


        
@dataclass
class cavity_mimicking_pulse_class_3_state: 
    name: str
    AWG_inst: Tektronix_AWG5014
    LO_frequency: float
    # mod_frequency: float
    DC_offsets: tuple
    ch2_correction: float
    phase_correction: float
    amplitude: float
    phase_rotation: float
    wait_time: int
    
    sim_filepath_G: str
    sim_filepath_E: str
    sim_filepath_F: str
    SR: float
    npts: int
    only_plus: bool
    only_minus: bool
    
    def print_info(self):
        print("Phase Correction: ", self.phase_correction)
        print("Amplitude correction: ", self.ch2_correction)
    
    def setup_pulse(self, preview = False): 
        Ifunc_corrected, Qfunc_corrected = cavity_response_with_correction_and_phase_rotation(self.phase_rotation,self.amplitude, self.sim_filepath_G, self.SR, self.npts, amp_corr = self.ch2_correction, phase_offset = self.phase_correction)
        
        if preview: 
            #plot traces before correction
            fig, ax = plt.subplots(figsize = (12, 10))
            fig.suptitle("Pulses")
            ax.set_aspect(1)
            t_arr = np.linspace(0, 4e-6, 4000)
            # ax.plot(Ifunc(self.amplitude, self.sim_filepath_G, 1e9, 4000), Qfunc(self.amplitude, self.sim_filepath_G, 1e9, 4000), label = 'uncorrected G')
            ax.plot(Ifunc_corrected(self.amplitude, self.sim_filepath_G, 1e9, 4000), Qfunc_corrected(self.amplitude, self.sim_filepath_G,1e9, 4000), label = 'corrected G')
            
            ax.set_aspect(1)
            t_arr = np.linspace(0, 4e-6, 4000)
            # ax.plot(Ifunc(1, self.sim_filepath_E, 1e9, 4000), Qfunc(t_arr, self.sim_filepath_E, 1e9, 4000), label = 'uncorrected E')
            ax.plot(Ifunc_corrected(self.amplitude, self.sim_filepath_E, 1e9, 4000), Qfunc_corrected(self.amplitude, self.sim_filepath_E,1e9, 4000), label = 'corrected E')
            
            ax.set_aspect(1)
            t_arr = np.linspace(0, 4e-6, 4000)
            # ax.plot(Ifunc(1, self.sim_filepath_F, 1e9, 4000), Qfunc(t_arr, self.sim_filepath_F, 1e9, 4000), label = 'uncorrected F')
            ax.plot(Ifunc_corrected(self.amplitude, self.sim_filepath_F, 1e9, 4000), Qfunc_corrected(self.amplitude, self.sim_filepath_F,1e9, 4000), label = 'corrected F')
            
            ax.legend()
            ax.grid()

        #all in one box,
        trig_wait_time = self.wait_time/1e6
        wait_time = 1e-6
        rearm_time = 500e-6
        pulse_dur = 2e-6
        buffer = 300e-9
        mkr_high_time = 80e-9
        mkr2_high_time = 400e-6
        
        marker_input = (trig_wait_time,mkr_high_time)
        
        #make element just for waiting for the trigger vefore each pulse
        bpTrigWait = bb.BluePrint()
        bpTrigWait.insertSegment(1, 'waituntil', rearm_time)
        bpTrigWait.setSR(1e9)
        #make same as above but with a dummy marker for setting off the alazar
        bpTrigWaitMkr = bb.BluePrint()
        bpTrigWaitMkr.insertSegment(1, 'waituntil', rearm_time)
        bpTrigWaitMkr.setSR(1e9)
        bpTrigWaitMkr.marker1 = [(trig_wait_time+0e-6,trig_wait_time+mkr_high_time)]
        #make the I channel for G:
        I0_channel = Ifunc_corrected # args: ampl, filepath_to_cavity_sim
        bpI0 = bb.BluePrint()
        bpI0.setSR(1e9)
        bpI0.insertSegment(1, 'waituntil', (wait_time))
        bpI0.insertSegment(2, I0_channel, (self.amplitude, self.sim_filepath_G), name='Ig', dur=pulse_dur)
        bpI0.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
        bpI0.marker1 = [marker_input]
        
        bpI0.marker2 = [(wait_time-buffer,mkr2_high_time)]
        
        #make the Q channel for G:
        Q0_channel = Qfunc_corrected # args: ampl,filepath_to_cavity_sim
        bpQ0 = bb.BluePrint()
        bpQ0.setSR(1e9)
        bpQ0.insertSegment(1, 'waituntil', (wait_time))
        bpQ0.insertSegment(2, Q0_channel, (self.amplitude, self.sim_filepath_G), name='Qg', dur=pulse_dur)
        bpQ0.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
        bpQ0.marker1 = [marker_input]
        
        #make the I channel for E:
        I1_channel = Ifunc_corrected # args: ampl, filepath_to_cavity_sim
        bpI1 = bb.BluePrint()
        bpI1.setSR(1e9)
        bpI1.insertSegment(1, 'waituntil', (wait_time))
        bpI1.insertSegment(2, I1_channel, (self.amplitude, self.sim_filepath_E), name='Ie', dur=pulse_dur)
        bpI1.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
        bpI1.marker1 = [marker_input]
        
        bpI1.marker2 = [(wait_time-buffer,mkr2_high_time)]
        
        #make the Q channel for E:
        Q1_channel = Qfunc_corrected # args: ampl,filepath_to_cavity_sim
        bpQ1 = bb.BluePrint()
        bpQ1.setSR(1e9)
        bpQ1.insertSegment(1, 'waituntil', (wait_time))
        bpQ1.insertSegment(2, Q1_channel, (self.amplitude, self.sim_filepath_E), name='Qe', dur=pulse_dur)
        bpQ1.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
        bpQ1.marker1 = [marker_input]
        
        #make the I channel for F:
        # I2_channel = Ifunc_corrected # args: ampl, filepath_to_cavity_sim
        bpI2 = bb.BluePrint()
        bpI2.setSR(1e9)
        bpI2.insertSegment(1, 'waituntil', (wait_time))
        bpI2.insertSegment(2, I1_channel, (self.amplitude, self.sim_filepath_F), name='If', dur=pulse_dur)
        bpI2.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
        bpI2.marker1 = [marker_input]
        
        bpI2.marker2 = [(wait_time-buffer,mkr2_high_time)]
        
        #make the Q channel for F:
        # Q2_channel = Qfunc_corrected # args: ampl,filepath_to_cavity_sim
        bpQ2 = bb.BluePrint()
        bpQ2.setSR(1e9)
        bpQ2.insertSegment(1, 'waituntil', (wait_time))
        bpQ2.insertSegment(2, Q1_channel, (self.amplitude, self.sim_filepath_F), name='Qf', dur=pulse_dur)
        bpQ2.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
        bpQ2.marker1 = [marker_input]
        
        ##############################################
        #put blueprints into elements
        waitEl = bb.Element()
        waitEl.addBluePrint(1, bpTrigWait)
        waitEl.addBluePrint(2, bpTrigWait)
        
        waitElMkr = bb.Element()
        waitElMkr.addBluePrint(1, bpTrigWaitMkr)
        waitElMkr.addBluePrint(2, bpTrigWait)
        
        CavEl1 = bb.Element()
        CavEl1.addBluePrint(1,bpI0+bpTrigWait)
        CavEl1.addBluePrint(2,bpQ0+bpTrigWait)
        # plotter(CavEl1)
        
        CavEl2 = bb.Element()
        CavEl2.addBluePrint(1,bpI1+bpTrigWait)
        CavEl2.addBluePrint(2,bpQ1+bpTrigWait)
        # plotter(CavEl2)
        
        CavEl3 = bb.Element()
        CavEl3.addBluePrint(1,bpI2+bpTrigWait)
        CavEl3.addBluePrint(2,bpQ2+bpTrigWait)
        
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
        
        self.AWG_inst.ch1_m1_high(2.5)
        self.AWG_inst.ch1_m2_high(2.5)
        self.AWG_inst.ch2_m1_high(1.5)
        self.AWG_inst.ch2_m2_high(1.5)
        
        #now we have to prep it for the AWG
        # CavSeq.addElement(1, waitElMkr)
        # CavSeq.addElement(1, waitEl)
        CavSeq.addElement(1, CavEl1)
        # CavSeq.addElement(3, waitEl)
        CavSeq.addElement(2, CavEl2)
        # CavSeq.addElement(5, waitEl)
        CavSeq.addElement(3, CavEl3)
        # CavSeq.addElement(7, waitEl)
        
        CavSeq.setSR(1e9)
        
        
        #set the sequencing
        # CavSeq.setSequencingTriggerWait(1, 1)
        # CavSeq.setSequencingTriggerWait(2, 1)
        # CavSeq.setSequencingNumberOfRepetitions(2, 150)
        # CavSeq.setSequencingTriggerWait(3, 0)
        # CavSeq.setSequencingTriggerWait(4, 0)
        # CavSeq.setSequencingTriggerWait(5, 0)
        # CavSeq.setSequencingTriggerWait(6, 0)
        # CavSeq.setSequencingTriggerWait(7, 0)
        # CavSeq.setSequencingTriggerWait(8, 0)
        
        CavSeq.setSequencingTriggerWait(1, 1)
        CavSeq.setSequencingTriggerWait(2, 1)
        CavSeq.setSequencingTriggerWait(3, 1)
        CavSeq.setSequencingNumberOfRepetitions(1, 2562)
        CavSeq.setSequencingNumberOfRepetitions(2, 2562)
        CavSeq.setSequencingNumberOfRepetitions(3, 2562)
        CavSeq.checkConsistency()
        
        #subsequences aren't fully implemented in broadbean :(
        # mainseq = bb.Sequence()
        # mainseq.setSR(1e9)
        # mainseq.addSubSequence(1, CavSeq)
        # mainseq.setSequencingNumberOfRepetitions(1, 2562)
        # mainseq.setChannelAmplitude(1, 4.5)
        # mainseq.setChannelAmplitude(2, 4.5)
        if preview: 
            plotter(CavSeq)
            # plotter(mainseq)
            print("number of AWG points in subsequence", CavSeq.points)
            # print("number of AWG points in main sequence", mainseq.points)
        

        package = CavSeq.outputForAWGFile()
        # package.channels
        self.AWG_inst.make_send_and_load_awg_file(*package[:])
        self.AWG_inst.ch1_amp(4.5)
        self.AWG_inst.ch2_amp(4.5)
        self.AWG_inst.ch1_offset(self.DC_offsets[0])
        self.AWG_inst.ch2_offset(self.DC_offsets[1])
        
        self.AWG_inst.ch1_state(1)
        self.AWG_inst.ch2_state(1)
        
