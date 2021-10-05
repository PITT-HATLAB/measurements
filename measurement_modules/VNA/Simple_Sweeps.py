# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 12:44:49 2020

@author: Ryan Kaufman

A repostory for functional 1-parameter sweeps that produce either a 2d image or a 1d lineplot

"""
import numpy as np 
#from plottr.data import datadict_storage as dds, datadict as dd

#%%
def Flux_Sweep(DATADIR, name, VNA_settings, CS_settings, ramp_rate = None):
    '''
    Parameters
    ----------
    DATADIR : string
        directory for saving location.
    name : TYPE
        DESCRIPTION.
    VNA_settings : TYPE
        DESCRIPTION.
    CS_settings : TYPE
        DESCRIPTION.
    ramp_rate : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    None.

    '''
    
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
            CS.change_current(current_val, ramp_rate = ramp_rate)
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
def Spec_sweep(DATADIR, name, CXA_settings, Gen_settings): 
    [CXA, CXA_fcenter, CXA_fspan, CXA_avgs] = CXA_settings
    [Gen, fstart, fstop, fpoints] = Gen_settings
    data = dd.DataDict(
        Gen_freq = dict(unit='Hz'),
        CXA_frequency = dict(unit='Hz'),
        power = dict(axes=['Gen_freq', 'CXA_frequency'], unit = 'dBm'), 
    )
    data.validate()
    CXA.fcenter(CXA_fcenter)
    CXA.fspan(CXA_fspan)
    i = 0
    Gen.output_status(1)
    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        for f_val in np.linspace(fstart,fstop,fpoints):
            Gen.frequency(f_val)
            data = CXA.get_data(count = CXA_avgs)
            freqs = data[:, 0] #1XN array, N in [1601,1000]
            pows = data[:, 1]
            # original writer cmd that failed on array size change
            writer.add_data(
                    Gen_freq = f_val*np.ones(np.size(freqs)),
                    CXA_frequency = freqs,
                    power = pows
                )
            print(f'{np.round((i+1)/fpoints*100)} percent  complete')
            i+=1
    Gen.output_status(0)
#%%
def Spec_frequency_sweep(DATADIR, name, CXA_settings, Gen_settings): 
    [CXA, CXA_fcenter, CXA_fspan, CXA_avgs] = CXA_settings
    [Gen, fstart, fstop, fpoints] = Gen_settings
    data = dd.DataDict(
        Gen_freq = dict(unit='Hz'),
        CXA_frequency = dict(unit='Hz'),
        power = dict(axes=['Gen_freq', 'CXA_frequency'], unit = 'dBm'), 
    )
    data.validate()
    CXA.fcenter(CXA_fcenter)
    CXA.fspan(CXA_fspan)
    i = 0
    Gen.output_status(1)
    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        for f_val in np.linspace(fstart,fstop,fpoints):
            Gen.frequency(f_val)
            data = CXA.get_data(count = CXA_avgs)
            freqs = data[:, 0] #1XN array, N in [1601,1000]
            pows = data[:, 1]
            # original writer cmd that failed on array size change
            writer.add_data(
                    Gen_freq = f_val*np.ones(np.size(freqs)),
                    CXA_frequency = freqs,
                    power = pows
                )
            print(f'{np.round((i+1)/fpoints*100)} percent  complete')
            i+=1
    Gen.output_status(0)
    
#%%
def Spec_power_sweep(DATADIR, name, CXA_settings, Gen_settings): 
    [CXA, CXA_fcenter, CXA_fspan, CXA_avgs] = CXA_settings
    [Gen, pstart, pstop, ppoints] = Gen_settings
    data = dd.DataDict(
        Gen_power = dict(unit='dBm'),
        CXA_frequency = dict(unit='Hz'),
        power = dict(axes=['Gen_power', 'CXA_frequency'], unit = 'dBm'), 
    )
    data.validate()
    CXA.fcenter(CXA_fcenter)
    CXA.fspan(CXA_fspan)
    i = 0
    Gen.output_status(1)
    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        for p_val in np.linspace(pstart,pstop,ppoints):
            Gen.power(p_val)
            data = CXA.get_data(count = CXA_avgs)
            freqs = data[:, 0] #1XN array, N in [1601,1000]
            pows = data[:, 1]
            # original writer cmd that failed on array size change
            writer.add_data(
                    Gen_power = p_val*np.ones(np.size(freqs)),
                    CXA_frequency = freqs,
                    power = pows
                )
            print(f'{np.round((i+1)/ppoints*100)} percent  complete')
            i+=1
    Gen.output_status(0)
#%% 2 Tone Test for measuring IIP3

def Two_Tone(DATADIR, name, CXA_settings, Gen_settings): 
    
    [CXA, CXA_fcenter, CXA_fspan, CXA_avgs] = CXA_settings
    [Gen1, Gen2, f1, f2, pstart, pstop, ppoints] = Gen_settings
    data = dd.DataDict(
        Gen_power = dict(unit='dBm'),
        CXA_frequency = dict(unit='Hz'),
        power = dict(axes=['Gen_power', 'CXA_frequency'], unit = 'dBm'), 
    )
    data.validate()
    
    CXA.fcenter(CXA_fcenter)
    CXA.fspan(CXA_fspan)
    i = 0
    Gen1.frequency(f1)
    Gen2.frequency(f2)
    Gen1.output_status(1)
    Gen2.output_status(1)
    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        for p_val in np.linspace(pstart,pstop,ppoints):
            Gen1.power(p_val)
            Gen2.power(p_val)
            data = CXA.get_data(count = CXA_avgs)
            freqs = data[:, 0] #1XN array, N in [1601,1000]
            pows = data[:, 1]
            # original writer cmd that failed on array size change
            writer.add_data(
                    Gen_power = p_val*np.ones(np.size(freqs)),
                    CXA_frequency = freqs,
                    power = pows
                )
            print(f'{np.round((i+1)/ppoints*100)} percent  complete')
            i+=1
    Gen1.output_status(0)
    Gen2.output_status(0)
    
    
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

def Saturation_freq_Sweep(DATADIR, name, VNA_settings, Gen_settings): 
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
        
#%%
def saturation_gen_power_sweep(DATADIR, name, VNA_settings, Gen_settings): 
    #take a VNA trace, and perform a saturation sweep at each point in the sweep
    [VNA, vna_cw_freq, vna_avgs, vna_p_start, vna_p_stop, vna_p_pts, vna_att] = VNA_settings
    [Gen, gen_freq, gen_power_start, gen_power_stop, gen_power_points, gen_att] = Gen_settings
    
    Gen.frequency(gen_freq)
    #change sweep type on VNA before changing powers
    VNA.sweep_type('POW')
    VNA.fcenter(vna_cw_freq)
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
    
    gen_powers = np.linspace(gen_power_start, gen_power_stop, gen_power_points)
    
    print('creating file')
    with dds.DDH5Writer(DATADIR, sat_data, name=name) as writer:
        #average
        for gen_power in gen_powers: 
            data = VNA.average(vna_avgs)
            gains = data[0, :]
            phases = data[1, :]
            pows = VNA.getSweepData()
            writer.add_data(
                sat_gen_freq = [gen_freq],
                sat_gen_power = [gen_power-gen_att],
                sat_vna_freq = [vna_cw_freq],
                sat_vna_powers = pows.reshape(1,-1)-vna_att,
                sat_gain = gains.reshape(1,-1),
                sat_phases = phases.reshape(1, -1)
                )
    Gen.output_status(0)
