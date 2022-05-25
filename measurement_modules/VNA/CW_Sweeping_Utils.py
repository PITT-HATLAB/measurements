# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 11:55:20 2021

@author: Hatlab-RRK

Goal: Set up a place where I can define helpers for all VNA measurements

Ideally, I want to centralize the many, many sweep codes we (I) have laying
around
"""

import numpy as np

from plottr.data import datadict_storage as dds, datadict as dd
from itertools import product
import time
from qcodes.instrument.parameter import Parameter
from datetime import datetime
from scipy.interpolate import interp1d
from plottr.data.datadict_storage import all_datadicts_from_hdf5
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

#%%supporting parameters for the CW sweep class
class wrapped_current(Parameter):
    def __init__(self, current_par, set_func, ramp_rate = 0.1e-3): 
        super().__init__('current')
        self.current_par = current_par
        self.set_func = set_func
        self._ramp_rate = ramp_rate
    def get_raw(self): 
        return self.current_par()
    
    def set_raw(self, val): 
        return self.set_func(val, ramp_rate = self._ramp_rate)
    
class amplifier_bias(Parameter): 
    '''
    purpose: 
        create an independent parameter that can integrate duffing tests into the functionality of cw_sweep
        
        what this means is that it will take info from a fluxsweep fit and use that to change the generator frequency
        according to the current that the user is sweeping.
    '''
    def __init__(self, current_par, generator_freq_par, fs_fit_filepath, gen_offset = 500e6, gen_factor = 1, norm = 0, VNA_inst = None): 
        super().__init__('bias_current')
        self._current_par = current_par
        self.fs_fit_func = self.read_fs_data(fs_fit_filepath)
        self._generator_freq_par = generator_freq_par
        self._gen_offset = gen_offset
        self._gen_factor = gen_factor
        self.VNA_inst = VNA_inst
        self._norm = norm
        
    def read_fs_data(self, fs_filepath, interpolation = 'linear'):
        ret = all_datadicts_from_hdf5(fs_filepath)
        res_freqs = ret['data'].extract('base_resonant_frequency').data_vals('base_resonant_frequency')
        currents = ret['data'].extract('base_resonant_frequency').data_vals('current')
        fs_fit_func = interp1d(currents, res_freqs, interpolation)
        return fs_fit_func
    
    def get_raw(self): 
        return self._current_par()
        
    def set_raw(self, val): 
        self._current_par(val)
        self._generator_freq_par(self.fs_fit_func(val)*self._gen_factor+self._gen_offset)
        if self._norm: 
            self.VNA_inst.renormalize(3*self.VNA_inst.avgnum())
    
    def preview_range(self, currents, show_pump = False): 
        fig, ax = plt.subplots(1,1)
        
        ax.plot(currents*1000, self.fs_fit_func(currents), label = 'Amp_res')
        if show_pump: 
            ax.plot(currents*1000, self.fs_fit_func(currents)*self._gen_factor+self._gen_offset, label = 'Generator')
        ax.set_xlabel('Bias currents (mA)')
        ax.set_ylabel('Frequency (GHz)')
        ax.legend()
        ax.grid()
        
class generator_detuning(Parameter): 
    '''
    Purpose: 
    Now that I can track resonant frequency, I need a seperate parameter that can also detune the generator from a setpoint. This is different than the previous parameter because it needs to output the generator frequency from the get_raw function, NOT a current
    '''
    
    def __init__(self, generator_freq_par):
        super().__init__('bias_current')
        self._generator_freq_par = generator_freq_par
        self.last_val = 0
        
    def get_raw(self): 
        # return self._generator_freq_par()
        return self.last_val
    
    def set_raw(self, val):
        self.last_val = val
        self._generator_freq_par(self._generator_freq_par()+val)
        
class Time(Parameter):
    '''
    Purpose: 
        create a parameter that can wait between taking data to check for things like stability over time
    '''
    def __init__(self): 
        super().__init__('record_time')
        self.time_stored = 0
    def get_raw(self): 
        return self.time_stored
    
    def set_raw(self, val):
        time.sleep(val)
        self.time_stored = datetime.timestamp(datetime.now())
        
class gradient_stepper_gain_curve():
    
    '''
    The CWSP class keeps track of its last data point. That's all this parameter should need to generate a gradient, and extrapolate on the value. The idea is that  we can record d(cost)/dp where p is the parameter we can change
    '''
    def __init__(self, CWSWP, stepping_parameter,  mode = 'Gain', init_scale = 10): 
        super().__init__('bias_current')
        self.CWSWP = CWSWP
        self._opt_par = stepping_parameter
        self.step_size = stepping_parameter
        self.gain_func = lambda x, G, f, bw: G/(1+((x-f)/bw)**2)
        self.starting_parameters = None
        self.init_scale = init_scale
        
    def fit_gain(self): 
        freqs, [mag, phase] = self.CWSWP.last_vna_data
        popt, pcov = curve_fit(self.gain_func, freqs, mag)
        G, f, bw = popt
        if self.starting_parameters is None:
            self.last_parameters = popt
        return popt
    def get_raw(self): 
        return self._opt_par()
    
    def set_raw(self, val): 
        '''
        this will set off the changing of the stepping parameter, limited by the magnitude of val
        '''
        #calculate the gradient of gain, in the case of the gain curve, positive is good and negative is bad
        self.active_parameters = self.fit_gain()
        
        self.dp = self.active_parameters-self.passive_parameters
        
        if self.dp == 0: 
            #this means we have to initialize, so we should step by some initial value and get an idea of how things change locally around here
            self.stepping_parameter(val/self.init_scale)
        else:
            None
            
    
    
        
        
#%% core class
class CW_sweep(): 
    """
    One class to unify all non-adaptive CW measurements
    e.g. gen power, gen frequency, vna power, vna_frequency sweeps
    - add independent parameters dynamically (!)
    """
    def __init__(self, 
                 name,
                 mode, 
                 VNA_inst = None, 
                 SA_inst = None, 
                 Gen_arr = []): 
        
        self.sweep_name = name+'_'+mode
        self.mode = mode
        
        self.VNA_inst = VNA_inst
        self.VNA_mode = 'NOT_SET'
        
        self.SA_inst = SA_inst
        
        self.Gen_inst_arr = Gen_arr
        self.ind_par_dict_arr = []
        self.is_ind_par_set = False
        
        self.last_vna_data = None
        self.last_SA_data = None
        
    def add_independent_parameter(self, ind_par_dict: dict): 
        '''
        will take input in form of 
        ind_par_dict{name: dict(parameter = actual_parameter_class, vals = [np_val_arr])}
        '''
        self.ind_par_dict_arr.append(ind_par_dict)
        self.is_ind_par_set = True
        
    def setup_VNA(self, sweep_mode, start, stop, points, normalize = False):
        '''
        Function for setting the primary indpendent variable of the VNA, and also the window of that variable
        
        e.g. for a frequency sweep,
        VNA.set_mode('FREQ')
        VNA.fstart()
        VNA.fstop()
        VNA.fpoints()
        VNA.avgnum(10)

        '''
        self.VNA_mode = [sweep_mode.upper() if sweep_mode.upper() == 'POW' or 'FREQ' else 'WRONG_INPUT'][0]
        self.vna_normalize = normalize
        if self.VNA_mode == 'FREQ': 
            self.VNA_inst.sweep_type('LIN')
            self.VNA_inst.fstart(start)
            self.VNA_inst.fstop(stop)
            self.VNA_inst.num_points(points)
            
        elif self.VNA_mode == 'POW': 
            self.VNA_inst.sweep_type('POW')
            self.VNA_inst.power_start(start)
            self.VNA_inst.power_stop(stop)
            self.VNA_inst.num_points(points)
        elif self.VNA_mode == 'WRONG_INPUT': 
            raise Exception('Wrong user input, either "POW" or "FREQ"')
    def setup_SA(self, start, stop):
        '''
        Function for setting up the SA
        '''

        self.SA_inst.fstart(start)
        self.SA_inst.fstop(stop)

        
    def VNA_parameter_name(self): 
        if self.VNA_mode == 'FREQ': 
            return 'vna_frequency'
        elif self.VNA_mode == 'POW': 
            return 'vna_input_power'
        else: 
            raise Exception(f'VNA mode not correct: ({self.VNA_mode})')
        
    def make_datadict(self, mode):
        '''
        use the independent variables supplied by CW_sweep.add_independent_variables 
        
        and assume the dependent variables are either (vna phase, vna power),  Spectrum PSD, or both
        '''
        
        # print(self.ind_par_dict_arr)
        axes_arr = [ind_par_dict['name'] for ind_par_dict in self.ind_par_dict_arr]
        
        dd_ind_var_dict = dict()
        for ind_par_dict in self.ind_par_dict_arr: 
            dd_ind_var_dict[ind_par_dict['name']] = dict(unit = ind_par_dict['parameter'].unit)
        
        if mode == 'VNA': 
            if self.VNA_mode == 'FREQ': 
                axes_arr.append(self.VNA_parameter_name())
                dd_ind_var_dict[self.VNA_parameter_name()] = dict(unit = 'Hz')
                dd_dep_var_dict = dict(vna_phase = dict(axes = axes_arr, unit = 'Rad'),
                                       vna_power = dict(axes = axes_arr, unit = 'dB')                                   
                                       )
            if self.VNA_mode == 'POW': 
                axes_arr.append(self.VNA_parameter_name())
                dd_ind_var_dict[self.VNA_parameter_name()] = dict(unit = 'dB')
                dd_dep_var_dict = dict(vna_phase = dict(axes = axes_arr, unit = 'Rad'),
                                       vna_power = dict(axes = axes_arr, unit = 'dB')                                   
                                       )
        if mode == 'SA': 
            axes_arr.append('spec_frequency')
            dd_ind_var_dict['spec_frequency'] = dict(unit = 'Hz')
            dd_dep_var_dict = dict(spec_power = dict(axes = axes_arr, unit = 'dBm'))
            
        assert self.is_ind_par_set == True
        
        return  dd.DataDict(**(dd_ind_var_dict | dd_dep_var_dict)) 
    
    def pre_measurement_operation(self):
        '''
        function that handles preparation for that particular setpoint of the experiment
        Adding dependency on the setpoint dictionary (stored in self) lets you make adjustments to the measurement, 
        e.g. changing the vna window for a Duffing Test or fluxsweep
        
        But this should NOT be done in this class, you should create another class that subclasses this 
        one (CW_Sweeps), then write a method that overrides this one
        '''
        # print(f'Setting {name} to {val["val"]} {val["parameter"].unit}\nvia {val["parameter"].name}')
        
        #TODO: this sucks! Make it better, general try except loops are dangerous
        [Gen.output_status(1) if Gen is not None else '' for Gen in self.Gen_inst_arr]
        print("Current parameters: ")
        [print(key,': ', val['val'], val['parameter'].unit) for key, val in self.setpoint_dict.items()]

    def post_measurement_operation(self, i): 
        '''
        very similar to pre_measurement_operation, this can be overridden 
        in a subclass to do smarter sweeps
        '''
        print(f"\nMeasurement {i+1} out of {np.shape(list(self.setpoint_arr))[0]} completed\n")
        
        if i+1 == np.shape(list(self.setpoint_arr))[0]: #the sweep is done
            [Gen.output_status(0) if Gen is not None else '' for Gen in self.Gen_inst_arr]
    def eta(self): 
        ind_par_names = []
        ind_par_parameters = []
        ind_par_vals = []
        for ind_par_dict in self.ind_par_dict_arr: 
            ind_par_names.append(ind_par_dict['name'])
            ind_par_parameters.append(ind_par_dict['parameter'])
            ind_par_vals.append(ind_par_dict['vals'])
        setpoint_arr = list(product(*ind_par_vals))
        size = np.shape(setpoint_arr)[0]
        if self.mode == 'VNA':
            print(f"ETA with 10 averages: {np.round(self.VNA_inst.sweep_time()*size/60*10)} minutes")
        
        if self.mode == 'both':
            print(f"ETA with 10 averages: {np.round(self.VNA_inst.sweep_time()*size/60*10+size*self.SA_inst.sweep_time()*500/60)}")
        
    def sweep(self, DATADIR, debug = True, VNA_avgnum = 10, SA_avgnum = 400):
        #TODO: hack this into more managable chunks
        if not self.is_ind_par_set: 
            raise Exception("Independent parameter not yet set. Run set_independent_parameter method")
            
        #preprocess the independent variables that are set in CW.add_independent_variable
        ind_par_names = []
        ind_par_parameters = []
        ind_par_vals = []
        for ind_par_dict in self.ind_par_dict_arr: 
            ind_par_names.append(ind_par_dict['name'])
            ind_par_parameters.append(ind_par_dict['parameter'])
            ind_par_vals.append(ind_par_dict['vals'])
    
        if self.mode == 'VNA' or self.mode == 'both': 
            self.vna_datadict =self.make_datadict(mode = 'VNA')
            self.vna_writer = dds.DDH5Writer(DATADIR, self.vna_datadict, name=self.sweep_name+'_VNA')
            self.vna_writer.__enter__()
            self.vna_savepath = self.vna_writer.file_path
        
        else: 
            self.vna_savepath = None
            
        if self.mode == 'SA' or self.mode == 'both': 
            self.sa_datadict =self.make_datadict(mode = 'SA')
            self.sa_writer = dds.DDH5Writer(DATADIR, self.sa_datadict, name=self.sweep_name+'_SA')
            self.sa_writer.__enter__()
            self.sa_savepath = self.sa_writer.file_path
        else: 
            self.sa_savepath = None
        '''
        each combination of independent variable values creates a 
        "setpoint" which defines a place in parameter space where the 
        minimal unit of data is taken. This is used to input the ind var
        info into the writer
        '''
        
        self.setpoint_arr = list(product(*ind_par_vals))
        
        for i, values in enumerate(self.setpoint_arr): 
            self.setpoint_dict = {}
            for j in range(np.size(values)):
                self.setpoint_dict[ind_par_names[j]] = dict(parameter = ind_par_parameters[j], 
                                                       val = values[j])

            ####################### Prepare for taking data
            self.pre_measurement_operation()
            #setting independent parameter values
            for name, val in self.setpoint_dict.items(): 
                val['parameter'](val['val'])
            
            if self.mode == 'VNA' or self.mode == 'both': 
                if debug: print("\nVNA measuring\n")
                vna_ind_var = self.VNA_inst.getSweepData() #this could also be a power... fuck
                vna_data = self.VNA_inst.average(VNA_avgnum)
                
                self.last_vna_data = [vna_ind_var, vna_data]
                vna_power = vna_data[0]
                vna_phase = vna_data[1]
                d = np.shape(vna_data)[1]
    
                vna_writer_dict = {}
                
                for ind_par_dict in self.ind_par_dict_arr:
                    vna_writer_dict[ind_par_dict['name']] = ind_par_dict['parameter']()*np.ones(d) 
                    #^^asks the instrument for an update, resize for plottr
                
                #this does both power and freq sweeps. Neat, huh?
                vna_writer_dict[self.VNA_parameter_name()] = vna_ind_var
                
                #add the dependent data...
                vna_writer_dict['vna_power'] = vna_power
                vna_writer_dict['vna_phase'] = vna_phase
                
                self.vna_writer.add_data(**vna_writer_dict)
                
            if self.mode == 'SA' or self.mode == 'both': 
                if debug: print("\nSA measuring\n")
                sa_data = self.SA_inst.get_data(count = SA_avgnum)
                sa_freqs = sa_data[:,  0]
                sa_power = sa_data[:,  1]
                
                self.last_sa_data = [sa_freqs,sa_power]
                d = np.size(sa_freqs)
    
                sa_writer_dict = {}
                
                for ind_par_dict in self.ind_par_dict_arr: 
                    sa_writer_dict[ind_par_dict['name']] = ind_par_dict['parameter']()*np.ones(d) 
                
                sa_writer_dict['spec_frequency'] = sa_freqs
                
                #add the dependent data...
                sa_writer_dict['spec_power'] = sa_power
                
                self.sa_writer.add_data(**sa_writer_dict)

            self.post_measurement_operation(i)
        
        if self.mode == 'SA' or self.mode == 'both': 
            self.sa_writer.file.close()
        
        if self.mode == 'VNA' or self.mode == 'both': 
            self.vna_writer.file.close()
            
        return self.vna_savepath, self.sa_savepath
    
# class CW_stepper_sweep(): 
#     """
#     One class to unify all adaptive CW measurements
#     e.g. gen power, gen frequency, vna power, vna_frequency sweeps
#     - add independent parameters dynamically
    
#     this is fundamentally different, because the goal is to scan through a single
#     primary independent variable with optimized secondary independent variables
#     as opposed to scanning through every independent variable
    
#     if done right, it should save a lot of time by reducing the effective dimension 
#     of the data to only the primary independent variable if the optimization
#     time is short
#     """
#     def __init__(self, 
#                  name,
#                  mode, 
#                  VNA_inst = None, 
#                  SA_inst = None, 
#                  Gen_arr = []): 
        
#         self.sweep_name = name+'_'+mode
#         self.mode = mode
        
#         self.VNA_inst = VNA_inst
#         self.VNA_mode = 'NOT_SET'
        
#         self.SA_inst = SA_inst
        
#         self.Gen_inst_arr = Gen_arr
#         self.ind_par_dict_arr = []
#         self.is_ind_par_set = False
        
#     def add_independent_parameter(self, ind_par_dict: dict): 
#         '''
#         will take input in form of 
#         ind_par_dict{name: dict(parameter = actual_parameter_class, vals = [np_val_arr])}
#         '''
        
#         self.prim_ind_par_dict_arr.append(ind_par_dict)
#         self.is_prim_ind_par_set = True
    
#     def add_optimization_parameter(self, opt_par_dict: dict):
#         '''
#         this adds a variable that is optimized with the provided evaluation function
#         for every combination of independent parameters
        
#         format of opt_par_dict: 
#         opt_par_dict = {name = str, 
#                         parameter = gettable_and_settable_parameter
#                         eval_func = function(CW_AD_SWP.measurement)}
#         #the evaluation function takes in the whole
#         '''
#     def _measure(): 
        
#         return
#     def setup_VNA(self, sweep_mode, start, stop, points):
#         '''
#         Function for setting the primary indpendent variable of the VNA, and also the window of that variable
        
#         e.g. for a frequency sweep,
#         VNA.set_mode('FREQ')
#         VNA.fstart()
#         VNA.fstop()
#         VNA.fpoints()
#         VNA.avgnum(10)

#         '''
#         self.VNA_mode = [sweep_mode.upper() if sweep_mode.upper() == 'POW' or 'FREQ' else 'WRONG_INPUT'][0]
        
#         if self.VNA_mode == 'FREQ': 
#             self.VNA_inst.sweep_type('LIN')
#             self.VNA_inst.fstart(start)
#             self.VNA_inst.fstop(stop)
#             self.VNA_inst.num_points(points)
            
#         elif self.VNA_mode == 'POW': 
#             self.VNA_inst.sweep_type('POW')
#             self.VNA_inst.power_start(start)
#             self.VNA_inst.power_stop(stop)
#             self.VNA_inst.num_points(points)
#         elif self.VNA_mode == 'WRONG_INPUT': 
#             raise Exception('Wrong user input, either "POW" or "FREQ"')
#     def setup_SA(self, start, stop):
#         '''
#         Function for setting up the SA
#         '''

#         self.SA_inst.fstart(start)
#         self.SA_inst.fstop(stop)

        
#     def VNA_parameter_name(self): 
#         if self.VNA_mode == 'FREQ': 
#             return 'vna_frequency'
#         elif self.VNA_mode == 'POW': 
#             return 'vna_power'
#         else: 
#             raise Exception(f'VNA mode not correct: ({self.VNA_mode})')
        
#     def make_datadict(self, mode):
#         '''
#         use the independent variables supplied by CW_sweep.add_independent_variables 
        
#         and assume the dependent variables are either (vna phase, vna power),  Spectrum PSD, or both
#         '''
        
#         print(self.ind_par_dict_arr)
#         axes_arr = [ind_par_dict['name'] for ind_par_dict in self.ind_par_dict_arr]
        
#         dd_ind_var_dict = dict()
#         for ind_par_dict in self.ind_par_dict_arr: 
#             dd_ind_var_dict[ind_par_dict['name']] = dict(unit = ind_par_dict['parameter'].unit)
        
#         if mode == 'VNA': 
#             if self.VNA_mode == 'FREQ': 
#                 axes_arr.append(self.VNA_parameter_name())
#                 dd_ind_var_dict[self.VNA_parameter_name()] = dict(unit = 'Hz')
#                 dd_dep_var_dict = dict(vna_phase = dict(axes = axes_arr, unit = 'Rad'),
#                                        vna_power = dict(axes = axes_arr, unit = 'dB')                                   
#                                        )
#         if mode == 'SA': 
#             axes_arr.append('spec_frequency')
#             dd_ind_var_dict['spec_frequency'] = dict(unit = 'Hz')
#             dd_dep_var_dict = dict(spec_power = dict(axes = axes_arr, unit = 'dBm'))
            
#         assert self.is_ind_par_set == True
        
#         return  dd.DataDict(**(dd_ind_var_dict | dd_dep_var_dict)) 
    
#     def pre_measurement_operation(self):
#         '''
#         function that handles preparation for that particular setpoint of the experiment
#         Adding dependency on the setpoint dictionary (stored in self) lets you make adjustments to the measurement, 
#         e.g. changing the vna window for a Duffing Test or fluxsweep
        
#         But this should NOT be done in this class, you should create another class that subclasses this 
#         one (CW_Sweeps), then write a method that overrides this one
#         '''
#         # print(f'Setting {name} to {val["val"]} {val["parameter"].unit}\nvia {val["parameter"].name}')
        
#         #TODO: this sucks! Make it better, general try except loops are dangerous
#         [Gen.output_status(1) if Gen is not None else '' for Gen in self.Gen_inst_arr]
#         print("Current parameters: ")
#         [print(key,': ', val) for key, val in self.setpoint_dict.items()]

#     def post_measurement_operation(self, i): 
#         '''
#         very similar to pre_measurement_operation, this can be overridden 
#         in a subclass to do smarter sweeps
#         '''
#         print(f"\nMeasurement {i+1} out of {np.shape(list(self.setpoint_arr))[0]} completed\n")
        
#         if i+1 == np.shape(list(self.setpoint_arr))[0]: #the sweep is done
#             [Gen.output_status(0) if Gen is not None else '' for Gen in self.Gen_inst_arr]
    
#     def sweep(self, DATADIR, debug = True, VNA_avgnum = 10, SA_avgnum = 400):
#         #TODO: hack this into more managable chunks
#         if not self.is_ind_par_set: 
#             raise Exception("Independent parameter not yet set. Run set_independent_parameter method")
            
#         #preprocess the independent variables that are set in CW.add_independent_variable
#         ind_par_names = []
#         ind_par_parameters = []
#         ind_par_vals = []
#         for ind_par_dict in self.ind_par_dict_arr: 
#             ind_par_names.append(ind_par_dict['name'])
#             ind_par_parameters.append(ind_par_dict['parameter'])
#             ind_par_vals.append(ind_par_dict['vals'])
    
#         if self.mode == 'VNA' or self.mode == 'both': 
#             self.vna_datadict =self.make_datadict(mode = 'VNA')
#             self.vna_writer = dds.DDH5Writer(DATADIR, self.vna_datadict, name=self.sweep_name+'_VNA')
#             self.vna_writer.__enter__()
#             self.vna_savepath = self.vna_writer.file_path
        
#         else: 
#             self.vna_savepath = None
            
#         if self.mode == 'SA' or self.mode == 'both': 
#             self.sa_datadict =self.make_datadict(mode = 'SA')
#             self.sa_writer = dds.DDH5Writer(DATADIR, self.sa_datadict, name=self.sweep_name+'_SA')
#             self.sa_writer.__enter__()
#             self.sa_savepath = self.sa_writer.file_path
#         else: 
#             self.sa_savepath = None
#         '''
#         each combination of independent variable values creates a 
#         "setpoint" which defines a place in parameter space where the 
#         minimal unit of data is taken. This is used to input the ind var
#         info into the writer
#         '''
        
#         self.setpoint_arr = list(product(*ind_par_vals))
        
#         for i, values in enumerate(self.setpoint_arr): 
#             self.setpoint_dict = {}
#             for j in range(np.size(values)):
#                 self.setpoint_dict[ind_par_names[j]] = dict(parameter = ind_par_parameters[j], 
#                                                        val = values[j])

#             ####################### Prepare for taking data
#             self.pre_measurement_operation()
#             #setting independent parameter values
#             for name, val in self.setpoint_dict.items(): 
#                 # try: 
#                 print(name, val)
#                 val['parameter'](val['val'])
#                 # except: 
#                     # print(name, val)
#             #taking data with VNA, SA, or both
            
#             if self.mode == 'VNA' or self.mode == 'both': 
#                 if debug: print("\nVNA measuring\n")
#                 vna_ind_var = self.VNA_inst.getSweepData() #this could also be a power... fuck
#                 vna_data = self.VNA_inst.average(VNA_avgnum)
#                 vna_power = vna_data[0]
#                 vna_phase = vna_data[1]
#                 d = np.shape(vna_data)[1]
    
#                 vna_writer_dict = {}
                
#                 for ind_par_dict in self.ind_par_dict_arr:
#                     vna_writer_dict[ind_par_dict['name']] = ind_par_dict['parameter']()*np.ones(d) 
#                     #^^asks the instrument for an update, resize for plottr
                
#                 #this does both power and freq sweeps. Neat, huh?
#                 vna_writer_dict[self.VNA_parameter_name()] = vna_ind_var
                
#                 #add the dependent data...
#                 vna_writer_dict['vna_power'] = vna_power
#                 vna_writer_dict['vna_phase'] = vna_phase
                
#                 self.vna_writer.add_data(**vna_writer_dict)
                
#             if self.mode == 'SA' or self.mode == 'both': 
#                 if debug: print("\nSA measuring\n")
#                 sa_data = self.SA_inst.get_data(count = SA_avgnum)
#                 sa_freqs = sa_data[:,  0]
#                 sa_power = sa_data[:,  1]
#                 d = np.size(sa_freqs)
    
#                 sa_writer_dict = {}
                
#                 for ind_par_dict in self.ind_par_dict_arr: 
#                     sa_writer_dict[ind_par_dict['name']] = ind_par_dict['parameter']()*np.ones(d) 
                
#                 sa_writer_dict['spec_frequency'] = sa_freqs
                
#                 #add the dependent data...
#                 sa_writer_dict['spec_power'] = sa_power
                
#                 self.sa_writer.add_data(**sa_writer_dict)

#             self.post_measurement_operation(i)
        
#         if self.mode == 'SA' or self.mode == 'both': 
#             self.sa_writer.file.close()
        
#         if self.mode == 'VNA' or self.mode == 'both': 
#             self.vna_writer.file.close()
            
#         return self.vna_savepath, self.sa_savepath
    
# class TACO_sweep(CW_sweep): 
#     def __init__(self, 
#                  name,
#                  mode, 
#                  **kwargs): 
#         super().__init__(self, name, mode, **kwargs)
#         '''
#         at this point you have an identical class to CW Sweeps, 
#         but now we can overwrite some functions to make it adaptive
#         '''

#     def _make_vna_writer(self, DATADIR): 
#         if self.mode == 'VNA' or self.mode == 'both': 
#             self.vna_datadict =self.make_datadict(mode = 'VNA')
#             self.vna_writer = dds.DDH5Writer(DATADIR, self.vna_datadict, name=self.sweep_name+'_VNA')
#             self.vna_writer.__enter__()
#             self.vna_savepath = self.vna_writer.file_path
#         else: 
#             self.vna_savepath = None
            
#     def _make_SA_writer(self, DATADIR): 
#         if self.mode == 'SA' or self.mode == 'both': 
#             self.sa_datadict =self.make_datadict(mode = 'SA')
#             self.sa_writer = dds.DDH5Writer(DATADIR, self.sa_datadict, name=self.sweep_name+'_SA')
#             self.sa_writer.__enter__()
#             self.sa_savepath = self.sa_writer.file_path
#         else: 
#             self.sa_savepath = None
            
#     def _eval_func(self):
#         self.measure_gain(self.setpoint_dict)
#         return 
    
    
#     def _stepper(self, stepping_var, eval_func): 
#         '''
#         This function should step the stepping variable until 
#         the method eval func returns true
#         '''
#         def change(): 
#             pass
#         while not eval_func(): 
#             change(stepping_var)

#     def sweep(self, DATADIR, debug = True, VNA_avgnum = 10, SA_avgnum = 400): 
#         '''
#         we need to hack up the CW sweep function into more managable chunks
#         '''
#         if not self.is_ind_par_set: 
#             raise Exception("Independent parameter not yet set. Run set_independent_parameter method")
            
#         self._make_vna_writer(DATADIR)
#         self._make_sa_writer(DATADIR)

#         '''
#         each combination of independent variable values creates a 
#         "setpoint" which defines a place in parameter space where the 
#         minimal unit of data is taken. This is used to input the ind var
#         info into the writer
#         '''
        
#         '''
#         now we generate the initial setpoint array, much like the sweep function
#         as before, but the difference is that the user only inputs the current
#         values into add_independet_parameter, so there is actually only one tuple in setpoint_arr
#         for everything EXCEPT current, which is 1xn
#         '''
#         ind_par_names = []
#         ind_par_parameters = []
#         ind_par_vals = []
#         for ind_par_dict in self.ind_par_dict_arr: 
#             ind_par_names.append(ind_par_dict['name'])
#             ind_par_parameters.append(ind_par_dict['parameter'])
#             ind_par_vals.append(ind_par_dict['vals'])
        
#         self.setpoint_arr = list(product(*ind_par_vals))
        
#         for i, values in enumerate(self.setpoint_arr): 
            
#             '''
#             generate the current setpoint, 
#             this is where we need the steppers and the memory of the last step
#             '''
            
#             self.setpoint_dict = {}
#             for j in range(np.size(values)):
#                 self.setpoint_dict[ind_par_names[j]] = dict(parameter = ind_par_parameters[j], 
#                                                        val = values[j])

#             ####################### Prepare for taking data
#             self.pre_measurement_operation()
#             #setting independent parameter values
#             for name, val in self.setpoint_dict.items(): 
#                 # try: 
#                 print(name, val)
#                 val['parameter'](val['val'])
#                 # except: 
#                     # print(name, val)
#             #taking data with VNA, SA, or both
            
#             if self.mode == 'VNA' or self.mode == 'both':
#                 self.VNA_inst.rfout(1)
#                 if debug: print("\nVNA measuring\n")
#                 vna_ind_var = self.VNA_inst.getSweepData() 
#                 vna_data = self.VNA_inst.average(VNA_avgnum)
#                 vna_power = vna_data[0]
#                 vna_phase = vna_data[1]
#                 d = np.shape(vna_data)[1]
    
#                 vna_writer_dict = {}
                
#                 for ind_par_dict in self.ind_par_dict_arr:
#                     vna_writer_dict[ind_par_dict['name']] = ind_par_dict['parameter']()*np.ones(d) #asks the instrument for an update, resize for plottr
                
#                 vna_writer_dict[self.VNA_parameter_name()] = vna_ind_var
                
#                 #add the dependent data...
#                 vna_writer_dict['vna_power'] = vna_power
#                 vna_writer_dict['vna_phase'] = vna_phase
                
#                 self.vna_writer.add_data(**vna_writer_dict)
                
#                 self.VNA_inst.rfout(0)
                
#             if self.mode == 'SA' or self.mode == 'both': 
#                 if debug: print("\nSA measuring\n")
#                 sa_data = self.SA_inst.get_data(count = SA_avgnum)
#                 sa_freqs = sa_data[:,  0]
#                 sa_power = sa_data[:,  1]
#                 d = np.size(sa_freqs)
    
#                 sa_writer_dict = {}
                
#                 for ind_par_dict in self.ind_par_dict_arr:
#                     sa_writer_dict[ind_par_dict['name']] = ind_par_dict['parameter']()*np.ones(d) #asks the instrument for an update, resize for plottr
                
#                 #I need to find a way to incorporate power sweeps into this too. for now, just frequency
#                 sa_writer_dict['spec_frequency'] = sa_freqs
                
#                 #add the dependent data...
#                 sa_writer_dict['spec_power'] = sa_power
                
#                 self.sa_writer.add_data(**sa_writer_dict)

#             self.post_measurement_operation(i)
        
        
        
#         if self.mode == 'SA' or self.mode == 'both': 
#             self.sa_writer.file.close()
        
#         if self.mode == 'VNA' or self.mode == 'both': 
#             self.vna_writer.file.close()
        
        
        
        
        
        
        
        
        
        
        
        
        