import numpy as np 
from plottr.data import datadict_storage as dds, datadict as dd
from plottr.data.datadict_storage import all_datadicts_from_hdf5
from scipy import interpolate

def decide_next_pump_power(p_pumps,gains,p_step,threshold=20):
    
    UPPER_LIMIT = 19
    LOWER_LIMIT = -20
    
    next_pump = None
    
    margins = 5 # how wide the taco is basically. how many extra points once we've reached the threshold, on both sides
    
    print(gains)
    
    if (len(gains) > margins*2):
        
        bottom_gain = np.take(gains,np.argsort(p_pumps)[0])
        top_gain = np.take(gains,np.argsort(p_pumps)[-1])
        
        if(bottom_gain > top_gain):
            
            return None
    
    if gains[0] > threshold:
        
        if(len(gains) < margins):
            
            print('a')
            
            return np.min(p_pumps[-1]) - p_step
            
        gains_at_lowest_pumps = np.take(gains,np.argsort(p_pumps)[0:margins])
        
        
        if(np.all(gains_at_lowest_pumps < threshold)):
            
            gains_at_highest_pumps = np.take(gains,np.argsort(p_pumps)[-margins:])
            
            if (np.all(gains_at_highest_pumps > threshold)): 
                
                print('c')
                
                return None
                
            else:
                
                print('d')
                
                return np.max(p_pumps) + p_step
 
        else:
            
            print('e')
            
            return np.min(p_pumps[-1]) - p_step
  
    else:
        
        if(len(gains) < margins):
        
            print('f')
            
            return np.max(p_pumps) + p_step

        gains_at_highest_pumps = np.take(gains,np.argsort(p_pumps)[-margins:])
        
        if(np.all(gains_at_highest_pumps > threshold)):
            
            gains_at_lowest_pumps = np.take(gains,np.argsort(p_pumps)[0:margins])

            
            if (np.all(gains_at_lowest_pumps < threshold)): 
                
                print('h')
                
                return None
                
            else:
                
                print('j')
                
                return np.min(p_pumps) - p_step 
                
        else:
            
            print('j')
            
            return np.max(p_pumps) + p_step

def lambdify_omega0(FS_fit_filepath):
    dd = all_datadicts_from_hdf5(FS_fit_filepath)['data']
    
    I_b = dd['current']['values']
    omega_0 = dd['base_resonant_frequency']['values']
    
    f = interpolate.interp1d(I_b, omega_0)
    
    return f
    
def get_gain_from_trace(VNA_p_off, VNA_p_on, width = 10):
    
    
    p_max = np.max(VNA_p_on)
    
    max_index = np.min(np.where(p_max == VNA_p_on))

    left_index = np.max([0,max_index-width])
    right_index = np.min([len(VNA_p_off),max_index+width])
    
    p_off = np.mean(VNA_p_off[left_index:right_index])
    
    p_on = np.mean(VNA_p_on[left_index:right_index])
    
    G = p_on - p_off # gain
    
    return G

def gain_mapping(DATADIR, name, VNA, gen, CS, FS_fit_filepath,att,p_step=0.1):
        
    data = dd.DataDict(
        f_pump = dict(unit='Hz'),
        p_pump = dict(unit='dBm'),
        I_b = dict(unit='A'),
        G_max = dict(axes=['f_pump','p_pump','I_b'], unit = 'dBm'))

    I_b = np.linspace(-4.4e-5,-3.4e-5,11)
    
    Delta_f = np.linspace(0,100e6,20)
    
    p_pump_0_0 = float(-5.0) # initial pump
    
    VNA_avgs = 20
    
    VNA.power(-30)
    
    omega0 = lambdify_omega0(FS_fit_filepath)
    
    data.validate()
    
    VNA.fspan(100e6)

    gen.output_status(0)

    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        
        for i in range(0,len(I_b)):
            
            CS.change_current(I_b[i], ramp_rate = 1e-5)
            
            f_pump = [2*omega0(I_b[i])]
            
            print(omega0(I_b[i]))
            VNA.fcenter(float(omega0(I_b[i])))
            
            for side in range(0,3):
                
                p_pump_0 = p_pump_0_0
                
                if (side == 0):
                    
                    f_pump = [2*omega0(I_b[i])]
                    
                if (side == 1):
                    
                    f_pump = 2*omega0(I_b[i]) + Delta_f[1:]
                    
                if (side == 2):
                    
                    f_pump = 2*omega0(I_b[i]) - Delta_f[1:]
                    
                
                
                for j in range(0,len(f_pump)):
                    
                    gen.frequency(f_pump[j])
                    
                    p_pump_k = p_pump_0
                    
                    p_pumps = [p_pump_0]
                    
                    gains = []
                                    
                    while (True):
                        
                        gen.power(p_pump_k)
                        
                        gen.output_status(0)
                        
                        freqs = VNA.getSweepData()
                        vnadata = np.array(VNA.average(VNA_avgs))
                        
                        VNA_p_off = vnadata[0]
                        
                        gen.output_status(1)
                        
                        freqs = VNA.getSweepData()
                        vnadata = np.array(VNA.average(VNA_avgs))
                        
                        VNA_p_on = vnadata[0]
    
                        G_max = get_gain_from_trace(VNA_p_off, VNA_p_on)
                        
                        gains.append(G_max)
                        
                        print('Pump power: ' + str(p_pump_k-att))
                        print('Pump freq: ' + str(f_pump[j]))
                        print('Bias current: ' + str(I_b[i]))
                        
                        print(G_max)
                        
                        
                        print(p_pump_k)
                        writer.add_data(
                                f_pump = f_pump[j],
                                p_pump = p_pump_k,
                                I_b = I_b[i],
                                G_max = G_max,
                            )
                        
                        
                        next_p_pump = decide_next_pump_power(p_pumps,gains,p_step)
    
                        p_pump_k = next_p_pump
                        
                        p_pumps.append(next_p_pump)
                        
                        if (next_p_pump == None or next_p_pump > 19 or next_p_pump < -15):
                            p_pump_0 = float(np.mean(p_pumps[:-1])//p_step*p_step)
                            break
                    
                
#%%

DATADIR = 'Z:/Data/SA_4C1_3152/gain_mapping'
name = 'gain_map_adaptive_-60dBm'
VNA = pVNA
gen = SC4
CS = yoko2
FS_fit_filepath = r'Z:/Data/SA_4C1_3152/fits/2021-12-23/2021-12-23_0088_FFS_parallel/2021-12-23_0088_FFS_parallel.ddh5'

gain_mapping(DATADIR, name, VNA, gen, CS, FS_fit_filepath, 10)