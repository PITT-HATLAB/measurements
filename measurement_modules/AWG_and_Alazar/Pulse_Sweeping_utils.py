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

from instrument_drivers.alazar_utilities.controller.ATSChannelController import ATSChannelController
from instrument_drivers.alazar_utilities.controller.alazar_channel import AlazarChannel

from data_processing.signal_processing.Pulse_Processing import demod, phase_correction

from dataclasses import dataclass

import broadbean as bb
from broadbean.plotting import plotter
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from plottr.data.datadict_storage import all_datadicts_from_hdf5

import time

def Process_One_Acquisition(name, sI_c1, sI_c2, sQ_c1 ,sQ_c2, bin_start, bin_stop, hist_scale = 200, odd_only = False, even_only = False):
    fig = plt.figure(1, figsize = (12,8))
    fig.suptitle(name)
    ax1 = fig.add_subplot(221)
    ax1.set_title("I")
    ax1.plot(np.average(sI_c1, axis = 0), label = 'even records')
    ax1.plot(np.average(sI_c2, axis = 0), label = 'odd_records')
    # ax1.set_aspect(1)
    ax1.legend(loc = 'upper right')
    ax2 = fig.add_subplot(222)
    ax2.set_title("Q")
    ax2.plot(np.average(sQ_c1, axis = 0), label = 'even records')
    ax2.plot(np.average(sQ_c2, axis = 0), label = 'odd records')
    # ax2.set_aspect(1)
    ax2.legend(loc = 'upper right')
    ax3 = fig.add_subplot(223)
    ax3.set_aspect(1)
    ax3.plot(np.average(sI_c1, axis = 0), np.average(sQ_c1, axis = 0))
    ax3.plot(np.average(sI_c2, axis = 0),np.average(sQ_c2, axis = 0))
    
    #figure for difference trace
    fig2 = plt.figure(2, figsize = (12,8))
    ax21 = fig2.add_subplot(221)
    ax21.set_title("I (even-odd records)")
    ax21.plot(np.average(sI_c1-sI_c2, axis = 0), label = 'even-odd records')
    
    # ax1.set_aspect(1)
    ax22 = fig2.add_subplot(222)
    ax22.set_title("Q (even-odd records)")
    ax22.plot(np.average(sQ_c1-sQ_c2, axis = 0), label = 'even-odd records')
    
    # ax2.set_aspect(1)
    ax23 = fig2.add_subplot(223)
    ax23.set_title("Trajectories")
    ax23.set_aspect(1)
    ax23.plot(np.average(sI_c1-sI_c2, axis = 0), np.average(sQ_c1-sQ_c2, axis = 0))
    
    
    ax24 = fig2.add_subplot(224)
    ax24.set_title("magnitudes")
    ax24.plot(np.average(sI_c1-sI_c2, axis = 0)**2+np.average(sQ_c1-sQ_c2, axis = 0)**2, label = 'magnitude')
    ax4 = fig.add_subplot(224)
    
    fig2, ax99 = plt.subplots()
    # print(np.shape(sI_c1))
    bins_even, h_even = boxcar_histogram(fig2, ax99, bin_start, bin_stop, sI_c1, sQ_c1, Ioffset = 0, Qoffset = 0, scale = hist_scale)
    bins_odd, h_odd = boxcar_histogram(fig2, ax99, bin_start, bin_stop, sI_c2, sQ_c2, Ioffset = 0, Qoffset = 0, scale = hist_scale)
    plt.close(fig2)
    
    if even_only and not odd_only: 
        print('displaying only even')
        boxcar_histogram(fig, ax4, bin_start, bin_stop, sI_c1, sQ_c1, Ioffset = 0, Qoffset = 0, scale = hist_scale)
        
    elif odd_only and not even_only: 
        print('displaying only odd')
        boxcar_histogram(fig, ax4, bin_start, bin_stop, sI_c2, sQ_c2, Ioffset = 0, Qoffset = 0, scale = hist_scale)
    else: 
        print('displaying both')
        boxcar_histogram(fig, ax4, bin_start, bin_stop, np.concatenate((sI_c1, sI_c2)), np.concatenate((sQ_c1, sQ_c2)), Ioffset = 0, Qoffset = 0, scale = hist_scale)
    plt.show()
    return bins_even, bins_odd, h_even.T, h_odd.T
    
    
    
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
    
    return bins, h

from scipy.optimize import curve_fit


def Gaussian_2D(M,amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
    x, y = M
    xo = float(xo)
    yo = float(yo)
    a = (np.cos(theta)**2)/(2*sigma_x**2) + (np.sin(theta)**2)/(2*sigma_y**2)
    b = -(np.sin(2*theta))/(4*sigma_x**2) + (np.sin(2*theta))/(4*sigma_y**2)
    c = (np.sin(theta)**2)/(2*sigma_x**2) + (np.cos(theta)**2)/(2*sigma_y**2)
    g = offset + amplitude*np.exp( - (a*((x-xo)**2) + 2*b*(x-xo)*(y-yo)
                            + c*((y-yo)**2)))
    return g

class Gaussian_info: 
    def __init__(self): 
        self.info_dict = {}
    def print_info(self):
        for key, val in self.info_dict.items(): 
            if key == 'popt':
                pass
            elif key == 'pcov':
                pass
            else: 
                print(key, ': ', val)
                
    def __sub__(self, other_GC):
        sub_class = Gaussian_info()
        for key, val in self.info_dict.items(): 
            sub_class.info_dict[key] = val - other_GC.info_dict[key]
        return sub_class
    
    def center_vec(self): 
        return np.array([self.info_dict['x0'], self.info_dict['y0']])
    def plot_on_ax(self, ax, displacement = np.array([0,0]), color = 'white'): 
        ax.annotate("", xy=self.center_vec(), xytext=(0, 0), arrowprops=dict(arrowstyle = '->', lw = 3, color = color))
    def plot_array(self):
        return Gaussian_2D(*self.info_dict['popt'])
        

def fit_2D_Gaussian(bins, 
                    h_arr, 
                    guessParams, 
                    max_fev = 100): 
    
    X, Y = np.meshgrid(bins[0:-1], bins[0:-1])
    resh_size = np.shape(X)
    xdata, ydata= np.vstack((X.ravel(), Y.ravel())), h_arr.ravel()
    # print('xdata_shape: ', np.shape(xdata))
    # print("y shape: ",np.shape(ydata))
    print("running curve_fit")
    popt, pcov = curve_fit(Gaussian_2D, xdata, ydata, p0 = guessParams, maxfev = max_fev)
    GC = Gaussian_info()
    GC.info_dict['canvas'] = xdata 
    GC.info_dict['amplitude'] = popt[0]
    GC.info_dict['x0'] = popt[1]
    GC.info_dict['y0'] = popt[2]
    GC.info_dict['sigma_x'] = popt[3]
    GC.info_dict['sigma_y'] = popt[4]
    GC.info_dict['theta'] = popt[5]
    GC.info_dict['offset'] = popt[6]
    GC.info_dict['popt'] = popt
    GC.info_dict['pcov'] = pcov
    GC.info_dict['contour'] = get_contour_line(X, Y, Gaussian_2D(xdata, *popt).reshape(resh_size), contour_line = 3)
    
    return GC

def get_contour_line(cont_x, cont_y, contour_arr, contour_line = 3):
    fig = plt.figure()
    contour_map = plt.contour(cont_x, cont_y, contour_arr)
    plt.close(fig)
    v = contour_map.collections[contour_line].get_paths()[0].vertices
    plot_y, plot_x = v[:,1], v[:,0]
    return plot_x, plot_y

def extract_2pulse_histogram_from_filepath(datapath, bin_start = 55, bin_stop = 150, hist_scale = 0.01, even_only = False, odd_only = False): 
    
    dd = all_datadicts_from_hdf5(datapath)['data']
    
    time_unit = dd['time']['unit']
    time_vals = dd['time']['values'].reshape((7500, 208))
    
    rec_unit = dd['record_num']['unit']
    rec_num = dd['record_num']['values'].reshape((7500, 208))
    
    I_plus = dd['I_plus']['values'].reshape((7500, 208))
    I_minus = dd['I_minus']['values'].reshape((7500, 208))
    
    Q_plus = dd['Q_plus']['values'].reshape((7500, 208))
    Q_minus = dd['Q_minus']['values'].reshape((7500, 208))
    
    #averages
    I_plus_avg = np.average(I_plus, axis = 0)
    I_minus_avg = np.average(I_minus, axis = 0)
    Q_plus_avg = np.average(Q_plus, axis = 0)
    Q_minus_avg = np.average(Q_minus, axis = 0)
    
    #re-weave the data back into it's original pre-saved form
    
    bins_even, bins_odd, h_even, h_odd = Process_One_Acquisition(datapath.split('/')[-1].split('\\')[-1], I_plus, I_minus, Q_plus, Q_minus, bin_start, bin_stop, hist_scale = hist_scale, even_only = even_only, odd_only = odd_only)
    
    Plus_x0Guess = np.average(np.average(I_plus_avg[bin_start:bin_stop]))
    Plus_y0Guess = np.average(np.average(Q_plus_avg[bin_start:bin_stop]))
    Plus_ampGuess = np.max(h_even)
    Plus_sxGuess = np.max(bins_even)/5
    Plus_syGuess = Plus_sxGuess
    Plus_thetaGuess = 0
    Plus_offsetGuess = 0
    
    Minus_x0Guess = np.average(np.average(I_minus_avg[bin_start:bin_stop]))
    Minus_y0Guess = np.average(np.average(Q_minus_avg[bin_start:bin_stop]))
    Minus_ampGuess = np.max(h_even)
    Minus_sxGuess = np.max(bins_even)/5
    Minus_syGuess = Minus_sxGuess
    Minus_thetaGuess = 0
    Minus_offsetGuess = 0
    
    guessParams = [[Plus_ampGuess, Plus_x0Guess, Plus_y0Guess, Plus_sxGuess, Plus_syGuess, Plus_thetaGuess, Plus_offsetGuess],
                   [Minus_ampGuess, Minus_x0Guess, Minus_y0Guess, Minus_sxGuess, Minus_syGuess, Minus_thetaGuess, Minus_offsetGuess]]
    
    return bins_even, bins_odd, h_even, h_odd, guessParams

    
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

def phase_shifter(I_data, Q_data, phase_offset, plot = False): 
    '''
    This will take I as the perfect channel and some phase offset sin(theta_imbalance) offsetting Q towards I
    Assuming I to be the unit magnitude
    '''
    
    Q_res = Q_data
    I_res = (I_data-np.sin(phase_offset)*Q_data)/np.cos(phase_offset)
    if plot: 
        plt.figure()
        plt.title("Before phase correction: ")
        plt.plot(I_data)
        plt.plot(Q_data)
        plt.figure()
        plt.title("After phase correction: ")
        plt.plot(I_res)
        plt.plot(Q_res)

    return I_res

def cavity_response_with_correction(amp, filepath, SR, npts, amp_corr = 1, phase_offset = 0):
    def cavity_response_Q_bb(amp, filepath, SR, npts):
        imag = pd.read_csv(filepath, usecols = ['imag']).to_numpy().T[0]
        return imag*amp
    
    def cavity_response_I_bb(amp, filepath, SR, npts, amp_corr = amp_corr, phase_corr = phase_offset):
        real = pd.read_csv(filepath, usecols = ['real']).to_numpy().T[0]
        scaled = real*amp
        amplitude_corrected = scaled*amp_corr
        Q_data = pd.read_csv(filepath, usecols = ['imag']).to_numpy().T[0]*amp
        phase_corrected = phase_shifter(amplitude_corrected, Q_data, phase_corr)
        return phase_corrected
    
    return cavity_response_I_bb, cavity_response_Q_bb

def cavity_response_with_correction_and_phase_rotation(theta, amp, filepath, SR, npts, amp_corr = 1, phase_offset = 0):
    cavity_response_I_bb, cavity_response_Q_bb = cavity_response_with_correction(amp, filepath, SR, npts, amp_corr = 1, phase_offset = 0)
    
    return lambda amp, filepath, SR, npts: cavity_response_I_bb(amp, filepath, SR, npts)*np.cos(theta)+cavity_response_Q_bb(amp, filepath, SR, npts)*np.sin(theta), lambda amp, filepath, SR, npts: cavity_response_Q_bb(amp, filepath, SR, npts)*np.cos(theta)-cavity_response_I_bb(amp, filepath, SR, npts)*np.sin(theta)

from qcodes.instrument_drivers.tektronix.AWG5014 import Tektronix_AWG5014

@dataclass
class cavity_mimicking_pulse_class: 
    name: str
    AWG_inst: Tektronix_AWG5014
    LO_frequency: float
    DC_offsets: tuple
    ch2_correction: float
    phase_offset: float
    amplitude: float
    phase_rotation: float
    sim_filepath_plus: str
    sim_filepath_minus: str
    SR: float
    npts: int
    only_plus: bool
    only_minus: bool

from qcodes.instrument.parameter import Parameter
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
        setup_cavity_mimicking_pulse(self.pulse_class)

def setup_cavity_mimicking_pulse(cmp_dc): 
    Ifunc_corrected, Qfunc_corrected = cavity_response_with_correction_and_phase_rotation(cmp_dc.phase_rotation,1, cmp_dc.sim_filepath_plus, cmp_dc.SR, cmp_dc.npts, amp_corr = cmp_dc.ch2_correction, phase_offset = cmp_dc.phase_offset)
    #all in one box,
    wait_time = 1e-6
    rearm_time = 10e-6
    pulse_dur = 2e-6
    buffer = 300e-9
    
    #make element just for waiting for the trigger vefore each pulse
    bpTrigWait = bb.BluePrint()
    bpTrigWait.insertSegment(1, 'waituntil', rearm_time)
    bpTrigWait.setSR(1e9)
    
    #make the I channel for -detuning:
    I0_channel = Ifunc_corrected # args: ampl, filepath_to_cavity_sim
    bpI0 = bb.BluePrint()
    bpI0.setSR(1e9)
    bpI0.insertSegment(1, 'waituntil', (wait_time))
    bpI0.insertSegment(2, I0_channel, (1, cmp_dc.sim_filepath_plus), name='Ig', dur=pulse_dur)
    bpI0.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
    bpI0.marker1 = [(0e-6,50e-9)]
    
    bpI0.marker2 = [(wait_time-buffer,pulse_dur+2*buffer)]
    
    
    #make the Q channel for -detuning:
    Q0_channel = Qfunc_corrected # args: ampl,filepath_to_cavity_sim
    bpQ0 = bb.BluePrint()
    bpQ0.setSR(1e9)
    bpQ0.insertSegment(1, 'waituntil', (wait_time))
    bpQ0.insertSegment(2, Q0_channel, (1, cmp_dc.sim_filepath_plus), name='Qg', dur=pulse_dur)
    bpQ0.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
    bpQ0.marker1 = [(0e-6,50e-9)]
    
    #make the I channel for +detuning:
    I1_channel = Ifunc_corrected # args: ampl, filepath_to_cavity_sim
    bpI1 = bb.BluePrint()
    bpI1.setSR(1e9)
    bpI1.insertSegment(1, 'waituntil', (wait_time))
    bpI1.insertSegment(2, I1_channel, (1, cmp_dc.sim_filepath_minus), name='Ie', dur=pulse_dur)
    bpI1.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
    bpI1.marker1 = [(0e-6,50e-9)]
    
    bpI1.marker2 = [(wait_time-buffer,pulse_dur+2*buffer)]
    
    #make the Q channel for +detuning:
    Q1_channel = Qfunc_corrected # args: ampl,filepath_to_cavity_sim
    bpQ1 = bb.BluePrint()
    bpQ1.setSR(1e9)
    bpQ1.insertSegment(1, 'waituntil', (wait_time))
    bpQ1.insertSegment(2, Q1_channel, (1, cmp_dc.sim_filepath_minus), name='Qe', dur=pulse_dur)
    bpQ1.insertSegment(3, 'waituntil', (2*wait_time+pulse_dur))
    bpQ1.marker1 = [(0e-6,50e-9)]
    
    ##############################################
    #put blueprints into elements
    waitEl = bb.Element()
    waitEl.addBluePrint(1, bpTrigWait)
    waitEl.addBluePrint(2, bpTrigWait)
    
    CavEl1 = bb.Element()
    CavEl1.addBluePrint(1,bpI0)
    CavEl1.addBluePrint(2,bpQ0)
    plotter(CavEl1)
    
    CavEl2 = bb.Element()
    CavEl2.addBluePrint(1,bpI1)
    CavEl2.addBluePrint(2,bpQ1)
    plotter(CavEl2)
    
    ###############################################
    #put elements into sequence
    CavSeq = bb.Sequence()
    
    #good values to kill leakage: 
    CavSeq.setChannelAmplitude(1, 5)  # Call signature: channel, amplitude (peak-to-peak)
    CavSeq.setChannelOffset(1, 0)
    CavSeq.setChannelAmplitude(2, 5)
    CavSeq.setChannelOffset(2, 0)
    
    #now we have to prep it for the AWG
    CavSeq.addElement(1, waitEl)
    CavSeq.addElement(2, CavEl1)
    CavSeq.addElement(3, waitEl)
    CavSeq.addElement(4, CavEl2)
    
    CavSeq.setSR(1e9)
    
    #set the sequencing
    # Here we repeat each element twice and then proceed to the next, wrapping over at the end
    if cmp_dc.only_plus and not cmp_dc.only_minus: 
        CavSeq.setSequencingTriggerWait(1, 1)
        CavSeq.setSequencingTriggerWait(2, 0)
        CavSeq.setSequencingTriggerWait(3, 1)
        CavSeq.setSequencingTriggerWait(4, 0)
        CavSeq.setSequencingGoto(2, 1)
    elif cmp_dc.only_minus and not cmp_dc.only_plus: 
        CavSeq.setSequencingTriggerWait(1, 1)
        CavSeq.setSequencingTriggerWait(2, 0)
        CavSeq.setSequencingTriggerWait(3, 1)
        CavSeq.setSequencingTriggerWait(4, 0)
        CavSeq.setSequencingGoto(4, 3)
    else: 
        CavSeq.setSequencingTriggerWait(1, 1)
        CavSeq.setSequencingTriggerWait(2, 0)
        CavSeq.setSequencingTriggerWait(3, 1)
        CavSeq.setSequencingTriggerWait(4, 0)
        CavSeq.setSequencingGoto(4, 1)

    CavSeq.checkConsistency()
    
    package = CavSeq.outputForAWGFile()
    package.channels
    cmp_dc.AWG_inst.make_send_and_load_awg_file(*package[:])
    cmp_dc.AWG_inst.ch1_amp(1)
    cmp_dc.AWG_inst.ch2_amp(1)
    cmp_dc.AWG_inst.ch1_offset(cmp_dc.DC_offsets[0])
    cmp_dc.AWG_inst.ch2_offset(cmp_dc.DC_offsets[1])
    
    cmp_dc.AWG_inst.ch1_state(1)
    cmp_dc.AWG_inst.ch2_state(1)
    
def acquire_one_pulse(AWG_inst, Alazar_controller, Sig_Gen, Ref_Gen, LO_frequency, mod_freq, sample_rate, debug = False): 

    Sig_Gen.frequency(LO_frequency)
    Ref_Gen.frequency(LO_frequency+mod_freq)
    Sig_Gen.output_status(1)
    Ref_Gen.output_status(1)
    myctrl = Alazar_controller
    AWG = AWG_inst
    AWG.ch1_m1_high(1.5)
    AWG.ch1_m2_high(2.5)
    AWG.ch2_m1_high(1.5)
    AWG.ch2_m2_high(2.5)
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
    
    Sig_Gen.output_status(0)
    Ref_Gen.output_status(0)
    return sI_c, sQ_c, rI_trace, rQ_trace

class Pulse_Sweep(): 
    
    def __init__(self, AWG, AWG_Config, Alazar_ctrl, Alazar_config, Sig_Gen, Ref_Gen): 
        
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
        
        
        
    def set_independent_parameter(self, ind_par, start, stop, points_or_step, arange = False, filename = None): 
        if arange: 
            self.ind_par_vals = np.arange(start, stop, points_or_step)
        else: 
            self.ind_par_vals = np.linspace(start, stop, points_or_step)
            
        self.ind_par = ind_par
        if filename == None: 
            self.filenames = [f'{ind_par.name}_{np.round(ind_par_val, 3)}' for ind_par_val in self.ind_par_vals]
        else: 
            self.filenames = [f'{filename}_{ind_par.name}_{np.round(ind_par_val, 3)}' for ind_par_val in self.ind_par_vals]
        
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
        
        
        
    
    