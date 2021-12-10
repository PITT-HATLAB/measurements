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


class CW_sweep(): 
    """
    One class to unify all non-adaptive CW measurements"
    - add independent parameters dynamically
    - calibrate automatically to stored IO line attenuations
    """
    def __init__(self, 
                 name,
                 mode, 
                 VNA_inst = None, 
                 SA_inst = None, 
                 Gen_arr = []): 
        
        self.filename_prepend = name+'_'
        self.mode = mode
        
        if mode == 'VNA': 
            self.VNA_inst = VNA_inst
        if mode == 'SA': 
            self.SA_inst = SA_inst
        
        self.Gen_inst_arr = Gen_arr
        self.ind_par_dict_arr = []
        self.is_ind_par_set = False
        
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
        # for name, val in val_dict.items(): 
        #     filename += (name+'_')
        #     filename += (str(np.round(val['val'], 3))+'_'+val['parameter'].unit + '_')
        return filename
    
    def pre_measurement_operation(self): 
        '''
        function that handles preparation for the experiment
        '''
        # print(f'Setting {name} to {val["val"]} {val["parameter"].unit}\nvia {val["parameter"].name}')
        
        #TODO: this sucks! Make it better, general try except loops are dangerous
        for Gen in self.Gen_inst_arr: 
            try:     
                Gen.output_status(1)
            except:
                pass
            

    def post_measurement_operation(self, i): 
        for Gen in self.Gen_inst_arr:
            try: 
                Gen.output_status(0)
            except: 
                pass
        print(f"\nMeasurement {i+1} out of {np.shape(list(self.setpoint_arr))[0]} completed\n")
        
    def make_datadict(self):
        '''
        use the independent variables supplied by CW_sweep.add_independent_variables 
        
        and assume the dependent variables are either (vna phase, vna power),  Spectrum PSD, or both
        
        '''
        
        print(self.ind_par_dict_arr)
        axes_arr = [ind_par_dict['name'] for ind_par_dict in self.ind_par_dict_arr]
        
        dd_ind_var_dict = dict()
        for ind_par_dict in self.ind_par_dict_arr: 
            dd_ind_var_dict[ind_par_dict['name']] = dict(unit = ind_par_dict['parameter'].unit)
            
        if self.mode == 'VNA': 
            axes_arr.append('vna_frequency')
            dd_ind_var_dict['vna_frequency'] = dict(unit = 'Hz')
            dd_dep_var_dict = dict(vna_phase = dict(axes = axes_arr, unit = 'Rad'),
                                   vna_power = dict(axes = axes_arr, unit = 'dB')                                   
                                   )
        if self.mode == 'SA': 
            axes_arr.append('spec_frequency')
            dd_ind_var_dict['spec_frequency'] = dict(unit = 'Hz')
            dd_dep_var_dict = dict(spec_power = dict(axes = axes_arr, unit = 'dB')                                   
                                   )
            
        assert self.is_ind_par_set == True
        
        return  dd.DataDict(**(dd_ind_var_dict | dd_dep_var_dict))
    
    def sweep(self, DATADIR, debug = True, avgnum = 10):
        
        if not self.is_ind_par_set: 
            raise Exception("Independent parameter not yet set. Run set_independent_parameter method")
            
        #preprocess the independent variables that are set in CW.add_independent_variable
        ind_par_names = []
        ind_par_parameters = []
        ind_par_vals = []
        for ind_par_dict in self.ind_par_dict_arr: 
            for name, info_dict in ind_par_dict.items(): 
                ind_par_names.append(name)
                ind_par_parameters.append(ind_par_dict[name]['parameter'])
                ind_par_vals.append(ind_par_dict[name]['vals'])

        ####################### Set up the datadict
        self.datadict =self.make_datadict()
        
        ####################### Prepare for taking data
        self.pre_measurement_operation()
        filename = self.filename_func(self.setpoint_dict)
        self.writer = dds.DDH5Writer(DATADIR, self.datadict, name=filename)
        self.writer.__enter__()
        self.savepath = self.writer.file_path
        
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

            #setting independent parameter values
            for name, val in self.setpoint_dict.items(): 
                val['parameter'](val['val'])
            
            if self.mode == 'VNA': 
                vna_freqs = self.VNA_inst.getSweepData() #this could also be a power... fuck
                vna_data = self.VNA_inst.average(avgnum)
                vna_power = vna_data[0]
                vna_phase = vna_data[1]
                d = np.shape(vna_data)[0]
    
                writer_dict = {}
                
                for ind_par_dict in self.ind_par_dict_arr: 
                    writer_dict[ind_par_dict['name']] = ind_par_dict['parameter']()*np.ones(d) #asks the instrument for an update, resize for plottr
                
                #I need to find a way to incorporate power sweeps into this too. for now, just frequency
                writer_dict['vna_frequency'] = vna_freqs
                
                #add the dependent data...
                writer_dict['vna_power'] = vna_power
                writer_dict['vna_phase'] = vna_phase
                
                self.writer.add_data(**writer_dict)
                
            self.post_measurement_operation(i)
        self.writer.__exit__()