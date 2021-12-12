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
    One class to unify all non-adaptive CW measurements
    e.g. gen power, gen frequency, vna power, vna_frequency sweeps
    - add independent parameters dynamically
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
        
    def make_datadict(self, mode):
        '''
        use the independent variables supplied by CW_sweep.add_independent_variables 
        
        and assume the dependent variables are either (vna phase, vna power),  Spectrum PSD, or both
        '''
        
        print(self.ind_par_dict_arr)
        axes_arr = [ind_par_dict['name'] for ind_par_dict in self.ind_par_dict_arr]
        
        dd_ind_var_dict = dict()
        for ind_par_dict in self.ind_par_dict_arr: 
            dd_ind_var_dict[ind_par_dict['name']] = dict(unit = ind_par_dict['parameter'].unit)
            
        if mode == 'VNA': 
            axes_arr.append('vna_frequency')
            dd_ind_var_dict['vna_frequency'] = dict(unit = 'Hz')
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
        Adding dependency on the setpoint dictionary lets you make adjustments to the measurement, 
        e.g. changing the vna window for a Duffing Test
        
        But this should NOT be done in this class, you should create another class that subclasses this 
        one (CW_Sweeps), then write a method that overrides this one
        '''
        # print(f'Setting {name} to {val["val"]} {val["parameter"].unit}\nvia {val["parameter"].name}')
        
        #TODO: this sucks! Make it better, general try except loops are dangerous
        [Gen.output_status(1) if Gen is not None else '' for Gen in self.Gen_inst_arr]
        print("Current parameters: ")
        [print(key,': ', val) for key, val in self.setpoint_dict.items()]

    def post_measurement_operation(self, i): 
        '''
        very similar to pre_measurement_operation, this can be overridden 
        in a subclass to do smarter sweeps
        '''
        print(f"\nMeasurement {i+1} out of {np.shape(list(self.setpoint_arr))[0]} completed\n")
        
        if i+1 == np.shape(list(self.setpoint_arr))[0]: #the sweep is done
            [Gen.output_status(0) if Gen is not None else '' for Gen in self.Gen_inst_arr]
    
    def sweep(self, DATADIR, debug = True, VNA_avgnum = 10, SA_avgnum = 200):
        
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
            
        if self.mode == 'SA' or self.mode == 'both': 
            self.sa_datadict =self.make_datadict(mode = 'SA')
            self.sa_writer = dds.DDH5Writer(DATADIR, self.sa_datadict, name=self.sweep_name+'_SA')
            self.sa_writer.__enter__()
            self.sa_savepath = self.sa_writer.file_path
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

            #taking data with VNA, SA, or both
            
            if self.mode == 'VNA' or self.mode == 'both': 
                if debug: print("\nVNA measuring\n")
                vna_freqs = self.VNA_inst.getSweepData() #this could also be a power... fuck
                vna_data = self.VNA_inst.average(VNA_avgnum)
                vna_power = vna_data[0]
                vna_phase = vna_data[1]
                d = np.shape(vna_data)[1]
    
                vna_writer_dict = {}
                
                for ind_par_dict in self.ind_par_dict_arr: 
                    vna_writer_dict[ind_par_dict['name']] = ind_par_dict['parameter']()*np.ones(d) #asks the instrument for an update, resize for plottr
                
                #I need to find a way to incorporate power sweeps into this too. for now, just frequency
                vna_writer_dict['vna_frequency'] = vna_freqs
                
                #add the dependent data...
                vna_writer_dict['vna_power'] = vna_power
                vna_writer_dict['vna_phase'] = vna_phase
                
                self.vna_writer.add_data(**vna_writer_dict)
                
            if self.mode == 'SA' or self.mode == 'both': 
                if debug: print("\nSA measuring\n")
                sa_data = self.SA_inst.get_data(count = SA_avgnum)
                sa_freqs = sa_data[:,  0]
                sa_power = sa_data[:,  1]
                d = np.size(sa_freqs)
    
                sa_writer_dict = {}
                
                for ind_par_dict in self.ind_par_dict_arr: 
                    sa_writer_dict[ind_par_dict['name']] = ind_par_dict['parameter']()*np.ones(d) #asks the instrument for an update, resize for plottr
                
                #I need to find a way to incorporate power sweeps into this too. for now, just frequency
                sa_writer_dict['spec_frequency'] = sa_freqs
                
                #add the dependent data...
                sa_writer_dict['spec_power'] = sa_power
                
                self.sa_writer.add_data(**sa_writer_dict)

            self.post_measurement_operation(i)
        
        if self.mode == 'SA' or self.mode == 'both': 
            self.sa_writer.file.close()
        
        if self.mode == 'VNA' or self.mode == 'both': 
            self.vna_writer.file.close()