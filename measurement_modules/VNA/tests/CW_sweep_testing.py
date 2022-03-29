# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 17:41:39 2021

@author: RRK

Purpose: troubleshoot CW sweeps class
"""
import numpy as np
import matplotlib.pyplot as plt
import measurement_modules.VNA.CW_Sweeping_Utils as CW
import logging
from qcodes.instrument.parameter import Parameter
from plottr.apps.autoplot import main
#%%
class test_parameter(Parameter): 
    def __init__(self, name):
        # only name is required
        super().__init__(name)
        self._value = 0
        self.unit = 'test_unit'

    # you must provide a get method, a set method, or both.
    def get_raw(self):
        return self._value

    def set_raw(self, val):
        self._value = val

class wrapped_parameter(Parameter): 
    def __init__(self, name, inst_parameter): 
        super().__init__(name)
        self.value = inst_parameter()
        self.unit = inst_parameter.unit
        self._inst_par = inst_parameter
    def get_raw(self): 
        self._inst_par()
    def set_raw(self, val): 
        self._inst_par(val)

#%%
# DATADIR = r''
# name = 'test'

# tp1_vals = np.linspace(0, 1, 100)
# tp2_vals = np.linspace(1, 2, 100)

# CWSWP = CW.CW_sweep(name, "VNA")

# test_parameter_1 = test_parameter('ind_var_1')
# test_parameter_2 = test_parameter('ind_var_2')
# #ind_par_dict{name: dict(parameter = actual_parameter_class, vals = [np_val_arr])}
# # amp_dict = dict(Amp = dict(parameter = SigGen.output_status, vals = np.array([0,1])))
# test_par_1 = dict(name = 'ind_var_1_name', parameter = test_parameter_1, vals = tp1_vals)
# test_par_2 = dict(name = 'ind_var_2_name', parameter = test_parameter_2, vals = tp2_vals)
# # 
# # CWSWP.add_independent_parameter(amp_dict)
# CWSWP.add_independent_parameter(test_par_1)
# CWSWP.add_independent_parameter(test_par_2)

# ddtest = CWSWP.make_datadict()

DATADIR = r'Z:\Data\testing'

name = 'CW_Sweeps_VNA_and_SA_test'

CWSWP = CW.CW_sweep(name, "both", VNA_inst = pVNA, SA_inst = CXA, Gen_arr = [SigGen])

vna_power_dict = dict(name = 'vna_input_power', parameter = pVNA.power, vals = np.array([-30, -25, -20]))
pump_power_dict = dict(name = 'pump_power', parameter = SigGen.power, vals = np.linspace(-10, 0, 6))

# CWSWP.add_independent_parameter(vna_power_dict)
CWSWP.add_independent_parameter(pump_power_dict)

#%%
# V(2)
CWSWP.sweep(DATADIR, debug = True)

#%%
DATADIR = r'Z:\Data\testing'

name = 'CW_Sweeps_VNA_and_SA_test'

CWSWP = CW.CW_sweep(name, "both", VNA_inst = pVNA, SA_inst = CXA, Gen_arr = [SigGen])
CWSWP.setup_VNA('FREQ', 7.511e9, 7.711e9, 2000) #start, stop, points
CWSWP.setup_SA(7.511e9, 7.711e9)
# vna_power_dict = dict(name = 'vna_input_power', parameter = pVNA.power, vals = np.array([-30, -25, -20]))
pump_power_dict = dict(name = 'pump_power', parameter = SigGen.power, vals = np.linspace(-10, 0, 6))

# CWSWP.add_independent_parameter(vna_power_dict)
CWSWP.add_independent_parameter(pump_power_dict)

#%%
# V(2)
CWSWP.sweep(DATADIR, debug = True)




