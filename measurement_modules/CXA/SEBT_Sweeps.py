import numpy as np 
from plottr.data import datadict_storage as dds, datadict as dd


def get_sidebands(frequency, power, small_AC_f, bw):
    
    real_pump_frequency = frequency[np.where(power == np.max(power))]

                    
    sideband_frequency = real_pump_frequency + small_AC_f
                    
    sideband_indices = np.where(  np.abs(frequency-sideband_frequency) < bw  )

    sideband_power = np.max(power[sideband_indices])
    
    return sideband_power
    
def sideband_Flux_Sweep(DATADIR, name, CXA, CS, SC):

    data = dd.DataDict(
        current = dict(unit='A'),
        sideband_power = dict(axes=['current'], unit = 'dBm'), 
    )
    
    # get array from measured resonance data
    
    current = np.array([0.000e+00, 2.500e-07, 5.000e-07, 7.500e-07, 1.000e-06, 1.250e-06,
       1.500e-06, 1.750e-06, 2.000e-06, 2.250e-06, 2.500e-06, 2.750e-06,
       3.000e-06, 3.250e-06, 3.500e-06, 3.750e-06, 4.000e-06, 4.250e-06,
       4.500e-06, 4.750e-06, 5.000e-06, 5.250e-06, 5.500e-06, 5.750e-06,
       6.000e-06, 6.250e-06, 6.500e-06, 6.750e-06, 7.000e-06, 7.250e-06,
       7.500e-06, 7.750e-06, 8.000e-06, 8.250e-06, 8.500e-06, 8.750e-06,
       9.000e-06, 9.250e-06, 9.500e-06, 9.750e-06, 1.000e-05, 1.025e-05,
       1.050e-05, 1.075e-05, 1.100e-05, 1.125e-05, 1.150e-05, 1.175e-05,
       1.200e-05, 1.225e-05, 1.250e-05, 1.275e-05, 1.300e-05, 1.325e-05,
       1.350e-05, 1.375e-05, 1.400e-05, 1.425e-05, 1.450e-05, 1.475e-05,
       1.500e-05, 1.525e-05, 1.550e-05, 1.575e-05, 1.600e-05, 1.625e-05,
       1.650e-05, 1.675e-05, 1.700e-05, 1.725e-05, 1.750e-05, 1.775e-05,
       1.800e-05, 1.825e-05, 1.850e-05, 1.875e-05, 1.900e-05, 1.925e-05,
       1.950e-05, 1.975e-05, 2.000e-05])
    
    
    fd = np.array([7.68518519e+09, 7.67184685e+09, 7.65850851e+09, 7.64517017e+09,
       7.63243243e+09, 7.61974474e+09, 7.60705706e+09, 7.60345345e+09,
       7.60150150e+09, 7.59954955e+09, 7.60435435e+09, 7.61118619e+09,
       7.61801802e+09, 7.62800300e+09, 7.63938939e+09, 7.65077578e+09,
       7.66356356e+09, 7.67722723e+09, 7.69089089e+09, 7.70543043e+09,
       7.72072072e+09, 7.73601101e+09, 7.75085085e+09, 7.76516517e+09,
       7.77947948e+09, 7.79341842e+09, 7.80675676e+09, 7.82009510e+09,
       7.83293293e+09, 7.84464464e+09, 7.85635636e+09, 7.86814314e+09,
       7.88018018e+09, 7.89221722e+09, 7.90415415e+09, 7.91554054e+09,
       7.92692693e+09, 7.93828829e+09, 7.94934935e+09, 7.96041041e+09,
       7.97147147e+09, 7.97895395e+09, 7.98643644e+09, 7.99391892e+09,
       8.00080080e+09, 8.00763263e+09, 8.01446446e+09, 8.02212212e+09,
       8.02992993e+09, 8.03773774e+09, 8.04329329e+09, 8.04817317e+09,
       8.05305305e+09, 8.05725726e+09, 8.06116116e+09, 8.06506507e+09,
       8.06976977e+09, 8.07497497e+09, 8.08018018e+09, 8.08415916e+09,
       8.08708709e+09, 8.09001502e+09, 8.09339339e+09, 8.09729730e+09,
       8.10120120e+09, 8.10435435e+09, 8.10630631e+09, 8.10825826e+09,
       8.11071071e+09, 8.11428929e+09, 8.11786787e+09, 8.12107107e+09,
       8.12302302e+09, 8.12497497e+09, 8.12682683e+09, 8.12812813e+09,
       8.12942943e+09, 8.13088088e+09, 8.13413413e+09, 8.13738739e+09,
       8.14064064e+09])
    
    CORRECTION = 300
    
    small_AC_f = 100
    
    return_val = 0*current
    
    data.validate()
    i = 0
    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        for i in range(0,len(current)):

            SC.frequency(fd[i])
            CXA.fcenter(fd[i] + CORRECTION)
            CS.current(current[i])

            frequency, power = CXA.gettrace(avgnum=20)
            
            bw = CXA.RBW()

            sideband_power = get_sidebands(frequency, power, small_AC_f, bw, correction=CORRECTION)
            
            print(sideband_power)
            
            return_val[i] = sideband_power
            
            writer.add_data(
                    current = current[i],
                    sideband_power = sideband_power
                )

            i+=1

    return return_val

def SmallAC_Voltage_Sweep(DATADIR, name, CXA, acsource):
    
    #CXA.fcenter(6.1896180000e9+200)
    #CXA.fspan(600)
    
    data = dd.DataDict(
        frequency = dict(unit='Hz'),
        voltage = dict(unit='V'),
        power = dict(axes=['frequency','voltage'], unit = 'dBm'), 
    )
    
    voltage = np.linspace(0.01, 1, 50)
    
    data.validate()
    i = 0
    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        for voltage_val in voltage:

            acsource.write('VOLT ' + str(voltage_val))
            frequency, power = CXA.gettrace(avgnum=10)
            
            writer.add_data(
                    frequency = frequency,
                    voltage = voltage_val*np.ones(np.size(frequency)),
                    power = power
                )

            i+=1
            
def Pump_Power_Sweep(DATADIR, name, CXA, SigGen):
    
    #CXA.fcenter(6.1896180000e9+200)
    #CXA.fspan(600)
    
    data = dd.DataDict(
        frequency = dict(unit='Hz'),
        pump_power = dict(unit='dBm'),
        power = dict(axes=['frequency','pump_power'], unit = 'dBm'), 
    )
    
    pump_power = np.linspace(-1.25,-0.25,101)
    
    data.validate()
    i = 0
    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        for pump_power_val in pump_power:
            print(pump_power_val)
            SigGen.power(pump_power_val)
            frequency, power = CXA.gettrace(avgnum=10)
            
            writer.add_data(
                    frequency = frequency,
                    pump_power = pump_power_val*np.ones(np.size(frequency)),
                    power = power
                )
            i+=1
            
def Kerr_mapping(DATADIR, name, CXA, SigCore, acsource):
    
    # I call this sweep Kerr mapping because it hopefully will help me understand
    # how the nonlinearity messes up my resonance condition. Note that it does not 
    # save traces - only the peak value of the sidebands. 
    
    small_AC_f = float(acsource.ask('FREQ?'))
    
    
    
    data = dd.DataDict(
        pump_frequency = dict(unit='Hz'),
        pump_power = dict(unit='dBm'),
        sideband_power1 = dict(axes=['pump_frequency','pump_power'], unit = 'dBm'), 
        sideband_power2 = dict(axes=['pump_frequency','pump_power'], unit = 'dBm'), 
        off_power1 = dict(axes=['pump_frequency','pump_power'], unit = 'dBm'), 
        off_power2 = dict(axes=['pump_frequency','pump_power'], unit = 'dBm'), 
    )
    
    pump_frequency = np.linspace(6.211e9,6.214e9,81)
    pump_power = np.linspace(-1.5,0.5,81)
    
    CXA.fspan(10*small_AC_f)
    
    CORRECTION = 300
    
    data.validate()
    i = 0
    j = 0
    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        for pump_frequency_val in pump_frequency:
            j += 1
            for pump_power_val in pump_power:         

                acsource.output_status(1)                

                SigCore.power(pump_power_val)
                
                CXA.fcenter(pump_frequency_val + CORRECTION)
                SigCore.frequency(pump_frequency_val)
        
                bw = CXA.RBW()
                
                frequency, power = CXA.gettrace(avgnum=5)
                
                sideband_power1 = get_sidebands(frequency, power, small_AC_f, bw)
                sideband_power2 = get_sidebands(frequency, power, small_AC_f*2, bw)
                
                acsource.output_status(0)
                
                frequency, power = CXA.gettrace(avgnum=5)
                
                off_power1 = get_sidebands(frequency, power, small_AC_f, bw)
                off_power2 = get_sidebands(frequency, power, small_AC_f*2, bw)               
    
                writer.add_data(
                        pump_frequency = pump_frequency_val,
                        pump_power = pump_power_val,
                        sideband_power1 = sideband_power1,
                        sideband_power2 = sideband_power2,
                        off_power1 = off_power1,
                        off_power2 = off_power2
                    )
                i+=1
                
                print('%i %i - sideband1: %0.3f - sideband2: %0.3f - off1: %0.3f - off2: %0.3f' % (i, j, sideband_power1, sideband_power2, off_power1, off_power2))

def SmallAC_Freq_Sweep(DATADIR, name, CXA, acsource):
    
 
    #CXA.fcenter(6.1896180000e9+200)
    #CXA.fspan(600)
    
    data = dd.DataDict(
        frequency = dict(unit='Hz'),
        flux_frequency = dict(unit='Hz'),
        power = dict(axes=['frequency','flux_frequency'], unit = 'dBm'), 
    )
    
    flux_frequency = np.linspace(2, 100, 200)
    
    data.validate()
    i = 0
    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        for flux_frequency_val in flux_frequency:

            acsource.write('FREQ ' + str(flux_frequency_val))
            frequency, power = CXA.gettrace(avgnum=10)
            
            writer.add_data(
                    frequency = frequency,
                    flux_frequency = flux_frequency_val*np.ones(np.size(frequency)),
                    power = power
                )
            print(i)
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
            
