# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 09:30:44 2020

@author: Ryan Kaufman, Wolfgang Pfaff

Purpose: 
    Repository for well-established sweeps
"""

import matplotlib.pyplot as plt
import numpy as np 
import time
import matplotlib.colors as color
from plottr.data import datadict_storage as dds, datadict as dd
from scipy.signal import find_peaks

#supporting functions #############################################
    
def power2dB(power):
    if np.size(power) == 1:
        if power == None: 
            return None
        else: 
            return 10 * np.log10(power)
    else: 
        return 10 * np.log10(power)


def dB2power(dB):
    return 10**(dB/10)

# def smoothen(trace, window_len=51):
#     w = savgol_filter(trace, window_len, 3)
#     return w

def smoothen(trace, window_len=50):
    w = np.blackman(window_len)
    return np.convolve(w/w.sum(), trace, mode='same')

def find_peak(frequencies, trace, d = 10, w = 2, p = 5):
    df = frequencies[1] - frequencies[0]
    
    # convert required distance between peaks from frequency to idx
    # require 10 freq units here.
    dist = d / df
    
    # width conversion to idx
    # require a width of 3 frequency units
    width = w / df
    
    # require height and prominence of at least 3 log power units
    peaks, props = find_peaks(trace, 5, distance=dist, prominence=p, width=width)
    
    if len(peaks) == 0:
        return None, None, None
    
    # extract relevant information in useful units. use the peak closest to 0.
    peak_positions = np.array([frequencies[i] for i in peaks])
    peak_idx = np.argmin(np.abs(peak_positions-0))
    peak_pos = peak_positions[peak_idx]
    peak_width = props['widths'][peak_idx] * df
    peak_height = props['peak_heights'][peak_idx]
    
    return peak_pos, peak_height, peak_width

########################### Main Data taking #################################
    
class Gain_Power_vs_Flux(): 
    ''' Record 20dB gain power change wrt flux 
    
    Procedure: 
        - Start with a minimal-power 20dB gain point at a certain flux
        - program steps current by curr_step
        - program sweeps generator frequency within given range with same power 
        (smoothing on?) to find highest power frequency
        - program slowly increases or decreases power to reach 20dB gain maximum
        - if 20dB cannot be achieved, NaN value is given for pump_power and 
        trace is saved, otherwise program records pump frequency, power, 
        and saves VNA amplitude trace at given current
        - repeat until current array is exhausted
    '''
    def __init__(self, CS, Gen, VNA, cwd, filename, gen_att = 0, vna_att = 0): 
        
        self.CS = CS
        self.Gen = Gen
        self.VNA = VNA
        self.name = filename
        self.datadir = cwd
        self.att = gen_att
        self.vna_att = vna_att
        self.gain_data = dd.DataDict(
            #gain vs current data
            bias_current = dict(unit='A'), #length N
            gen_frequency = dict(unit='Hz'), #length M for each N (NxM)
            gen_power = dict(unit='dBm'), # variable length P for each M (NxMxP)
            vna_frequency = dict(unit = 'Hz'), #length L for each N,M,P pair (1601 usually, adjustable but not variable) (NxMxP(N,M)xL)
            
            gain_trace = dict(axes=['bias_current', 'gen_frequency', 'gen_power', 'vna_frequency'], unit = 'dB'), #length L for each N,M,P combo (NxMxP(N,M)xL)
            phase_trace = dict(axes=['bias_current', 'gen_frequency', 'gen_power', 'vna_frequency'], unit = 'Degrees'), #length L for each N,M,P combo (NxMxP(N,M)xL)
            
            calculated_gain = dict(axes=['bias_current', 'gen_frequency', 'gen_power'], unit = 'dBm'), #length 1 for each N,M,P combo (NxMxP(N,M)x1)
            gain_freq = dict(axes=['bias_current', 'gen_frequency', 'gen_power'], unit = 'Hz'),
            gain_bw = dict(axes=['bias_current','gen_frequency', 'gen_power'], unit = 'Hz'),
            #^^ plotted quantities
        )
        self.sat_data = dd.DataDict(
            ## saturation data
            sat_bias_current = dict(unit = 'A'),
            sat_gen_freq = dict(unit = 'Hz'),
            sat_gen_power = dict(unit = 'dBm'),
            sat_vna_freq = dict(unit = 'Hz'),
            sat_vna_powers = dict(unit = 'dBm'),
            
            sat_gain = dict(axes = ['sat_bias_current', 'sat_gen_freq', 'sat_gen_power', 'sat_vna_freq', 'sat_vna_powers'])
            )
        self.gain_data.validate()
        self.sat_data.validate()
        print('creating files')
        self.gain_writer = dds.DDH5Writer(self.datadir, self.gain_data, name=self.name+'_gain')
        self.gain_writer.__enter__()
        
        self.sat_writer = dds.DDH5Writer(self.datadir, self.sat_data, name=self.name+'_sat')
        self.sat_writer.__enter__()
        print('file created')
    
    def set_VNA_to_freq_sweep(self, fcenter, fspan, points, avgs, normed = True):
        self.VNA.sweep_type('LIN')
        self.VNA.fcenter(fcenter)
        self.VNA.fspan(fspan)
        self.VNA.avgnum(avgs)
        self.VNA.num_points(points)
        if normed == True: 
            self.VNA.math('DIV')
        
    def save_gain_datapoint(self, current, gen_freq, gen_power, vna_freqs, vna_gain_trace, vna_phase_trace, calc_gain, gain_freq, bw):
        '''
        loads information into the class's stored datadict.
        '''
        #this is entered as 1601 identical currents, 1601 identical gen frequencies, 1601 identical gen powers, 
        #1601 different VNA freqs, 1601 different, VNA gains, 1601 different VNA phases,
        #and 1601 identical calculated gains
        # shape_shifter = np.ones(len(vna_freqs))

        self.gain_writer.add_data(
            bias_current = [current],
            gen_frequency = [gen_freq],
            gen_power = [gen_power-self.att],
            vna_frequency = np.reshape(vna_freqs, (1,-1)),
            
            gain_trace = np.reshape(vna_gain_trace, (1,-1)), 
            phase_trace = np.reshape(vna_phase_trace, (1,-1)),
            
            calculated_gain = [calc_gain],
            gain_freq = [gain_freq], 
            gain_bw = [bw]
            )
    def save_saturation_datapoint(self, current, gen_freq, gen_power, vna_freq, vna_input_powers, gains):
        '''
        Loads information about the saturation power found for a given 20dB-ish gain point. 
        Goal is to have (Gain) vs (bias current, generator detuning, vna_power) plot 
        '''
        self.sat_writer.add_data(
            sat_bias_current = [current],
            sat_gen_freq = [gen_freq],
            sat_gen_power = [gen_power-self.att],
            sat_vna_freq = [vna_freq],
            sat_vna_powers = vna_input_powers.reshape(1,-1)-self.vna_att,
            
            sat_gain = gains.reshape(1,-1)
            )
        
    def analyze_trace(self, frequencies, trace, smooth=True, plot=False, peak_width_minimum = 1):
        if smooth:
            smooth_trace = power2dB(smoothen(dB2power((trace))))
            peak_pos, peak_height, peak_width = find_peak(frequencies, dB2power(smooth_trace), w = peak_width_minimum)
        else:
            smooth_trace = None
            peak_pos, peak_height, peak_width = find_peak(frequencies, trace, p = peak_width_minimum)
            
        if plot:
            plt.close('all')
            fig, ax = plt.subplots(1,1)
            # ax.plot(frequencies, trace, label='data')
            
            if smooth_trace is not None:
                ax.plot(frequencies, smooth_trace, label='smoothed')
            
            if peak_pos is not None:
                ax.vlines(x=peak_pos, ymin=0, ymax=power2dB(peak_height), color='g', lw=2)
                ax.hlines(y=power2dB(peak_height/2), xmin=peak_pos-peak_width/2, xmax=peak_pos+peak_width/2, color='g', lw=2)
                ax.text(frequencies[0], 29, 
                        f"$f$ = {peak_pos:.1f}\n"
                        f"$G$ = {power2dB(peak_height):.1f}\n"
                        f"$BW$ = {peak_width:.1f}",
                        color='g', ha='left', va='top', backgroundcolor='w')
                
            ax.legend(loc=0, fontsize='small')
            ax.set_ylim(-10,30)
            ax.grid(dashes=[3,3])
            ax.set_xlabel('frequency')
            ax.set_ylabel('S11 (dB)')
            plt.show()
            
        return peak_pos, power2dB(peak_height), peak_width
    def find_gain(self, window = 1e6): 
        '''
        Parameters
        ----------
        avg_number : int
            number of VNA averages taken
        window : float
            frequency range in Hz where we average over to get the effective gain
        Returns
        -------
        gain : float
            calculated gain of a trace
        '''
        data = np.array(self.VNA.average(self.VNA_avg_number))
        pow_data = data[0]
        phase_data = data[1]
        fdata = np.array(self.VNA.getSweepData())
        max_loc = int(np.average(np.where(np.isclose(pow_data, np.max(pow_data)))))
        f_low = fdata[max_loc] - window/2
        f_high = fdata[max_loc] + window/2
        f_low_bool_arr = fdata > f_low
        f_high_bool_arr = fdata<f_high
        f_bool_arr = f_low_bool_arr*f_high_bool_arr
        gain = np.average(pow_data[f_bool_arr])
        return gain, pow_data, phase_data, fdata
        
    def find_gain_W(self, peak_width_minimum = 1): 
        freqs = self.VNA.getSweepData()
        freqs_renormed = (freqs-freqs[int(len(freqs)/2)])/1e6
        data = np.array(self.VNA.average(self.VNA_avg_number))
        peak_pos, peak_height, peak_width = self.analyze_trace(freqs_renormed, data[0], plot = True, peak_width_minimum = peak_width_minimum)
        if peak_pos is not None: 
            peak_freq = peak_pos*1e6 + freqs[int(len(freqs)/2)]
        else: 
            peak_freq = float('nan')
            peak_height = float('nan')
            peak_width = float('nan')
        
        return peak_freq, peak_height, peak_width, freqs, data[0], data[1]
    
    def saturation_sweep(self, bias_current, gen_freq, gen_power, vna_freq, vna_p_start, vna_p_stop, vna_num_pts, vna_p_avgs): 
        
        #storing_previous sweep swettings
        prev_fspan = self.VNA.fspan()
        prev_fcenter = self.VNA.fcenter()
        prev_avgs = self.VNA.avgnum()
        prev_points = self.VNA.num_points()
        #setting initial independent variables
        
        self.CS.change_current(bias_current), 
        self.Gen.frequency(gen_freq)
        self.Gen.power(gen_power)
        self.Gen.output_status(1)
        #change sweep type on VNA before changing powers
        self.VNA.sweep_type('POW')
        self.VNA.math('NORM') #turn math off
        self.VNA.fcenter(vna_freq)
        self.VNA.power_start(vna_p_start)
        self.VNA.power_stop(vna_p_stop)
        self.VNA.num_points(vna_num_pts)
        
        #average
        data = self.VNA.average(vna_p_avgs)
        print(data)
        pows = self.VNA.getSweepData()
        self.Gen.output_status(0)
        
        plt.plot(pows, data[0])
        plt.title(f"Power Sweep at {bias_current}mA and VNA@{vna_freq} Gen @{gen_freq, gen_power}")
        plt.show()
        
        #save
        self.save_saturation_datapoint(self.CS.current(),self.Gen.frequency(),self.Gen.power(), self.VNA.fcenter(), pows, data[0])
        
        #reset
        self.set_VNA_to_freq_sweep(prev_fcenter, prev_fspan, prev_points, prev_avgs)
        
        return pows, data
        
    def sweep_power_for_gain(self, stepsize = 0.01, block_size = 10, limit = 10, target_gain = 20, threshold = 2, saturation_sweep = True, vna_p_start = -43, vna_p_stop = 10, vna_p_steps = 1000, vna_p_avgs = 100, peak_width_minimum = 1): 
        current_bias = self.CS.current()
        gen_freq = self.Gen.frequency()
        starting_power = self.Gen.power()
        
        #run a power sweep, and find the lowest power 20dB point in that sweep
        steps = int(np.floor(block_size/2))
        pow_arr = np.arange(starting_power-steps*stepsize, starting_power+steps*stepsize, stepsize)
        #cut it off at 20dB and -20dB (generator range)
                #(-1)^n
        alt_array = np.empty(2*steps+1)
        alt_array[0] = 0
        alt_array[1::2] = -1
        alt_array[2::2] = 1
        step_array = np.linspace(0,2*steps, 2*steps+1)
        alt_step_array = step_array*alt_array
        
        big_pow_step = (2*steps+1)*stepsize
        final_pow_arr = np.array([])
        final_gain_arr = np.array([])
        i = 0
        while True: 
            gain_arr = []
            gain_vna_freq_arr = []
            #changing range of power array
            pow_arr = np.copy(pow_arr+alt_step_array[i]*big_pow_step)
            #cut it off at 20dB and -20dB (generator range)
            for p, k in enumerate(pow_arr): 
                if p < -20:
                    pow_arr[k] = -20
                if p> 20: 
                    pow_arr[k] = 20
                    
            print(f"Adjusting power, powers: {str(pow_arr)}")
            self.Gen.output_status(1)
            for gen_power in pow_arr: 
                print(f"Gen_power: {gen_power}")
                self.Gen.power(gen_power)
                gain_freq_found, gain_found, bw_found, VNA_freqs, VNA_gain_trace, VNA_phase_trace = self.find_gain_W(peak_width_minimum = peak_width_minimum)
                self.save_gain_datapoint(current_bias, gen_freq, gen_power, VNA_freqs, VNA_gain_trace, VNA_phase_trace, gain_found, gain_freq_found, bw_found)
                
                #for adaptivity: 
                gain_arr.append(gain_found)
                gain_vna_freq_arr.append(gain_freq_found)
                
                print(f"Gain: {gain_found} at {gain_freq_found}")
            self.Gen.output_status(0)
            # checking to see what we found
            
            if np.isnan(gain_arr).all() == True: #all Nan's
                gain_found = False
                print("\nNo Peaks Found! Adjusting powers\n")
            else: 
                gain_found = True
                
                gain_arr = np.array(gain_arr)
                #find gain that is closest to target_gaindB
                diff_arr = np.abs(gain_arr - target_gain)
                closest_val_loc = np.where(diff_arr == np.nanmin(diff_arr))[0][0]
                closest_val = gain_arr[closest_val_loc]
                closest_power = pow_arr[closest_val_loc]
                closest_vna_freq = gain_vna_freq_arr[closest_val_loc]
                
                print(f'Closest Gain: {closest_val} at {closest_vna_freq}')
                
                final_gain_arr = np.append(final_gain_arr, gain_arr)
                final_pow_arr = np.append(final_pow_arr, pow_arr)

                    
                if np.abs(closest_val-target_gain) < threshold: #this is a good gainpoint
                    print(f"Gain Point found at pow:{closest_power} gain:{closest_val}")
                    self.Gen.power(closest_power)
                    sorted_data = np.array(list(zip(*[(y,x) for y,x in sorted(zip(final_pow_arr,final_gain_arr))])))
                    
                    #perform saturation sweep at this point if desired
                    if saturation_sweep: 
                        self.saturation_sweep(current_bias, gen_freq, closest_power, closest_vna_freq, vna_p_start, vna_p_stop, vna_p_steps, vna_p_avgs)
                        
                    return sorted_data[0], sorted_data[1], [closest_power, closest_val]
            if i == limit:
                print("No Gain Point Found, breaking")
                try: 
                    self.Gen.power(closest_power)
                except: 
                    #it might not exist if none were found, so if not we'll do the starting power
                    self.Gen.power(starting_power)
                sorted_data = np.array(list(zip(*[(y,x) for y,x in sorted(zip(final_pow_arr,final_gain_arr))])))
                return sorted_data[0], sorted_data[1], [float("NaN"), float("NaN")]
            i+=1 
            
    def sweep_gain_vs_freq(self, gen_freqs, stepsize = 0.01, block_size = 10, limit = 10, target_gain = 20, threshold = 2, saturation_sweep = True, vna_p_start = -43, vna_p_stop = 10, vna_p_steps = 1000, vna_p_avgs = 100, smooth = True, peak_width_minimum = 1):
        '''
        Parameters
        ----------
        VNA: Instrument
        Gen: Instrument
        gen_freqs : ndarray
            list of possible frequencies to try for reaching 20dB gain
            
        Returns
        ------
        
        '''
        gain_arr_arr = []
        pow_arr_arr = []
        pow_list = []
        gain_list = []
        prev_pow = self.Gen.power()
        
        for freq in gen_freqs: 
            print(f"Adjusting frequency: {freq}, starting power {prev_pow}")
            self.Gen.frequency(freq)
            self.Gen.power(prev_pow)
            pow_arr, gain_arr, [closest_power, closest_val] =  self.sweep_power_for_gain(stepsize = stepsize, 
                                                                                         block_size = block_size, 
                                                                                         limit = limit, 
                                                                                         target_gain = target_gain,
                                                                                         threshold = threshold,
                                                                                         saturation_sweep = True,
                                                                                         vna_p_start = vna_p_start,
                                                                                         vna_p_stop = vna_p_stop,
                                                                                         vna_p_steps = vna_p_steps,
                                                                                         vna_p_avgs = vna_p_avgs,
                                                                                         peak_width_minimum = peak_width_minimum
                                                                                         )
            
            if closest_power != closest_power:
                pass #this means no point was found, so we'll keep the power guess where it was at
            else: 
                prev_pow = closest_power
                
            pow_list.append(closest_power)
            gain_list.append(closest_val)
            pow_arr_arr.append(pow_arr)
            gain_arr_arr.append(gain_arr)
            
        return  [np.array(pow_list), np.array(gain_list), pow_arr_arr, gain_arr_arr]
    
    def get_freq_sweep_info(self, freq_arr, pow_arr, pow_arr_arr, gain_arr_arr): 
        min_loc = np.where(pow_arr == np.nanmin(pow_arr))[0][0]
        min_freq = freq_arr[min_loc]
        max_loc = np.where(pow_arr == np.nanmax(pow_arr))[0][0]
        max_freq = freq_arr[max_loc]
        
        min_pow = pow_arr[min_loc]
        max_pow = pow_arr[max_loc]
        return([min_pow, max_pow], [min_freq, max_freq])
    
    def plot_powers(self, freq_arr, pow_arr, pow_arr_arr, gain_arr_arr, cmin = 16, cmax = 24): 
        print(pow_arr)
        print(np.min(pow_arr))
        min_loc = np.where(pow_arr == np.nanmin(pow_arr))[0][0]
        min_freq = freq_arr[min_loc]
        freq_arr = np.copy(freq_arr-freq_arr[min_loc])
        dx = int((np.max(freq_arr)-np.min(freq_arr))/(4*len(freq_arr)))
        colors = [color.hex2color('#0000FF'), color.hex2color('#FFFFFF'), color.hex2color('#FF0000')]
        _cmap = color.LinearSegmentedColormap.from_list('my_cmap', colors)
        _norm = color.Normalize(vmin = 16, vmax = 24)
        for i in range(len(freq_arr)): 
            x = freq_arr[i]
            y_start = pow_arr_arr[i][0]
            y_end = pow_arr_arr[i][-1]
            # print(dx, x, y_start, y_end)
            plt.imshow(np.array([gain_arr_arr[i]]).T, extent = [x-dx, x+dx, y_start, y_end], origin = 'lower', aspect = 'auto', norm = _norm, cmap = _cmap)
            
        plt.plot(freq_arr, pow_arr)
        plt.title("Minimum 20dB Power vs Frequency Detuning")
        plt.xlabel("Generator Detuning (Hz)")
        plt.ylabel("P_20dB (dBm)")
        plt.colorbar()
        plt.show()
        # plt.xticks(ticks = plt.xticks()[0]/1e6)
        print(f"\nMin {pow_arr[min_loc]} at {min_freq/1e9, min_freq/2e9}GHz")
        
    def sweep_min_power_and_saturation_vs_current(self, current_settings, res_func, VNA_settings, Gen_settings, 
                                                  stepsize = 0.1, limit = 10, target_gain = 20, threshold = 2, 
                                                  saturation_sweep = True, vna_p_start = -43, vna_p_stop = 10, vna_p_steps = 1000, vna_p_avgs = 100): 
        
        '''
        This creates a taco's worth of data for EACH current bias point within a range, starting from a known point
        
        In order to do this it needs a fitted fluxsweep, so that it can make a fair guess at the generator frequencies it should try at each current. 
        
        steps:
            - starting from a known working bias point, run a taco sweep
            - acquire minimum power point (gen freq and power)_opt from first taco
            - set VNA to gen_freq_opt/2 +- X_MHz span, num_points, etc
            - move bias point by small, specified current step (generally <0.5% of quanta)
            - renormalize VNA
            - repeat
        '''
        #timestamp 
        t_start = time.time()
        #unpack inputs 
        [c_start, c_stop, c_stepsize] = current_settings
        [VNA_fcenter, VNA_fspan, self.VNA_avg_number, VNA_fpower, VNA_fpoints] = VNA_settings
        [gen_freq_known, gen_init_range, gen_init_stepsize, gen_pow_known] = Gen_settings
        #generate current_arrays
        currents = np.arange(c_start, c_stop, c_stepsize)
        
        print(f"Current Array: {currents}")
        
        ############run initial sweep
        
        self.CS.change_current(c_start)
        self.Gen.frequency(gen_freq_known)
        self.Gen.power(gen_pow_known)
        
        #change_VNA_settings
        self.VNA.fcenter(VNA_fcenter)
        self.VNA.fspan(VNA_fspan)
        self.VNA.avgnum(self.VNA_avg_number)
        self.VNA.power(VNA_fpower)
        self.VNA.num_points(VNA_fpoints)
        
        self.Gen.output_status(0)
        self.VNA.renormalize(10*self.VNA_avg_number)
        self.Gen.output_status(1)
        
        init_gen_freqs = np.arange(gen_freq_known-gen_init_range/2, gen_freq_known+gen_init_range/2, gen_init_stepsize)
        self.c_after_data = []
        self.after_min_gen_power_arr = []
        self.after_min_gen_freq_arr = []
        
        
        
        for i, current in enumerate(currents): 
            self.CS.change_current(current)
            if i == 0:
                gen_freqs = np.arange(gen_freq_known-gen_init_range/2, gen_freq_known+gen_init_range/2, gen_init_stepsize)
            else: 
                #remake the gen_freqs based on the fitted fluxsweep
                new_center_guess = float(res_func(current))*2
                gen_freqs = np.linspace(new_center_guess-gen_init_range/2, new_center_guess+gen_init_range/2, np.size(gen_freqs))
            datasets = self.sweep_gain_vs_freq(gen_freqs,  
                                               stepsize = 0.1,
                                               limit = 6,
                                               target_gain = 20,
                                               threshold = 2,
                                               saturation_sweep = True, 
                                               vna_p_start = vna_p_start, 
                                               vna_p_stop = vna_p_stop,
                                               vna_p_steps = vna_p_steps, 
                                               vna_p_avgs = vna_p_avgs)
            
        
            self.plot_powers(init_gen_freqs, datasets[0], datasets[2], datasets[3])

            [min_gen_pow, max_gen_pow], [min_gen_freq, max_gen_freq] = self.get_freq_sweep_info(init_gen_freqs, datasets[0], datasets[2], datasets[3])
            self.c_after_data.append(datasets)
            self.after_min_gen_power_arr.append(min_gen_pow)
            self.after_min_gen_freq_arr.append(min_gen_freq)
            
            #adjust VNA window center based on minimum generator frequency, and set generator power according to the minimum power
            self.VNA.fcenter(min_gen_freq/2)
            self.Gen.power(np.average([min_gen_pow, max_gen_pow]))
            #renormalize
            self.Gen.output_status(0)
            self.VNA.renormalize(10*self.VNA_avg_number)
            self.Gen.output_status(1)
            
            print(f"\n\n After current sweep {(i+1)/len(currents)*100} percent completed")
            
        
        t_taken = time.time() - t_start
        print(f"Mega TACO completed, time taken {t_taken/60/60} hours")
        
        
        