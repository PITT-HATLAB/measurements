# -*- coding: utf-8 -*-
"""
Created on Thu Apr 29 09:40:12 2021

@author: Ryan Kaufman

Set up function module that can assist in loading pulse sequences into AWG
and functionalizing Alazar acquiring
"""
import numpy as np

from plottr.data import datadict_storage as dds, datadict as dd

from instrument_drivers.alazar_utilities.controller.ATSChannelController import ATSChannelController
from instrument_drivers.alazar_utilities.controller.alazar_channel import AlazarChannel
from qcodes.instrument.parameter import Parameter
from data_processing.signal_processing.Pulse_Processing import demod, phase_correction

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
        self.pulse_class.setup_pulse()

class LO_Parameter(Parameter): 
    def __init__(self, name, RefGen, SigGen, Modulation_freq):
        # only name is required
        super().__init__(name)
        self._LO_frequency = SigGen.frequency()
        self.SigGen = SigGen
        self.RefGen = RefGen
        self.mod_freq = Modulation_freq
        
    # you must provide a get method, a set method, or both.
    def get_raw(self):
        return self.SigGen.frequency()

    def set_raw(self, val):
        self.SigGen.frequency(val)
        self.RefGen.frequency(val+self.mod_freq)
        self.create_and_load_awg_sequence()
        
    def create_and_load_awg_sequence(self):
        self.pulse_class.setup_pulse()
        
class Voltage_Parameter(Parameter): 
    def __init__(self, name, cavity_mimicking_pulse_class):
        # only name is required
        super().__init__(name)
        self._amplitude = cavity_mimicking_pulse_class.amplitude
        self.pulse_class = cavity_mimicking_pulse_class

    # you must provide a get method, a set method, or both.
    def get_raw(self):
        return self.pulse_class.amplitude

    def set_raw(self, val):
        self.pulse_class.amplitude = val
        self.create_and_load_awg_sequence()
        
    def create_and_load_awg_sequence(self):
        self.pulse_class.setup_pulse()


    
def acquire_one_pulse(AWG_inst, Alazar_controller, mod_freq, sample_rate, debug = False): 

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

    return sI_c, sQ_c, rI_trace, rQ_trace

class Pulse_Sweep(): 
    
    def __init__(self, 
                 AWG: Tektronix_AWG5014, 
                 AWG_Config, 
                 Alazar_ctrl, 
                 Alazar_config, 
                 Sig_Gen, 
                 Ref_Gen): 
        
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
        self.ind_par_dict = []
        
    def add_independent_parameter(self, ind_par, points, filename = None): 

        self.ind_par_vals = points
        self.ind_par.append(ind_par)
        if filename == None: 
            self.filenames = [f'{ind_par.name}_{np.round(ind_par_val, 3)}' for ind_par_val in self.ind_par_vals]
        else: 
            self.filenames = [f'{filename}_{ind_par.name}_{np.round(ind_par_val, 3)}' for ind_par_val in self.ind_par_vals]
        
        self.is_ind_par_set = True
        
    def configure_datadict(independent_parameters, dependent_variables):
        
        
        
        
    def pre_measurement_operation(self, i): 
        self.ind_par(self.ind_par_vals[i])
        self.sig_gen.output_status(1)
        self.ref_gen.output_status(1)
        
    def post_measurement_operation(self, i): 
        self.sig_gen.output_status(0)
        self.ref_gen.output_status(0)
        print(f"\nMeasurement {i+1} out of {np.size(self.ind_par_vals)} completed\n")
    
    def sweep(self, DATADIR, savemode = 'seperate'):
        
        if not self.is_ind_par_set: 
            raise Exception("Independent parameter not yet set. Run set_independent_parameter method")
        
        if savemode == 'seperate': 
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
        
        
        
    
    