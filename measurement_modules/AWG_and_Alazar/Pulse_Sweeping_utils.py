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

from hatdrivers.alazar_utilities.controller.ATSChannelController import ATSChannelController
from hatdrivers.alazar_utilities.controller.alazar_channel import AlazarChannel

from hat_utilities.signal_processing.Pulse_Processing import demod, phase_correction

import time
import matplotlib.pyplot as plt

def Process_One_Acquisition(sI_c, sQ_c, bin_start, bin_stop):
    fig = plt.figure(1)
    ax1 = fig.add_subplot(221)
    ax1.set_title("I")
    ax1.plot(np.average(sI_c[0::2], axis = 0), label = 'even records')
    ax1.plot(np.average(sI_c[1::2], axis = 0), label = 'odd_records')
    # ax1.set_aspect(1)
    ax1.legend()
    ax2 = fig.add_subplot(222)
    ax2.set_title("Q")
    ax2.plot(np.average(sQ_c[0::2], axis = 0), label = 'even records')
    ax2.plot(np.average(sQ_c[1::2], axis = 0), label = 'odd records')
    # ax2.set_aspect(1)
    ax2.legend()
    ax3 = fig.add_subplot(223)
    ax3.set_aspect(1)
    ax3.plot(np.average(sI_c[0::2], axis = 0), np.average(sQ_c[0::2], axis = 0))
    ax3.plot(np.average(sI_c[1::2], axis = 0),np.average(sQ_c[1::2], axis = 0))
    
    #figure for difference tarce
    fig2 = plt.figure(2)
    ax21 = fig2.add_subplot(221)
    ax21.set_title("I")
    ax21.plot(np.average(sI_c[0::2]-sI_c[1::2], axis = 0), label = 'even-odd records')
    
    # ax1.set_aspect(1)
    ax21.legend()
    ax22 = fig2.add_subplot(222)
    ax22.set_title("Q")
    ax22.plot(np.average(sQ_c[0::2]-sQ_c[1::2], axis = 0), label = 'even-odd records')
    
    # ax2.set_aspect(1)
    ax22.legend()
    ax23 = fig2.add_subplot(223)
    ax23.set_aspect(1)
    ax23.plot(np.average(sI_c[0::2]-sI_c[1::2], axis = 0), np.average(sQ_c[0::2]-sQ_c[1::2], axis = 0))
    
    ax24 = fig2.add_subplot(224)
    ax24.plot(np.average(sI_c[0::2]-sI_c[1::2], axis = 0)**2+np.average(sQ_c[0::2]-sQ_c[1::2], axis = 0)**2, label = 'magnitude')
    ax24.legend()
    #%%
    ax4 = fig.add_subplot(224)
    boxcar_histogram(fig, ax4, bin_start, bin_stop, sI_c, sQ_c, Ioffset = 0, Qoffset = 0, scale = 1200)

def boxcar_histogram(fig, ax, start_pt, stop_pt, sI, sQ, Ioffset = 0, Qoffset = 0, scale = 1, num_bins = 100):
    I_bground = Ioffset
    Q_bground = Qoffset
    # print(I_bground, Q_bground)
    I_pts = []
    Q_pts = []
    for I_row, Q_row in zip(sI, sQ): 
        I_pts.append(np.average(I_row[start_pt:stop_pt]-I_bground))
        Q_pts.append(np.average(Q_row[start_pt:stop_pt]-Q_bground))
    # plt.imshow(np.histogram2d(np.array(I_pts), np.array(Q_pts))[0])
    divider = make_axes_locatable(ax)
    ax.set_aspect(1)
    bins = np.linspace(-1,1, num_bins)*scale
    (h, xedges, yedges, im) = ax.hist2d(I_pts, Q_pts, bins = [bins, bins])
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax = cax, orientation = 'vertical')
    # ax.hexbin(I_pts, Q_pts, extent = np.array([-1,1,-1,1])*scale)
    # ax.set_xticks(np.array([-100,-75,-50,-25,0,25,50,75,100])*scale/100)
    # ax.set_yticks(np.array([-100,-75,-50,-25,0,25,50,75,100])*scale/100)
    ax.grid()


    
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
    
    print(myctrl.samples_per_record())
    alazar.buffer_timeout.set(20000)
    rec_num = 15000
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
    
    
def acquire_one_pulse(AWG_inst, Alazar_controller, Sig_Gen, Ref_Gen, LO_frequency, mod_freq, sample_rate, debug = False): 

    Sig_Gen.frequency(LO_frequency)
    Ref_Gen.frequency(LO_frequency+mod_freq)
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
    
    sI = np.zeros(arr_shape)
    sQ = np.zeros(arr_shape)
    rI = np.zeros(arr_shape)
    rQ = np.zeros(arr_shape)
    
    for i, (ch1data_record, ch2data_record) in enumerate(zip(ch1data, ch2data)):
        
        sI_row,sQ_row,rI_row,rQ_row = demod(ch1data_record, ch2data_record)
        sI[i] = sI_row
        sQ[i] = sQ_row
        rI[i] = rI_row
        rQ[i] = rQ_row
        
    
    # Phase correction
    sI_c, sQ_c, rI_trace, rQ_trace = phase_correction(sI, sQ, rI, rQ)
    
    return sI_c, sQ_c, rI_trace, rQ_trace

class Pulse_Sweep(): 
    
    def __init__(self, AWG, AWG_Config, Alazar, Alazar_config, Sig_Gen, Ref_Gen): 
        
        '''
        Implicit in this file is the external interferometer, these components
        '''
        self.AWG_inst = AWG
        self.Alazar_inst = Alazar
        self.is_ind_par_set = False
        self.Alazar_ctrl = Standard_Alazar_Config(Alazar, Alazar_config)
        self.Alazar_config = Alazar_config
        self.AWG_Config = AWG_Config
        self.sig_gen = Sig_Gen
        self.ref_gen = Ref_Gen
        
        
        
    def set_independent_parameter(self, ind_par, start, stop, points_or_step, arange = False): 
        if arange: 
            self.ind_par_vals = np.arange(start, stop, points_or_step)
        else: 
            self.ind_par_vals = np.linspace(start, stop, points_or_step)
            
        self.ind_par = ind_par
        
        self.filenames = [f'{ind_par.name}_{np.round(ind_par_val, 3)}' for ind_par_val in self.ind_par_vals]
        
        
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
        
        
        
    
    