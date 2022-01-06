# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 12:44:49 2020

@author: Ryan Kaufman

A repostory for functional 1-parameter sweeps that produce either a 2d image or a 1d lineplot

"""
import numpy as np 
from plottr.data import datadict_storage as dds, datadict as dd
from plottr.data.datadict_storage import all_datadicts_from_hdf5
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

#%%

def read_fs_data(fs_filepath, interpolation = 'linear'):
        ret = all_datadicts_from_hdf5(fs_filepath)
        res_freqs = ret['data'].extract('base_resonant_frequency').data_vals('base_resonant_frequency')
        currents = ret['data'].extract('base_resonant_frequency').data_vals('current')
        fs_fit_func = interp1d(currents, res_freqs, interpolation)
        return fs_fit_func

def Duffing_Sweep(DATADIR, name, VNA_settings, CS_settings, Gen_settings,att, fs_filepath):
    
    '''
    VNA_settings = [pVNA,7.5e9,3e9,1500,15]
    CS_settings = [yoko2, -6e-5,-3.4e-5,40]
    Gen_settings = [SC4, -19, 18, 40]
    att = 10
    '''
    
    omega0 = read_fs_data(fs_filepath)
    
    [VNA, VNA_fcenter, VNA_fspan, VNA_fpoints, VNA_avgs] = VNA_settings
    [CS, c_start, c_stop, c_points] = CS_settings
    [gen, gen_start, gen_stop, gen_points] = Gen_settings
    VNA.fcenter(VNA_fcenter)
    VNA.fspan(VNA_fspan)
    VNA.num_points(VNA_fpoints)
    VNA.avgnum(VNA_avgs)
    
    data = dd.DataDict(
        current = dict(unit='A'),
        frequency = dict(unit='Hz'),
        gen_power = dict(unit='dBm'),
        gen_freq = dict(axes=['current'], unit = 'Hz'), 
        undriven_power = dict(axes=['current', 'frequency', 'gen_power'], unit = 'dBm'), 
        undriven_phase = dict(axes=['current', 'frequency', 'gen_power'], unit = 'Degrees'),
        driven_power = dict(axes=['current', 'frequency', 'gen_power'], unit = 'dBm'), 
        driven_phase = dict(axes=['current', 'frequency', 'gen_power'], unit = 'Degrees'),
    )
    
    data.validate()
    i = 0
    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        for current_val in np.linspace(c_start,c_stop,c_points):

            gen_freq = float(omega0(current_val))
            
            gen.frequency(gen_freq)
            
            CS.change_current(current_val)
            
            for gen_val in np.linspace(gen_start-att,gen_stop-att,gen_points):
                
                
                gen.power(gen_val+att)
                
                gen.output_status(0)
                
                
                freqs = VNA.getSweepData() #1XN array, N in [1601,1000]
                undriven_vnadata = np.array(VNA.average(VNA_avgs)) #2xN array, N in [1601, 1000]
                
                gen.output_status(1)
                
                freqs = VNA.getSweepData() #1XN array, N in [1601,1000]
                driven_vnadata = np.array(VNA.average(VNA_avgs)) #2xN array, N in [1601, 1000]
        
                writer.add_data(
                        current = current_val*np.ones(np.size(freqs)),
                        gen_power = gen_val*np.ones(np.size(freqs)),
                        gen_freq = gen_freq*np.ones(np.size(freqs)),
                        frequency = freqs,
                        undriven_power = undriven_vnadata[0],
                        undriven_phase = undriven_vnadata[1],
                        driven_power = driven_vnadata[0],
                        driven_phase = driven_vnadata[1],
                    )
                print(f'{np.round((i+1)/c_points*100/gen_points)} percent  complete')
                i+=1

def Flux_Sweep(DATADIR, name, VNA_settings, CS_settings):
    
    [VNA, VNA_fcenter, VNA_fspan, VNA_fpoints, VNA_avgs] = VNA_settings
    [CS, c_start, c_stop, c_points] = CS_settings
    VNA.fcenter(VNA_fcenter)
    VNA.fspan(VNA_fspan)
    VNA.num_points(VNA_fpoints)
    VNA.avgnum(VNA_avgs)
    
    data = dd.DataDict(
        current = dict(unit='A'),
        frequency = dict(unit='Hz'),
        power = dict(axes=['current', 'frequency'], unit = 'dBm'), 
        phase = dict(axes=['current', 'frequency'], unit = 'Degrees'),
    )
    
    data.validate()
    i = 0
    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        for current_val in np.linspace(c_start,c_stop,c_points):
            CS.change_current(current_val)
            freqs = VNA.getSweepData() #1XN array, N in [1601,1000]
            vnadata = np.array(VNA.average(VNA_avgs)) #2xN array, N in [1601, 1000]
    
            writer.add_data(
                    current = current_val*np.ones(np.size(freqs)),
                    frequency = freqs,
                    power = vnadata[0],
                    phase = vnadata[1]
                )
            print(f'{np.round((i+1)/c_points*100)} percent  complete')
            i+=1
#%%
def Frequency_Sweep(DATADIR, name, VNA_settings, Gen_settings):
    
    [VNA, VNA_fcenter, VNA_fspan, VNA_fpoints, VNA_avgs] = VNA_settings
    [Gen, fstart, fstop, fpoints] = Gen_settings
    data = dd.DataDict(
        Gen_freq = dict(unit='Hz'),
        VNA_frequency = dict(unit='Hz'),
        power = dict(axes=['Gen_freq', 'VNA_frequency'], unit = 'dBm'), 
        phase = dict(axes=['Gen_freq', 'VNA_frequency'], unit = 'Degrees'),
    )
    data.validate()
    VNA.fcenter(VNA_fcenter)
    VNA.fspan(VNA_fspan)
    VNA.num_points(VNA_fpoints)
    Gen.output_status(0) 
    VNA.renormalize(5*VNA_avgs)
    Gen.output_status(1)
    i = 0
    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        for f_val in np.linspace(fstart,fstop,fpoints):
            Gen.frequency(f_val)
            freqs = VNA.getSweepData() #1XN array, N in [1601,1000]
            vnadata = np.array(VNA.average(VNA_avgs)) #2xN array, N in [1601, 1000]
            
            # original writer cmd that failed on array size change
            writer.add_data(
                    Gen_freq = f_val*np.ones(np.size(freqs)),
                    VNA_frequency = freqs,
                    power = vnadata[0],
                    phase = vnadata[1]
                )
            print(f'{np.round((i+1)/fpoints*100)} percent  complete')
            i+=1
    Gen.output_status(0)
#%%
def Power_Sweep(DATADIR, name, VNA_settings, Gen_settings, renorm = False): 
    
    [VNA, VNA_fcenter, VNA_fspan, VNA_fpoints, VNA_avgs] = VNA_settings
    [Gen, p_start, p_stop, p_points] = Gen_settings
    
    data = dd.DataDict(
        Gen_power = dict(unit='dBm'),
        VNA_frequency = dict(unit='Hz'),
        power = dict(axes=['Gen_power', 'VNA_frequency'], unit = 'dBm'), 
        phase = dict(axes=['Gen_power', 'VNA_frequency'], unit = 'Degrees'),
    )
    data.validate()
    VNA.fcenter(VNA_fcenter)
    VNA.fspan(VNA_fspan)
    
    if renorm: 
        Gen.output_status(0)
        VNA.renormalize(VNA_avgs)
        Gen.output_status(1)
    i = 0
    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        for p_val in np.linspace(p_start,p_stop,p_points):
            Gen.power(p_val)
            freqs = VNA.getSweepData() #1XN array, N in [1601,1000]
            vnadata = np.array(VNA.average(VNA_avgs)) #2xN array, N in [1601, 1000]
            
            # original writer cmd that failed on array size change
            writer.add_data(
                    Gen_power = p_val*np.ones(np.size(freqs)),
                    VNA_frequency = freqs,
                    power = vnadata[0],
                    phase = vnadata[1]
                )
            print(f'{np.round((i+1)/p_points*100)} percent  complete')
            i+=1
    try: 
        Gen.output_status(0)
    except AttributeError: 
        Gen.rfout(0)
#%%

def Saturation_Sweep(DATADIR, name, VNA_settings, Gen_settings): 
    #take a VNA trace, and perform a saturation sweep at each point in the sweep
    [VNA, vna_avgs, vna_cw_start, vna_cw_stop, vna_cw_points, vna_p_start, vna_p_stop, vna_p_pts, vna_att] = VNA_settings
    [Gen, gen_freq, gen_power, gen_att] = Gen_settings
    
    Gen.frequency(gen_freq)
    Gen.power(gen_power)
    Gen.output_status(1)
    #change sweep type on VNA before changing powers
    VNA.sweep_type('POW')
    VNA.math('NORM') #turn math off

    VNA.power_start(vna_p_start)
    VNA.power_stop(vna_p_stop)
    VNA.num_points(vna_p_pts)
    
    sat_data = dd.DataDict(
        ## saturation data
        sat_gen_freq = dict(unit = 'Hz'),
        sat_gen_power = dict(unit = 'dBm'),
        sat_vna_freq = dict(unit = 'Hz'),
        sat_vna_powers = dict(unit = 'dBm'),
        sat_gain = dict(axes = ['sat_gen_freq', 'sat_gen_power', 'sat_vna_freq', 'sat_vna_powers'], unit = 'dBm'),
        sat_phases = dict(axes = ['sat_gen_freq', 'sat_gen_power', 'sat_vna_freq', 'sat_vna_powers'], unit = 'rad')
        )
    sat_data.validate()
    
    vna_cw_freqs = np.linspace(vna_cw_start, vna_cw_stop, vna_cw_points)
    
    print('creating file')
    with dds.DDH5Writer(DATADIR, sat_data, name=name) as writer:
        #average
        for cw_freq in vna_cw_freqs: 
            VNA.fcenter(cw_freq)
            data = VNA.average(vna_avgs)
            gains = data[0, :]
            phases = data[1, :]
            pows = VNA.getSweepData()
            writer.add_data(
                sat_gen_freq = [gen_freq],
                sat_gen_power = [gen_power-gen_att],
                sat_vna_freq = [cw_freq],
                sat_vna_powers = pows.reshape(1,-1)-vna_att,
                sat_gain = gains.reshape(1,-1),
                sat_phases = phases.reshape(1, -1)
                )
    Gen.output_status(0)
        
        
