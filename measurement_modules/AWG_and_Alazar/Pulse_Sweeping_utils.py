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
import matplotlib.pyplot as plt
import time

from itertools import product
    
def Standard_Alazar_Config(alazar_inst,alazar_dataclass):
    alazar = alazar_inst
    ad = alazar_dataclass
    
    with alazar.syncing():    
        # alazar.clock_source('INTERNAL_CLOCK')
        alazar.clock_source('EXTERNAL_CLOCK_10MHz_REF')
        alazar.sample_rate(1000000000)
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
        alazar.trigger_slope1('TRIG_SLOPE_NEGATIVE')
        alazar.trigger_level1(150)
        alazar.trigger_engine2('TRIG_ENGINE_K')
        alazar.trigger_source2('DISABLE')
        alazar.trigger_slope2('TRIG_SLOPE_POSITIVE')
        alazar.trigger_level2(128)
        alazar.external_trigger_coupling('DC')
        alazar.external_trigger_range('ETR_1V')
        alazar.trigger_delay(0)
        alazar.timeout_ticks(0)
        # alazar.aux_io_mode('AUX_IN_AUXILIARY') # AUX_IN_TRIGGER_ENABLE for seq mode on
        # alazar.aux_io_param('NONE') # TRIG_SLOPE_POSITIVE for seq mode on
    print("\nAlazar Configured\n")
    # Create the acquisition controller which will take care of the data handling and tell it which 
    # alazar instrument to talk to. Explicitly pass the default options to the Alazar.
    # Dont integrate over samples but avarage over records

    myctrl = ATSChannelController(name='my_controller', alazar_name='Alazar')
    myctrl.int_time(ad.record_time)
    myctrl.int_delay(0e-9)
    
    print("Samples per record: ",myctrl.samples_per_record())
    alazar.buffer_timeout.set(20000)
    
    rec_num = ad.record_num
    chan1 = AlazarChannel(myctrl, 'ChanA', demod=False, integrate_samples=False, average_records=False, average_buffers = True)
    chan1.alazar_channel('A')
    chan1.records_per_buffer(rec_num)
    chan1.num_averages(1)
    # chan1.prepare_channel() #save for later
    
    chan2 = AlazarChannel(myctrl, 'ChanB', demod=False, integrate_samples=False, average_records= False, average_buffers = True)
    chan2.alazar_channel('B')
    chan2.records_per_buffer(rec_num)
    chan2.num_averages(1)
    # chan2.prepare_channel() #save for later
    
    myctrl.channels.append(chan1)
    myctrl.channels.append(chan2)
    
    return myctrl        

class Phase_Parameter(Parameter): 
    def __init__(self, name, cavity_mimicking_pulse_class):
        # only name is required
        super().__init__(name)
        self._phase = cavity_mimicking_pulse_class.phase_rotation
        self.pulse_class = cavity_mimicking_pulse_class
        self.unit = 'rad'

    # you must provide a get method, a set method, or both.
    def get_raw(self):
        return self.pulse_class.phase_rotation

    def set_raw(self, val):
        self.pulse_class.phase_rotation = val
        self.create_and_load_awg_sequence()
        
    def create_and_load_awg_sequence(self):
        self.pulse_class.setup_pulse()
        
class repitition_parameter(Parameter): 
    def __init__(self, name):
        # only name is required
        super().__init__(name)
        self.unit = ''
        self.rep = 1
    # you must provide a get method, a set method, or both.
    def get_raw(self):
        return self.rep

    def set_raw(self, val):
        self.rep = val
        
class LO_Parameter(Parameter): 
    def __init__(self, name, RefGen, SigGen, Modulation_freq):
        # only name is required
        super().__init__(name)
        self._LO_frequency = SigGen.frequency()
        self.SigGen = SigGen
        self.RefGen = RefGen
        self.mod_freq = Modulation_freq
        self.unit = 'Hz'
        
    # you must provide a get method, a set method, or both.
    def get_raw(self):
        return self.SigGen.frequency()

    def set_raw(self, val):
        self.SigGen.frequency(val)
        self.RefGen.frequency(val+self.mod_freq)
        
class Voltage_Parameter(Parameter): 
    def __init__(self, name, cavity_mimicking_pulse_class):
        # only name is required
        super().__init__(name)
        self._amplitude = cavity_mimicking_pulse_class.amplitude
        self.pulse_class = cavity_mimicking_pulse_class
        self.unit = 'V'

    # you must provide a get method, a set method, or both.
    def get_raw(self):
        return self.pulse_class.amplitude

    def set_raw(self, val):
        self.pulse_class.amplitude = val
        self.create_and_load_awg_sequence()
        
    def create_and_load_awg_sequence(self):
        self.pulse_class.setup_pulse()
        
class Phase_Correction_Parameter(Parameter): 
    def __init__(self, name, cavity_mimicking_pulse_class):
        # only name is required
        super().__init__(name)
        self._phase_correction = cavity_mimicking_pulse_class.phase_correction
        self.pulse_class = cavity_mimicking_pulse_class
        self.unit = 'rad'

    # you must provide a get method, a set method, or both.
    def get_raw(self):
        return self.pulse_class.phase_correction

    def set_raw(self, val):
        self.pulse_class.phase_correction = val
        self.create_and_load_awg_sequence()
        
    def create_and_load_awg_sequence(self):
        self.pulse_class.setup_pulse()

class wait_time_parameter(Parameter): 
    def __init__(self, name, cavity_mimicking_pulse_class):
        # only name is required
        super().__init__(name)
        self._wait_time = cavity_mimicking_pulse_class.wait_time
        self.pulse_class = cavity_mimicking_pulse_class
        self.unit = 'us'

    # you must provide a get method, a set method, or both.
    def get_raw(self):
        return self.pulse_class.wait_time

    def set_raw(self, val):
        self.pulse_class.wait_time = val
        self.create_and_load_awg_sequence()
        
    def create_and_load_awg_sequence(self):
        self.pulse_class.setup_pulse()


    
def acquire_one_pulse(AWG_inst, Alazar_controller, mod_freq, sample_rate, debug = False): 
    print(f"Mod freq: {mod_freq}\nSample Rate: {sample_rate}")
    myctrl = Alazar_controller
    AWG = AWG_inst
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

from threading import Thread

def data_handler(data_storage_list, data_parameter): 
    print("dataThread acquiring data...")
    data_storage_list.append(data_parameter())
    print("dataThread acquisition complete")
    
def acquire_one_pulse_3_state(AWG_inst, Alazar_controller, mod_freq, sample_rate, debug = False): 
    print(f"Mod freq: {mod_freq}\nSample Rate: {sample_rate}")
    myctrl = Alazar_controller
    AWG = AWG_inst
    # AWG.ch1_m1_high(2.5)
    # AWG.ch1_m2_high(2.5)
    # AWG.ch2_m1_high(2.5)
    # AWG.ch2_m2_high(2.5)
    myctrl.channels[0].prepare_channel()
    myctrl.channels[1].prepare_channel()
    
    # time.sleep(15)
    #have to use multithreading to start the Alazar acquisition first, only THEN start the AWG
    #the problem is alazar acquisition blocks commands, hence the threading
    
    dataList = []
    dataThread = Thread(target = data_handler, args = (dataList, myctrl.channels.data))
    dataThread.start()
    sleep_time = 0.1
    print(f'Waiting for {sleep_time}s between AWG start and Alazar acquire')
    time.sleep(sleep_time) #hardcoded temp value. Need enough time to start the thread and prep the alazar
    AWG.run()
    #close the thread
    #wait a bit longer
    time.sleep(0.5)
    dataThread.join()
    if debug: 
        print("Data: ", dataList)
    ch1data, ch2data = dataList[0]
    
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
    # sI_c = sI
    # sQ_c = sQ
    # rI_trace = np.average(rI,axis = 1)
    # rQ_trace = np.average(rQ, axis = 1)

    return sI_c, sQ_c, rI_trace, rQ_trace

def acquire_one_pulse_finite_IF(AWG_inst, Alazar_controller, mod_freq, sample_rate, debug = False): 
    print(f"Mod freq: {mod_freq}\nSample Rate: {sample_rate}")
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
    # sI_c, sQ_c, rI_trace, rQ_trace = phase_correction(sI, sQ, rI, rQ)

    return sI, sQ, rI, rQ

class Pulse_Sweep(): 
    
    def __init__(self, 
                 name,
                 AWG, 
                 AWG_Config, 
                 Alazar_ctrl, 
                 Alazar_config, 
                 Sig_Gen, 
                 Ref_Gen): 
        
        '''
        Implicit in this file is the external interferometer, these components
        '''
        self.filename_prepend = name+'_'
        self.AWG_inst = AWG
        self.is_ind_par_set = False
        self.Alazar_ctrl = Alazar_ctrl
        # self.Alazar_ctrl = Standard_Alazar_Config(Alazar, Alazar_config)
        self.Alazar_config = Alazar_config
        self.AWG_Config = AWG_Config
        self.sig_gen = Sig_Gen
        self.ref_gen = Ref_Gen
        self.ind_par_dict_arr = []
        
    def add_independent_parameter(self, ind_par_dict: dict): 
        '''
        will take input in form of 
        ind_par_dict{name: dict(parameter = actual_parameter_class, vals = [np_val_arr])}
        '''
        self.ind_par_dict_arr.append(ind_par_dict)
        self.is_ind_par_set = True
    
    def filename_func(self, val_dict):
        '''
        takes in a dictionary where the parameters are the keys, and the vals are the setpoints
        eg {SigGen.power: dict('name' = str, 'val' = float))}
        '''
        filename = self.filename_prepend
        for name, val in val_dict.items(): 
            filename += (name+'_')
            filename += (str(np.round(val['val'], 3))+'_'+val['parameter'].unit + '_')
        return filename
    
    def pre_measurement_operation(self): 
        '''
        takes in a dictionary where the parameters are the keys, and the vals are the setpoints
        eg {name: dict(parameter = SigGen.power, 'val' = float))} 
        '''
        for name, val in self.setpoint_dict.items(): 
            val['parameter'](val['val'])
        print(f'Setting {name} to {val["val"]} {val["parameter"].unit}\nvia {val["parameter"].name}')
        self.sig_gen.output_status(1)
        self.ref_gen.output_status(1)

    def post_measurement_operation(self, i): 
        self.sig_gen.output_status(0)
        self.ref_gen.output_status(0)
        print(f"\nMeasurement {i+1} out of {np.shape(list(self.setpoint_arr))[0]} completed\n")
    
    def sweep(self, DATADIR, savemode = 'seperate', debug = False):
        
        if not self.is_ind_par_set: 
            raise Exception("Independent parameter not yet set. Run set_independent_parameter method")
        
        if savemode == 'seperate': 
            '''zip all the combos of parameters, names, units, and values to 
            iterate over, we want ONE loop to rule them all
            '''
            ind_par_names = []
            ind_par_parameters = []
            ind_par_vals = []
            for ind_par_dict in self.ind_par_dict_arr: 
                for name, info_dict in ind_par_dict.items(): 
                    ind_par_names.append(name)
                    ind_par_parameters.append(ind_par_dict[name]['parameter'])
                    ind_par_vals.append(ind_par_dict[name]['vals'])
                
            ################
            self.setpoint_arr = list(product(*ind_par_vals))
            for i, values in enumerate(self.setpoint_arr): 
                self.setpoint_dict = {}
                for j in range(np.size(values)):
                    self.setpoint_dict[ind_par_names[j]] = dict(parameter = ind_par_parameters[j], 
                                                           val = values[j])
                
                dep_var_dict = dict(time = dict(unit = 'ns'),
                                    record_num = dict(unit = 'num'),
                                    I_plus = dict(axes=['record_num', 'time' ], unit = 'V'),
                                    Q_plus = dict(axes=['record_num', 'time' ], unit = 'V'),
                                    I_minus = dict(axes=['record_num', 'time' ], unit = 'V'),
                                    Q_minus = dict(axes=['record_num', 'time' ], unit = 'V')
                                    )
                
                ####################### Set up the datadict
                self.datadict = dd.DataDict(**dep_var_dict)
                self.pre_measurement_operation()
                filename = self.filename_func(self.setpoint_dict)
                
                
                with dds.DDH5Writer(DATADIR, self.datadict, name=filename) as writer:
                    sI_c, sQ_c, ref_I, ref_Q = acquire_one_pulse(self.AWG_inst, self.Alazar_ctrl, self.AWG_Config.Mod_freq, self.Alazar_config.SR)

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
        
class Pulse_Sweep_finite_IF(): 
    
    def __init__(self, 
                 name,
                 AWG, 
                 AWG_Config, 
                 Alazar_ctrl, 
                 Alazar_config, 
                 Sig_Gen, 
                 Ref_Gen): 
        
        '''
        Implicit in this file is the external interferometer, these components
        '''
        self.filename_prepend = name+'_'
        self.AWG_inst = AWG
        self.is_ind_par_set = False
        self.Alazar_ctrl = Alazar_ctrl
        # self.Alazar_ctrl = Standard_Alazar_Config(Alazar, Alazar_config)
        self.Alazar_config = Alazar_config
        self.AWG_Config = AWG_Config
        self.sig_gen = Sig_Gen
        self.ref_gen = Ref_Gen
        self.ind_par_dict_arr = []
        
    def add_independent_parameter(self, ind_par_dict: dict): 
        '''
        will take input in form of 
        ind_par_dict{name: dict(parameter = actual_parameter_class, vals = [np_val_arr])}
        '''
        self.ind_par_dict_arr.append(ind_par_dict)
        self.is_ind_par_set = True
    
    def filename_func(self, val_dict):
        '''
        takes in a dictionary where the parameters are the keys, and the vals are the setpoints
        eg {SigGen.power: dict('name' = str, 'val' = float))}
        '''
        filename = self.filename_prepend
        for name, val in val_dict.items(): 
            filename += (name+'_')
            filename += (str(np.round(val['val'], 3))+'_'+val['parameter'].unit + '_')
        return filename
    
    def pre_measurement_operation(self): 
        '''
        takes in a dictionary where the parameters are the keys, and the vals are the setpoints
        eg {name: dict(parameter = SigGen.power, 'val' = float))} 
        '''
        for name, val in self.setpoint_dict.items(): 
            val['parameter'](val['val'])
        print(f'Setting {name} to {val["val"]} {val["parameter"].unit}\nvia {val["parameter"].name}')
        self.sig_gen.output_status(1)
        self.ref_gen.output_status(1)

    def post_measurement_operation(self, i): 
        self.sig_gen.output_status(0)
        self.ref_gen.output_status(0)
        print(f"\nMeasurement {i+1} out of {np.shape(list(self.setpoint_arr))[0]} completed\n")
    
    def sweep(self, DATADIR, savemode = 'seperate'):
        
        if not self.is_ind_par_set: 
            raise Exception("Independent parameter not yet set. Run set_independent_parameter method")
        
        if savemode == 'seperate': 
            '''zip all the combos of parameters, names, units, and values to 
            iterate over, we want ONE loop to rule them all
            '''
            ind_par_names = []
            ind_par_parameters = []
            ind_par_vals = []
            for ind_par_dict in self.ind_par_dict_arr: 
                for name, info_dict in ind_par_dict.items(): 
                    ind_par_names.append(name)
                    ind_par_parameters.append(ind_par_dict[name]['parameter'])
                    ind_par_vals.append(ind_par_dict[name]['vals'])
                
            ################
            self.setpoint_arr = list(product(*ind_par_vals))
            for i, values in enumerate(self.setpoint_arr): 
                self.setpoint_dict = {}
                for j in range(np.size(values)):
                    self.setpoint_dict[ind_par_names[j]] = dict(parameter = ind_par_parameters[j], 
                                                           val = values[j])
                
                dep_var_dict = dict(time = dict(unit = 'ns'),
                                    record_num = dict(unit = 'num'),
                                    I_plus = dict(axes=['record_num', 'time' ], unit = 'V'),
                                    Q_plus = dict(axes=['record_num', 'time' ], unit = 'V'),
                                    I_minus = dict(axes=['record_num', 'time' ], unit = 'V'),
                                    Q_minus = dict(axes=['record_num', 'time' ], unit = 'V')
                                    )
                
                ####################### Set up the datadict
                self.datadict = dd.DataDict(**dep_var_dict)
                self.pre_measurement_operation()
                filename = self.filename_func(self.setpoint_dict)
                
                
                with dds.DDH5Writer(DATADIR, self.datadict, name=filename) as writer:
                    
                    sI_c, sQ_c, ref_I, ref_Q = acquire_one_pulse_finite_IF(self.AWG_inst, self.Alazar_ctrl, self.AWG_Config.Mod_freq, self.Alazar_config.SR)
                    
                    
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
                    filepath = writer.file_path
                    
                self.post_measurement_operation(i)
                
                return filepath

class Pulse_Sweep_3_state(): 
    
    def __init__(self, 
                 name,
                 AWG, 
                 AWG_Config, 
                 Alazar_ctrl, 
                 Alazar_config, 
                 Sig_Gen, 
                 Ref_Gen): 
        
        '''
        Implicit in this file is the external interferometer
        '''
        self.filename_prepend = name+'_'
        self.AWG_inst = AWG
        self.is_ind_par_set = False
        self.Alazar_ctrl = Alazar_ctrl
        # self.Alazar_ctrl = Standard_Alazar_Config(Alazar, Alazar_config)
        self.Alazar_config = Alazar_config
        self.AWG_Config = AWG_Config
        self.sig_gen = Sig_Gen
        self.ref_gen = Ref_Gen
        self.ind_par_dict_arr = []
        
    def add_independent_parameter(self, ind_par_dict: dict): 
        '''
        will take input in form of 
        ind_par_dict{name: dict(parameter = actual_parameter_class, vals = [np_val_arr])}
        '''
        self.ind_par_dict_arr.append(ind_par_dict)
        self.is_ind_par_set = True
    
    def filename_func(self, val_dict):
        '''
        takes in a dictionary where the parameters are the keys, and the vals are the setpoints
        eg {SigGen.power: dict('name' = str, 'val' = float))}
        '''
        filename = self.filename_prepend
        for name, val in val_dict.items(): 
            filename += (name+'_')
            filename += (str(np.round(val['val'], 3))+'_'+val['parameter'].unit + '_')
        return filename
    
    def pre_measurement_operation(self): 
        '''
        takes in a dictionary where the parameters are the keys, and the vals are the setpoints
        eg {name: dict(parameter = SigGen.power, 'val' = float))} 
        '''
        for name, val in self.setpoint_dict.items(): 
            val['parameter'](val['val'])
        print(f'Setting {name} to {val["val"]} {val["parameter"].unit}\nvia {val["parameter"].name}')
        self.sig_gen.output_status(1)
        self.ref_gen.output_status(1)

    def post_measurement_operation(self, i): 
        self.sig_gen.output_status(0)
        self.ref_gen.output_status(0)
        print(f"\nMeasurement {i+1} out of {np.shape(list(self.setpoint_arr))[0]} completed\n")
    
    def sweep(self, DATADIR, savemode = 'seperate', debug = True):
        
        if not self.is_ind_par_set: 
            raise Exception("Independent parameter not yet set. Run set_independent_parameter method")
        
        if savemode == 'seperate': 
            '''zip all the combos of parameters, names, units, and values to 
            iterate over, we want ONE loop to rule them all
            '''
            ind_par_names = []
            ind_par_parameters = []
            ind_par_vals = []
            for ind_par_dict in self.ind_par_dict_arr: 
                for name, info_dict in ind_par_dict.items(): 
                    ind_par_names.append(name)
                    ind_par_parameters.append(ind_par_dict[name]['parameter'])
                    ind_par_vals.append(ind_par_dict[name]['vals'])
                
            ################
            self.setpoint_arr = list(product(*ind_par_vals))
            for i, values in enumerate(self.setpoint_arr): 
                self.setpoint_dict = {}
                for j in range(np.size(values)):
                    self.setpoint_dict[ind_par_names[j]] = dict(parameter = ind_par_parameters[j], 
                                                           val = values[j])
                
                dep_var_dict = dict(time = dict(unit = 'ns'),
                                    record_num = dict(unit = 'num'),
                                    I_G = dict(axes=['record_num', 'time' ], unit = 'V'),
                                    Q_G = dict(axes=['record_num', 'time' ], unit = 'V'),
                                    I_E = dict(axes=['record_num', 'time' ], unit = 'V'),
                                    Q_E = dict(axes=['record_num', 'time' ], unit = 'V'), 
                                    I_F = dict(axes=['record_num', 'time' ], unit = 'V'),
                                    Q_F = dict(axes=['record_num', 'time' ], unit = 'V')
                                    )
                
                ####################### Set up the datadict
                self.datadict = dd.DataDict(**dep_var_dict)
                self.pre_measurement_operation()
                filename = self.filename_func(self.setpoint_dict)
                
                
                with dds.DDH5Writer(DATADIR, self.datadict, name=filename) as writer:
                    sI_c, sQ_c, ref_I, ref_Q = acquire_one_pulse_3_state(self.AWG_inst, self.Alazar_ctrl, np.abs(self.AWG_Config.Mod_freq), self.Alazar_config.SR)
                    s = list(np.shape(sI_c))
                    s[0] = int(s[0]//3) #evenly divided amongst I_plus and I_minus
                    time_step = self.Alazar_config.SR/np.abs(self.AWG_Config.Mod_freq)
                    if debug: 
                        plt.figure()
                        plt.plot(ref_I)
                        plt.title("I")
                        plt.figure()
                        plt.plot(ref_Q)
                        plt.title("Q")
                        plt.figure()
                        plt.plot(np.mod(np.angle(ref_I+1j*ref_Q), 2*np.pi), '.')
                        plt.title("Phase")
                        print("sI_c shape: ", np.shape(sI_c))
                    num_records = np.shape(sI_c)[0]
                    if num_records%3 != 0: raise Exception("Number of records not divisible by 3")
                    rec_per_pulse = num_records//3
                    writer.add_data(
                            record_num = np.repeat(np.arange(s[0]), s[1]),
                            time = np.tile(np.arange(int(s[1]))*time_step, s[0]),
                            I_G = sI_c[0:rec_per_pulse].flatten(),
                            Q_G = sQ_c[0:rec_per_pulse].flatten(),
                            I_E = sI_c[rec_per_pulse:2*rec_per_pulse].flatten(),
                            Q_E = sQ_c[rec_per_pulse:2*rec_per_pulse].flatten(),
                            I_F = sI_c[2*rec_per_pulse:3*rec_per_pulse].flatten(),
                            Q_F = sQ_c[2*rec_per_pulse:3*rec_per_pulse].flatten()
                            )
                    
                self.post_measurement_operation(i)
    
    