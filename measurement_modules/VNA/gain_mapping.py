import numpy as np 
from plottr.data import datadict_storage as dds, datadict as dd
from plottr.data.datadict_storage import all_datadicts_from_hdf5
from scipy import interpolate

def lambdify_omega0(FS_fit_filepath):
    dd = all_datadicts_from_hdf5(FS_fit_filepath)['data']
    
    I_b = dd['current']['values']
    omega_0 = dd['base_resonant_frequency']['values']
    
    f = interpolate.interp1d(I_b, omega_0)
    
    return f
    
def get_gain_from_trace(VNA_p_off, VNA_p_on):
    p_max = np.max(VNA_p_on)
    p_off = VNA_p_off[np.where(p_max == VNA_p_on)]
    
    G_max = p_max - p_off # gain
    
    return G_max

def gain_mapping(DATADIR, name, VNA, gen, CS, FS_fit_filepath):
        
    data = dd.DataDict(
        Delta_f_pump = dict(unit='Hz'),
        p_pump = dict(unit='dBm'),
        I_b = dict(unit='A'),
        G_max = dict(axes=['Delta_f_pump','p_pump','I_b'], unit = 'dBm'))

    I_b = np.linspace(-5e-5,-3.4e-3,5)
    
    Delta_f = np.linspace(-50e6,50e6,20)
    
    p_pump = np.linspace(-10,19,30)
    
    VNA_avgs = 40
    
    omega0 = lambdify_omega0(FS_fit_filepath)
    
    data.validate()
    
    VNA.fspan(100e6)
    
    gen.output_status(0)
    
    stop_for_20db = False

    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        
        for i in range(0,len(I_b)):
            
            
            
            CS.change_current(I_b[i], ramp_rate = 1e-6)
            
            f_pump = Delta_f + 2*omega0(I_b[i])
            
            VNA.fcenter = omega0(I_b[i])
            
            for j in range(0,len(f_pump)):
                
                gen.frequency(f_pump[j])
                                
                for k in range(0,len(p_pump)):
                    
                    print('Pump power: ' + str(p_pump[k]))
                    print('Pump freq: ' + str(f_pump[j]))
                    print('Bias current: ' + str(I_b[i]))
                    
                    gen.power(p_pump[k])
                    
                    gen.output_status(0)
                    
                    freqs = VNA.getSweepData()
                    vnadata = np.array(VNA.average(VNA_avgs))
                    
                    VNA_p_off = vnadata[0]
                    
                    gen.output_status(1)
                    
                    freqs = VNA.getSweepData()
                    vnadata = np.array(VNA.average(VNA_avgs))
                    
                    VNA_p_on = vnadata[0]

                    G_max = get_gain_from_trace(VNA_p_off, VNA_p_on)
                    
                    print(G_max)
                    print(' ')
                    
                    if stop_for_20db:
                        if (G_max > 20):
                            
                            print('20 dB reached! press q to stop pausing')
                            q = input()
                            if q == 'q':
                                stop_for_20db = False
                    
                    
                    
                    writer.add_data(
                            Delta_f_pump = Delta_f[j],
                            p_pump = p_pump[k],
                            I_b = I_b[i],
                            G_max = G_max,
                        )

                
                
#%%

DATADIR = 'Z:/Data/SA_4C1_3152/gain_mapping'
name = 'gain_map_-60dBm'
VNA = pVNA
gen = SC4
CS = yoko2
FS_fit_filepath = r'Z:/Data/SA_4C1_3152/fits/2021-12-23/2021-12-23_0088_FFS_parallel/2021-12-23_0088_FFS_parallel.ddh5'

gain_mapping(DATADIR, name, VNA, gen, CS, FS_fit_filepath)