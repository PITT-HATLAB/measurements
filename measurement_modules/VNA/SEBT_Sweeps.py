import numpy as np 
from plottr.data import datadict_storage as dds, datadict as dd

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
        pump_power = dict(unit='V'),
        power = dict(axes=['frequency','pump_power'], unit = 'dBm'), 
    )
    
    pump_power = np.linspace(-20,-10,101)
    
    data.validate()
    i = 0
    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        for pump_power_val in pump_power:

            SigGen.power(pump_power_val)
            frequency, power = CXA.gettrace(avgnum=10)
            
            writer.add_data(
                    frequency = frequency,
                    pump_power = pump_power_val*np.ones(np.size(frequency)),
                    power = power
                )
            i+=1

def SmallAC_Freq_Sweep(DATADIR, name, CXA, acsource):
    
    # not done!!!
    
    #CXA.fcenter(6.1896180000e9+200)
    #CXA.fspan(600)
    
    data = dd.DataDict(
        frequency = dict(unit='Hz'),
        flux_frequency = dict(unit='V'),
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