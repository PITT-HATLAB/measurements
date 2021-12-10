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
                 VNA, 
                 SA, 
                 Gen1, 
                 Gen2, 
                 Gen3): 
        
        self.filename_prepend = name+'_'
        self.VNA_inst = VNA
        self.SA_inst = SA
        self.Gen_inst_arr = [Gen1, Gen2, Gen3]
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
        for name, val in val_dict.items(): 
            filename += (name+'_')
            filename += (str(np.round(val['val'], 3))+'_'+val['parameter'].unit + '_')
        return filename
    
    def pre_measurement_operation(self): 
        '''
        function that handles preparation for the experimen
        '''
        print(f'Setting {name} to {val["val"]} {val["parameter"].unit}\nvia {val["parameter"].name}')
        for Gen in self.Gen_inst_arr: 
            Gen.output_status(1)    

    def post_measurement_operation(self, i): 
        self.sig_gen.output_status(0)
        self.ref_gen.output_status(0)
        print(f"\nMeasurement {i+1} out of {np.shape(list(self.setpoint_arr))[0]} completed\n")
        
    def make_datadict(self):
        assert self.is_ind_par_set == True
        
        data = dd.Datadict(
            
            
            )
        
        
        return datadict
    
    def sweep(self, DATADIR, savemode = 'together', debug = True):
        
        if not self.is_ind_par_set: 
            raise Exception("Independent parameter not yet set. Run set_independent_parameter method")
        
        if savemode == 'together': 
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
            #setting independent parameter values
            for name, val in self.setpoint_dict.items(): 
                val['parameter'](val['val'])
                
                
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
                    sI_c, sQ_c, ref_I, ref_Q = acquire_one_pulse_3_state(self.AWG_inst, self.Alazar_ctrl, self.AWG_Config.Mod_freq, self.Alazar_config.SR)
                    s = list(np.shape(sI_c))
                    s[0] = int(s[0]//3) #evenly divided amongst I_plus and I_minus
                    time_step = self.Alazar_config.SR/self.AWG_Config.Mod_freq
                    if debug: 
                        plt.figure()
                        plt.plot(ref_I[:500])
                        plt.title("I")
                        plt.figure()
                        plt.plot(ref_Q[:500])
                        plt.title("Q")
                        plt.figure()
                        plt.plot(np.mod(np.angle(ref_I+1j*ref_Q), 2*np.pi)[:500], '.')
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