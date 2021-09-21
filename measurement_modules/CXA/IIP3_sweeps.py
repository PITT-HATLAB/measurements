import numpy as np 
from plottr.data import datadict_storage as dds, datadict as dd
from dataclasses import dataclass
from plottr.data.datadict_storage import all_datadicts_from_hdf5

def get_sidebands(frequency, power, small_AC_f, bw):
    
    real_pump_frequency = frequency[np.where(power == np.max(power))]

                    
    sideband_frequency = real_pump_frequency + small_AC_f
                    
    sideband_indices = np.where(  np.abs(frequency-sideband_frequency) < bw  )

    sideband_power = np.max(power[sideband_indices])
    
    return sideband_power
    

def extract_bands_IIP3(filepath, fs, bw):

    datadict = all_datadicts_from_hdf5(filepath)['data']
    
    CXA_frequency = datadict.extract('CXA_power')['CXA_frequency']['values']
    SC_power = datadict.extract('CXA_power')['SC_power']['values']
    CXA_power = datadict.extract('CXA_power')['CXA_power']['values']
    
    VNA_frequency = datadict.extract('VNA_power')['VNA_frequency']['values']
    VNA_power = datadict.extract('VNA_power')['VNA_power']['values']
    
    bands = np.zeros([len(SC_power),len(fs)])
    
    for i in range(0,len(SC_power)):
        for j in range(0,len(fs)):
            
            bands[i,j] = get_sidebands(CXA_frequency, CXA_power, fs[j], bw)
        
    return bands
    
    
def IIP3_sweep_basic(DATADIR, dataclass):
    
    #CXA.fcenter(6.1896180000e9+200)
    #CXA.fspan(600)
    
    data = dd.DataDict(
        CXA_frequency = dict(unit='Hz'),
        SC_power = dict(unit='dBm'),
        CXA_power = dict(axes=['CXA_frequency','SC_power'], unit = 'dBm'),
        VNA_frequency = dict(units='Hz'),
        VNA_power = dict(axes=['VNA_frequency','SC_power'],units='dBm')
    )
    
    DATADIR = dataclass.DATADIR
    name = dataclass.filename
    CXA = dataclass.inst_dict['CXA']
    SC = dataclass.inst_dict['SC']
    VNA = dataclass.inst_dict['VNA']
    Gen = dataclass.inst_dict['Gen']
    
    SC_power = np.linspace(dataclass.SC_p_start, dataclass.SC_p_stop, dataclass.SC_p_steps)
    
    data.validate()
    i = 0
    with dds.DDH5Writer(DATADIR, data, name=name) as writer:
        for SC_power_val in SC_power:
            
            SC.power(SC_power_val)
            CXA_frequency, CXA_power = CXA.gettrace(avgnum=10)
            
            VNA.rfout(1)
            VNA_frequency, VNA_power = VNA.gettrace()
            VNA.rfout(0)
            
            writer.add_data(
                    CXA_frequency = CXA_frequency,
                    SC_power = SC_power_val*np.ones(np.size(CXA_frequency)),
                    CXA_power = CXA_power,
                    VNA_power = VNA_power,
                    VNA_frequency = VNA_frequency
                    )
            
            i+=1
            
            
@dataclass
class IIP3_dataclass():
    cwd: str = None
    DATADIR = None
    filename: str = None
    inst_dict: dict = None
    
    bias_current: float = None
    vna_att: float = None
    gen_att: float = None
    
    #SigGen settings
    gen_freqs: np.ndarray = None
    
    #VNA settings
    vna_start: float = None
    vna_stop: float = None
        
    vna_points: float = 1601
    vna_avg_number: float = 10
    vna_power: float = -43
    
    #VNA settings
    CXA_start: float = None
    CXA_stop: float = None
        
    CXA_points: float = 1601
    CXA_avg_number: float = 10
    CXA_power: float = -43
    
    #power sweep SC settings
    SC_p_start: float = -20
    SC_p_stop: float = 15
    SC_p_steps: float = 101
    
    gen_freq_start_set: int = 0
    gen_freq_stop_set: int = 0
    
    def set_start(self): 
        self.vna_start = self.inst_dict['VNA'].fstart()
        self.vna_stop = self.inst_dict['VNA'].fstop()
        self.gen_freq_start = self.inst_dict['Gen'].frequency()
        self.gen_power_start = self.inst_dict['Gen'].power()
        self.gen_freq_start_set = 1
        self.inst_dict['SC'].output_status(0)
    
        self.CXA_start = self.inst_dict['CXA'].fstart()
        self.CXA_stop = self.inst_dict['CXA'].fstop()
    
    def goto_stop(self, gen_freq_offset = 30e6):
        if self.gen_freq_start_set: 
            self.inst_dict['Gen'].frequency(self.gen_freq_start+gen_freq_offset)
        else: 
            raise Exception('Set start first')
        
    def set_stop(self, gen_pts = 20): 
        self.vna_start = self.inst_dict['VNA'].fstart()
        self.vna_stop = self.inst_dict['VNA'].fstop()
        self.gen_freq_stop = self.inst_dict['Gen'].frequency()
        self.gen_power_stop = self.inst_dict['Gen'].power()
        
        if self.gen_freq_start_set: 
            self.gen_freqs = np.linspace(self.gen_freq_start, self.gen_freq_stop, gen_pts)
        else: 
            raise Exception('set start first')
        
    def goto_start(self):
        self.inst_dict['CS'].change_current(self.bias_current)
        self.inst_dict['Gen'].power(self.gen_power_start)
        self.inst_dict['Gen'].frequency(self.gen_freq_start)
        self.inst_dict['Gen'].output_status(1)
        self.inst_dict['VNA'].fstart(self.vna_start)
    
    def print_info(self): 
        print(self.__dict__)
        
    def renormalize(self, power = -43, avgnum = 50): 
        self.goto_start()
        self.inst_dict['Gen'].output_status(0)
        # self.inst_dict['VNA'].smoothing(1)
        self.inst_dict['VNA'].power(power)
        self.inst_dict['VNA'].renormalize(avgnum)
        self.inst_dict['VNA'].power(self.vna_power)
        # self.inst_dict['VNA'].smoothing(0)
        self.inst_dict['Gen'].output_status(1)
        
        
dataclass = IIP3_dataclass()
dataclass.inst_dict = dict([('CXA',CXA),('SC',SC9),('VNA',pVNA),('Gen',SigGen)])
