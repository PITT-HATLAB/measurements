import numpy as np 
from plottr.data import datadict_storage as dds, datadict as dd
from plottr.data.datadict_storage import all_datadicts_from_hdf5
from scipy import interpolate

class Dummy_CS():
    def __init__(self):
        pass
    
    def change_current(self,ramp_rate=None):
        pass

def decide_next_pump_power(p_pumps,gains,p_step,threshold=20):
    
    UPPER_LIMIT = 18
    LOWER_LIMIT = -19
    
    margins = 5 # how wide the taco is basically. how many extra points once we've reached the threshold, on both sides
    
    print(p_pumps)
    print(gains)
    
    return_val = 0
    
    bottom_gain = np.take(gains,np.argsort(p_pumps)[0])
    top_gain = np.take(gains,np.argsort(p_pumps)[-1])
    
    if (len(gains) > margins*2 and (bottom_gain > top_gain)):

        return_val = np.min(p_pumps) - p_step

    elif (gains[0] > threshold):
        
        gains_at_lowest_pumps = np.take(gains,np.argsort(p_pumps)[0:margins])
        
        if(len(gains) < margins):
            
            return_val = np.min(p_pumps) - p_step
            
        elif np.all(gains_at_lowest_pumps < threshold) :
            
            gains_at_highest_pumps = np.take(gains,np.argsort(p_pumps)[-margins:])
            
            if (np.all(gains_at_highest_pumps > threshold)): 
                
                return_val = None
                
            else:
                
                return_val = np.max(p_pumps) + p_step
 
        else:
            
            return_val = np.min(p_pumps) - p_step
  
    else:
        
        gains_at_lowest_pumps = np.take(gains,np.argsort(p_pumps)[0:margins])
        
        if(len(gains) < margins):
            
            return_val = np.max(p_pumps) + p_step

        elif(np.all(gains_at_lowest_pumps < threshold)):
            
            gains_at_highest_pumps = np.take(gains,np.argsort(p_pumps)[-margins:])

            if (np.all(gains_at_highest_pumps > threshold)): 
                
                return_val = None
                
            else:

                return_val = np.max(p_pumps) + p_step 
                
        else:

            return_val = np.min(p_pumps) - p_step
            
    if (return_val != None):
        
        if (np.min(p_pumps) <= LOWER_LIMIT and np.max(p_pumps) >= UPPER_LIMIT):
            
            return_val = None
            
        elif (np.min(p_pumps) > LOWER_LIMIT and np.max(p_pumps) >= UPPER_LIMIT):
            
            return_val = np.min(p_pumps[-1]) - p_step

        elif (np.min(p_pumps) <= LOWER_LIMIT and np.max(p_pumps) < UPPER_LIMIT):
            
            return_val = np.max(p_pumps) + p_step 

        elif (np.min(p_pumps) > LOWER_LIMIT and np.max(p_pumps) < UPPER_LIMIT):
            pass

    return return_val

def lambdify_omega0(FS_fit_filepath, override=None):
    dd = all_datadicts_from_hdf5(FS_fit_filepath)['data']
    
    I_b = dd['current']['values']
    omega_0 = dd['base_resonant_frequency']['values']
    
    f = interpolate.interp1d(I_b, omega_0)
    
    if (override != None):
        
        f = interpolate.interp1d(I_b, I_b*0 + override)
    
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

    I_b = np.linspace(-4.3e-5,-3.4e-5,10)
    
    Delta_f = np.linspace(0,100e6,20)
    
    p_pump_0_0 = float(-15.0) # initial pump
    
    VNA_avgs = 20
    
    VNA.power(-30)
    
    omega0 = lambdify_omega0(FS_fit_filepath)
    
    data.validate()
    
    VNA.fspan(200e6)

    gen.output_status(0)

    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        
        for i in range(0,len(I_b)):
            
            CS.change_current(I_b[i])
            
            f_pump = [2*omega0(I_b[i])]
            
            print(omega0(I_b[i]))
            VNA.fcenter(float(omega0(I_b[i])))
            
            p_pump_0 = p_pump_0_0

            for side in range(0,3):
                
                if (side == 0):
                    
                    f_pump = [2*omega0(I_b[i])]
                    
                if (side == 1):
                    
                    f_pump = 2*omega0(I_b[i]) + Delta_f[1:]
                    
                if (side == 2):
                    
                    f_pump = 2*omega0(I_b[i]) - Delta_f[1:]

                for j in range(0,len(f_pump)):
                    
                    gen.frequency(f_pump[j])
                    
                    p_pump_k = p_pump_0
                    
                    minimum_pump = -19
                    maximum_pump = 18
                    
                    Done = False
                    
                    for method in range(0,2):
                        
                        p_pumps = [p_pump_k]
                    
                        gains = []

                        while (len(p_pumps) < 20):
                            
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
                            print('Side: ' + str(side))
                            print('Method: ' + str(method))
                            print('Gmax: ' + str(G_max))
                            print('Allowed range: ' + str([minimum_pump,maximum_pump]))
                            print(' ')
                            
                            writer.add_data(
                                    f_pump = f_pump[j],
                                    p_pump = p_pump_k,
                                    I_b = I_b[i],
                                    G_max = G_max,
                                )
                            
                            
                            next_p_pump = decide_next_pump_power(p_pumps,gains,p_step)
        
                            p_pump_k = next_p_pump
                            
                            p_pumps.append(next_p_pump)
                            
                            if (next_p_pump == None or next_p_pump < minimum_pump or next_p_pump > maximum_pump):
                                
                                print('done with this frequency....')
                                
                                Done = True
                                
                                try:
                                    indices_at_least_20 = np.where(np.array(gains) >= 20)
                                    
                                    pump_at_least_20 = np.array(p_pumps)[indices_at_least_20]
                                    
                                    min_pump_at_least_20 = np.min(pump_at_least_20)
        
                                    p_pump_0 = min_pump_at_least_20
                                    
                                except:
                                    p_pump_0 = np.min(p_pumps)
                                    
                                break
                        
                        if (Done == True):
                            
                            break
                        
                        else:
                            
                            if (method == 1):
                                
                                break
                            
                            rough_p_pumps = np.arange(-18,18,2)
                            rough_gains = rough_p_pumps*0
                            
                            for k in range(0,len(rough_p_pumps)):
                                
                                gen.power(rough_p_pumps[k])
                        
                                gen.output_status(0)
                                
                                freqs = VNA.getSweepData()
                                vnadata = np.array(VNA.average(VNA_avgs))
                                
                                VNA_p_off = vnadata[0]
                                
                                gen.output_status(1)
                                
                                freqs = VNA.getSweepData()
                                vnadata = np.array(VNA.average(VNA_avgs))
                                
                                VNA_p_on = vnadata[0]
            
                                G_max = get_gain_from_trace(VNA_p_off, VNA_p_on)
                                
                                rough_gains[k] = G_max
                                
                                print('Pump power: ' + str(rough_p_pumps[k]-att))
                                print('Pump freq: ' + str(f_pump[j]))
                                print('Bias current: ' + str(I_b[i]))
                                print('Side: ' + str(side))
                                print('Method: ' + str(method))
                                print('Gmax: ' + str(G_max))
                                print(' ')
                                
                                
                                writer.add_data(
                                    f_pump = f_pump[j],
                                    p_pump = rough_p_pumps[k],
                                    I_b = I_b[i],
                                    G_max = G_max,
                                )
                             

                            rough_p_pumps_max = rough_p_pumps[np.argsort(rough_gains)[-1]]
                            
                            minimum_pump = np.clip(rough_p_pumps_max - 3,-19,18)
                            maximum_pump = np.clip(rough_p_pumps_max + 3,-19,18)
                            
                            print(' ')
                            print('New pump_k: ' + str(rough_p_pumps_max))
                            print(' ')
                            
                            p_pump_k = rough_p_pumps_max
                            
                    
                
  #%%

DATADIR = 'Z:/Data/SA_4C1_3152/gain_mapping'
name = 'gain_map_adaptive_-60dBm'
VNA = pVNA
gen = SC4
CS = yoko2
FS_fit_filepath = r'Z:/Data/SA_4C1_3152/fits/2021-12-23/2021-12-23_0088_FFS_parallel/2021-12-23_0088_FFS_parallel.ddh5'

gain_mapping(DATADIR, name, VNA, gen, CS, FS_fit_filepath, 0)