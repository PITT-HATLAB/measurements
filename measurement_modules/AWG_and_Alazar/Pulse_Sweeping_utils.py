# -*- coding: utf-8 -*-
"""
Created on Thu Apr 29 09:40:12 2021

@author: Ryan Kaufman

Set up function module that can assist in loading pulse sequences into AWG
and functionalizing Alazar acquiring
"""
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable

from plottr.data import datadict_storage as dds, datadict as dd

from instrument_drivers.alazar_utilities.controller.ATSChannelController import ATSChannelController
from instrument_drivers.alazar_utilities.controller.alazar_channel import AlazarChannel
from qcodes.instrument_drivers.tektronix.AWG5014 import Tektronix_AWG5014
from qcodes.instrument.parameter import Parameter
from data_processing.signal_processing.Pulse_Processing import demod, phase_correction

from dataclasses import dataclass

import broadbean as bb
from broadbean.plotting import plotter
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from plottr.data.datadict_storage import all_datadicts_from_hdf5

import time

    
def Standard_Alazar_Config(alazar_inst,alazar_dataclass):
    alazar = alazar_inst
    ad = alazar_dataclass
    
    with alazar.syncing():    
        alazar.clock_source('EXTERNAL_CLOCK_10MHz_REF')
        alazar.sample_rate(ad.SR)
        alazar.decimation(1)
        alazar.coupling1('AC')
        alazar.coupling2('AC')
        alazar.channel_range1(ad.ch1_range)
        alazar.channel_range2(ad.ch2_range)
        alazar.impedance1(50)
        alazar.impedance2(50)
        alazar.trigger_operation('TRIG_ENGINE_OP_J')
        alazar.trigger_engine1('TRIG_ENGINE_J')
        alazar.trigger_source1('EXTERNAL')
        alazar.trigger_slope1('TRIG_SLOPE_POSITIVE')
        alazar.trigger_level1(160)
        alazar.trigger_engine2('TRIG_ENGINE_K')
        alazar.trigger_source2('DISABLE')
        alazar.trigger_slope2('TRIG_SLOPE_POSITIVE')
        alazar.trigger_level2(128)
        alazar.external_trigger_coupling('DC')
        alazar.external_trigger_range('ETR_1V')
        alazar.trigger_delay(0)
        alazar.timeout_ticks(0)
        alazar.aux_io_mode('AUX_IN_AUXILIARY') # AUX_IN_TRIGGER_ENABLE for seq mode on
        alazar.aux_io_param('NONE') # TRIG_SLOPE_POSITIVE for seq mode on
    print("\nAlazar Configured\n")
    # Create the acquisition controller which will take care of the data handling and tell it which 
    # alazar instrument to talk to. Explicitly pass the default options to the Alazar.
    # Dont integrate over samples but avarage over records

    myctrl = ATSChannelController(name='my_controller', alazar_name='Alazar')
    myctrl.int_time(4e-6)
    myctrl.int_delay(0e-9)
    
    print("Samples per record: ",myctrl.samples_per_record())
    alazar.buffer_timeout.set(20000)
    rec_num = 7680
    chan1 = AlazarChannel(myctrl, 'ChanA', demod=False, integrate_samples=False, average_records=False, average_buffers = True)
    chan1.alazar_channel('A')
    chan1.records_per_buffer(rec_num)
    chan1.num_averages(1)
    chan1.prepare_channel()
    
    chan2 = AlazarChannel(myctrl, 'ChanB', demod=False, integrate_samples=False, average_records= False, average_buffers = True)
    chan2.alazar_channel('B')
    chan2.records_per_buffer(rec_num)
    chan2.num_averages(1)
    chan2.prepare_channel()
    
    myctrl.channels.append(chan1)
    myctrl.channels.append(chan2)
    
    return myctrl        

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
    def cavity_response_Q_bb(amp, filepath, SR, npts):
        imag = pd.read_csv(filepath, usecols = ['imag']).to_numpy().T[0]
        return imag*amp
    
    def cavity_response_I_bb(amp, filepath, SR, npts, amp_corr = amp_corr, phase_corr = phase_offset):
        real = pd.read_csv(filepath, usecols = ['real']).to_numpy().T[0]
        scaled = real*amp
        amplitude_corrected = scaled*amp_corr
        Q_data = pd.read_csv(filepath, usecols = ['imag']).to_numpy().T[0]*amp
        phase_corrected = phase_shifter(amplitude_corrected, Q_data, phase_corr)
        return phase_corrected
    
    return cavity_response_I_bb, cavity_response_Q_bb

def cavity_response_with_correction_and_phase_rotation(theta, amp, filepath, SR, npts, amp_corr = 1, phase_offset = 0):
    cavity_response_I_bb, cavity_response_Q_bb = cavity_response_with_correction(amp, filepath, SR, npts, amp_corr = 1, phase_offset = 0)
    
    return lambda amp, filepath, SR, npts: cavity_response_I_bb(amp, filepath, SR, npts)*np.cos(theta)+cavity_response_Q_bb(amp, filepath, SR, npts)*np.sin(theta), lambda amp, filepath, SR, npts: cavity_response_Q_bb(amp, filepath, SR, npts)*np.cos(theta)-cavity_response_I_bb(amp, filepath, SR, npts)*np.sin(theta)

class Phase_Parameter(Parameter): 
    def __init__(self, name, cavity_mimicking_pulse_class):
        # only name is required
        super().__init__(name)
        self._phase = cavity_mimicking_pulse_class.phase_rotation
        self.pulse_class = cavity_mimicking_pulse_class

    # you must provide a get method, a set method, or both.
    def get_raw(self):
        return self.pulse_class.phase_rotation

    def set_raw(self, val):
        self.pulse_class.phase_rotation = val
        self.create_and_load_awg_sequence()
        
    def create_and_load_awg_sequence(self):
        self.pulse_class.setup_cavity_mimicking_pulse()

class LO_Parameter(Parameter): 
    def __init__(self, name, cavity_mimicking_pulse_class):
        # only name is required
        super().__init__(name)
        self._phase = cavity_mimicking_pulse_class.phase_rotation
        self.pulse_class = cavity_mimicking_pulse_class

    # you must provide a get method, a set method, or both.
    def get_raw(self):
        return self.pulse_class.phase_rotation

    def set_raw(self, val):
        self.pulse_class.phase_rotation = val
        self.create_and_load_awg_sequence()
        
    def create_and_load_awg_sequence(self):
        self.pulse_class.setup_cavity_mimicking_pulse()
        
class Voltage_Parameter(Parameter): 
    def __init__(self, name, cavity_mimicking_pulse_class):
        # only name is required
        super().__init__(name)
        self._phase = cavity_mimicking_pulse_class.phase_rotation
        self.pulse_class = cavity_mimicking_pulse_class

    # you must provide a get method, a set method, or both.
    def get_raw(self):
        return self.pulse_class.phase_rotation

    def set_raw(self, val):
        self.pulse_class.phase_rotation = val
        self.create_and_load_awg_sequence()
        
    def create_and_load_awg_sequence(self):
        self.pulse_class.setup_cavity_mimicking_pulse()

@dataclass
class cavity_mimicking_pulse_class: 
    name: str
    AWG_inst: Tektronix_AWG5014
    LO_frequency: float
    DC_offsets: tuple
    ch2_correction: float
    phase_offset: float
    amplitude: float
    phase_rotation: float
    sim_filepath_plus: str
    sim_filepath_minus: str
    SR: float
    npts: int
    only_plus: bool
    only_minus: bool
    
    def setup_cavity_mimicking_pulse(self): 
        Ifunc_corrected, Qfunc_corrected = cavity_response_with_correction_and_phase_rotation(self.phase_rotation,1, self.sim_filepath_plus, self.SR, self.npts, amp_corr = self.ch2_correction, phase_offset = self.phase_offset)
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
        bpI0.insertSegment(2, I0_channel, (1, self.sim_filepath_plus), name='Ig', dur=pulse_dur)
        bpI0.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
        bpI0.marker1 = [(0e-6,50e-9)]
        
        bpI0.marker2 = [(wait_time-buffer,pulse_dur+2*buffer)]
        
        
        #make the Q channel for -detuning:
        Q0_channel = Qfunc_corrected # args: ampl,filepath_to_cavity_sim
        bpQ0 = bb.BluePrint()
        bpQ0.setSR(1e9)
        bpQ0.insertSegment(1, 'waituntil', (wait_time))
        bpQ0.insertSegment(2, Q0_channel, (1, self.sim_filepath_plus), name='Qg', dur=pulse_dur)
        bpQ0.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
        bpQ0.marker1 = [(0e-6,50e-9)]
        
        #make the I channel for +detuning:
        I1_channel = Ifunc_corrected # args: ampl, filepath_to_cavity_sim
        bpI1 = bb.BluePrint()
        bpI1.setSR(1e9)
        bpI1.insertSegment(1, 'waituntil', (wait_time))
        bpI1.insertSegment(2, I1_channel, (1, self.sim_filepath_minus), name='Ie', dur=pulse_dur)
        bpI1.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
        bpI1.marker1 = [(0e-6,50e-9)]
        
        bpI1.marker2 = [(wait_time-buffer,pulse_dur+2*buffer)]
        
        #make the Q channel for +detuning:
        Q1_channel = Qfunc_corrected # args: ampl,filepath_to_cavity_sim
        bpQ1 = bb.BluePrint()
        bpQ1.setSR(1e9)
        bpQ1.insertSegment(1, 'waituntil', (wait_time))
        bpQ1.insertSegment(2, Q1_channel, (1, self.sim_filepath_minus), name='Qe', dur=pulse_dur)
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
        plotter(CavEl1)
        
        CavEl2 = bb.Element()
        CavEl2.addBluePrint(1,bpI1)
        CavEl2.addBluePrint(2,bpQ1)
        plotter(CavEl2)
        
        ###############################################
        #put elements into sequence
        CavSeq = bb.Sequence()
        
        #good values to kill leakage: 
        CavSeq.setChannelAmplitude(1, 5)  # Call signature: channel, amplitude (peak-to-peak)
        CavSeq.setChannelOffset(1, 0)
        CavSeq.setChannelAmplitude(2, 5)
        CavSeq.setChannelOffset(2, 0)
        
        #now we have to prep it for the AWG
        CavSeq.addElement(1, waitEl)
        CavSeq.addElement(2, CavEl1)
        CavSeq.addElement(3, waitEl)
        CavSeq.addElement(4, CavEl2)
        
        CavSeq.setSR(1e9)
        
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
        self.AWG_inst.ch1_amp(1)
        self.AWG_inst.ch2_amp(1)
        self.AWG_inst.ch1_offset(self.DC_offsets[0])
        self.AWG_inst.ch2_offset(self.DC_offsets[1])
        
        self.AWG_inst.ch1_state(1)
        self.AWG_inst.ch2_state(1)
    
def acquire_one_pulse(AWG_inst, Alazar_controller, Sig_Gen, Ref_Gen, LO_frequency, mod_freq, sample_rate, debug = False): 

    Sig_Gen.frequency(LO_frequency)
    Ref_Gen.frequency(LO_frequency+mod_freq)
    Sig_Gen.output_status(1)
    Ref_Gen.output_status(1)
    myctrl = Alazar_controller
    AWG = AWG_inst
    AWG.ch1_m1_high(1.8)
    AWG.ch1_m2_high(2.5)
    AWG.ch2_m1_high(1.9)
    AWG.ch2_m2_high(2.5)
    AWG.run()
    time.sleep(1)
    ch1data, ch2data = myctrl.channels.data()
    AWG.stop()
    #Demodulation
    mod_period = sample_rate//mod_freq
    arr_shape = list(np.shape(ch1data)) #same as ch2
    arr_shape[1] = int(arr_shape[1]//mod_period)
    
    sI = []
    sQ = []
    rI = []
    rQ = []
    
    for i, (ch1data_record, ch2data_record) in enumerate(zip(ch1data, ch2data)):
        
        sI_row,sQ_row,rI_row,rQ_row = demod(ch1data_record, ch2data_record)
        sI.append(sI_row)
        sQ.append(sQ_row)
        rI.append(rI_row)
        rQ.append(rQ_row)
        
    sI = np.array(sI)
    sQ = np.array(sQ)
    rI = np.array(rI)
    rQ = np.array(rQ)
    # Phase correction
    sI_c, sQ_c, rI_trace, rQ_trace = phase_correction(sI, sQ, rI, rQ)
    
    Sig_Gen.output_status(0)
    Ref_Gen.output_status(0)
    return sI_c, sQ_c, rI_trace, rQ_trace

class Pulse_Sweep(): 
    
    def __init__(self, AWG, AWG_Config, Alazar_ctrl, Alazar_config, Sig_Gen, Ref_Gen): 
        
        '''
        Implicit in this file is the external interferometer, these components
        '''
        self.AWG_inst = AWG
        self.is_ind_par_set = False
        self.Alazar_ctrl = Alazar_ctrl
        # self.Alazar_ctrl = Standard_Alazar_Config(Alazar, Alazar_config)
        self.Alazar_config = Alazar_config
        self.AWG_Config = AWG_Config
        self.sig_gen = Sig_Gen
        self.ref_gen = Ref_Gen
        self.ind_pars = []
        
    def add_independent_parameter(self, ind_par, points, filename = None): 

        self.ind_par_vals = points
        self.ind_par.append(ind_par)
        if filename == None: 
            self.filenames = [f'{ind_par.name}_{np.round(ind_par_val, 3)}' for ind_par_val in self.ind_par_vals]
        else: 
            self.filenames = [f'{filename}_{ind_par.name}_{np.round(ind_par_val, 3)}' for ind_par_val in self.ind_par_vals]
        
        self.is_ind_par_set = True
        
    def pre_measurement_operation(self, i): 
        self.ind_par(self.ind_par_vals[i])
        
    def post_measurement_operation(self, i): 
        print(f"\nMeasurement {i+1} out of {np.size(self.ind_par_vals)} completed\n")
    
    def sweep(self, DATADIR): 
        if not self.is_ind_par_set: 
            raise Exception("Independent parameter not yet set. Run set_independent_parameter method")
        for i, filename in enumerate(self.filenames):
            
            ####################### Set up the datadict
            self.datadict = dd.DataDict(
                time = dict(unit = 'ns'),
                record_num = dict(unit = 'num'),
                I_plus = dict(axes=['record_num', 'time' ], unit = 'DAC'),
                Q_plus = dict(axes=['record_num', 'time' ], unit = 'DAC'),
                I_minus = dict(axes=['record_num', 'time' ], unit = 'DAC'),
                Q_minus = dict(axes=['record_num', 'time' ], unit = 'DAC')
            )
        
            self.pre_measurement_operation(i)
            
            with dds.DDH5Writer(DATADIR, self.datadict, name=filename) as writer:
                sI_c, sQ_c, ref_I, ref_Q = acquire_one_pulse(self.AWG_inst, self.Alazar_ctrl, self.sig_gen, self.ref_gen, self.AWG_Config.Sig_freq, self.AWG_Config.Mod_freq, self.Alazar_config.SR)
                s = list(np.shape(sI_c))
                s[0] = int(s[0]//2) #evenly divided amongst I_plus and I_minus
                time_step = self.Alazar_config.SR/self.AWG_Config.Mod_freq
                writer.add_data(
                        record_num = np.repeat(np.arange(s[0]), s[1]),
                        time = np.tile(np.arange(int(s[1]))*time_step, s[0]),
                        I_plus = sI_c[0::2].flatten(),
                        Q_plus = sQ_c[0::2].flatten(),
                        I_minus = sI_c[1::2].flatten(),
                        Q_minus = sQ_c[1::2].flatten()
                        )
                
            self.post_measurement_operation(i)
        
        
        
    
    