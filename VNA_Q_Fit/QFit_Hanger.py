import numpy as np
import matplotlib.pyplot as plt
import csv
import h5py
import inspect
from scipy.optimize import curve_fit
# import easygui
from plottr.data import datadict_storage as dds, datadict as dd
from plottr.data.datadict_storage import all_datadicts_from_hdf5

FREQ_UNIT = {'GHz' : 1e9,
             'MHz' : 1e6,
             'KHz' : 1e3,
             'Hz' : 1.0
             }


def rounder(value):
    return "{:.4e}".format(value)

def reflectionFunc(freq, Qext, Qint, f0, magBack, phaseCorrect):
    omega0 = f0
    delta = freq - omega0
    S_11_up = 1.0 / (1j * delta * (2 + delta / omega0) / (1 + delta / omega0) + omega0 / Qint) - Qext / omega0
    S_11_down = 1.0 / (1j * delta * (2 + delta / omega0) / (1 + delta / omega0) + omega0 / Qint) + Qext / omega0
    S11 = magBack * (S_11_up / S_11_down) * np.exp(1j * (phaseCorrect))
    realPart = np.real(S11)
    imagPart = np.imag(S11)

    return (realPart + 1j * imagPart).view(float)
    # return realPart 
    # return imagPart 
    
def hangerFunc(freq, Qext, Qint, f0, magBack, phaseCorrect):
    omega0 = f0
    delta = freq - omega0
    
    x = -(freq - omega0 - delta)/(omega0 + delta)
    S21_up = Qext + 1j * Qext * Qint * (2 * x + 2 * delta / omega0)
    S21_down = (Qint + Qext) + 2 * 1j * Qext * Qint * x

    S21 = magBack * (S21_up / S21_down) * np.exp(1j * (phaseCorrect))
    realPart = np.real(S21)
    imagPart = np.imag(S21)
    
    return S21.view(float)

def hangerFunc_re(freq, Qext, Qint, f0, magBack, phaseCorrect):
    return hangerFunc(freq, Qext, Qint, f0, magBack, phaseCorrect)[::2]

def reflectionFunc_re(freq, Qext, Qint, f0, magBack, phaseCorrect):
    return reflectionFunc(freq, Qext, Qint, f0, magBack, phaseCorrect)[::2]

def getData_from_datadict(filepath, plot_data = None): 
    datadict = all_datadicts_from_hdf5(filepath)['data']
    powers_dB = datadict.extract('power')['power']['values']
    freqs = datadict.extract('power')['frequency']['values']*2*np.pi
    phase_rad = datadict.extract('phase')['phase']['values']
    
    lin = np.power(10, powers_dB/20)
    real = lin*np.cos(phase_rad)
    imag = lin*np.sin(phase_rad)
    
    
    if plot_data:
        plt.figure('mag')
        plt.plot(freqs, powers_dB)
        plt.figure('phase')
        plt.plot(freqs, phase_rad)
        
    return (freqs, real, imag, powers_dB, phase_rad)
    
    
def getData(filename, method='hfss', freq_unit = 'GHz', plot_data=1):
    if method == 'hfss':
        """The csv file must be inthe format of:
            freq  mag(dB)  phase(cang_deg)  
        """
        with open(filename) as csvfile:
            csvData = list(csv.reader(csvfile))
            csvData.pop(0)  # Remove the header
            data = np.zeros((len(csvData[0]), len(csvData)))
            for x in range(len(csvData)):
                for y in range(len(csvData[0])):
                    data[y][x] = csvData[x][y]

        freq = data[0] * 2 * np.pi * FREQ_UNIT[freq_unit] #omega
        phase = np.array(data[2]) / 180. * np.pi
        mag = data[1]
        lin = 10**(mag / 20.0)
        
    elif method == 'vna':  
        f = h5py.File(filename,'r')
        freq = f['VNA Frequency (Hz)'][()]*2*np.pi
        phase = f['Phase (deg)'][()]
        mag = f['Power (dB)'][()]
        lin = 10**(mag/20.0)
        f.close()
        
    elif method == 'vna_old': 
        f = h5py.File(filename,'r')
        freq = f['Freq'][()]*2 * np.pi
        phase = f['S21'][()][1] / 180. * np.pi
        mag = f['S21'][()][0]
        lin = 10**(mag / 20.0)
        f.close()
        
    else:
        raise NotImplementedError('method not supported')
        
    imag = lin * np.sin(phase)
    real = lin * np.cos(phase)
    
    if plot_data:
        plt.figure('mag')        
        plt.plot(freq/2/np.pi, mag)
        plt.figure('phase')
        plt.plot(freq/2/np.pi, phase)
        
    return (freq, real, imag, mag, phase)
    
    # if method == 'vna':  
    #     f = h5py.File(filename,'r')
    #     freq = f['VNA Frequency (Hz)'][()]
    #     phase = f['Phase (deg)'][()] / 180. * np.pi
    #     lin = 10**(f['Power (dB)'][()] / 20.0)
    # if method == 'vna_old': 
    #     f = h5py.File(filename,'r')
    #     freq = f['Freq'][()]
    #     phase = f['S21'][()][0] / 180. * np.pi
    #     lin = 10**(f['S21'][()][1] / 20.0)
        

def fit(freq, real, imag, mag, phase, Qguess=(2e5, 1e5),real_only = 0, bounds = None, f0Guess = None, magBackGuess = None, phaseGuess = 0):
    # f0Guess = 2*np.pi*5.45e9
    # f0Guess = freq[np.argmin(mag)] #smart guess of "it's probably the lowest point"
    if f0Guess == None:
        # f0Guess = freq[int(np.floor(np.size(freq)/2))] #dumb guess of "it's probably in the middle"
        f0Guess = freq[np.argmin(mag)] #smart guess of "it's probably the lowest point"
    print("Guess freq: "+str(f0Guess/(2*np.pi*1e9)))
    lin = 10**(mag / 20.0)
    if magBackGuess == None: 
        magBackGuess = np.average(lin[:int(len(freq) / 5)])
    # print(f"MAGBACKGUESS: {magBackGuess}")
    QextGuess = Qguess[0]
    QintGuess = Qguess[1]
    if bounds == None: 
        bounds=([QextGuess / 10, QintGuess /10, f0Guess/1.5, magBackGuess / 10, -np.pi],
                [QextGuess * 10, QintGuess * 10, f0Guess*1.5, magBackGuess * 10, np.pi])
    
    target_func = hangerFunc
    data_to_fit = (real  + 1j * imag).view(float)
    if real_only:
        target_func = hangerFunc_re
        data_to_fit = real
    popt, pcov = curve_fit(target_func, freq, data_to_fit, 
                            p0=(QextGuess, QintGuess, f0Guess, magBackGuess, phaseGuess),
                            bounds=bounds,
                            maxfev=1e4, ftol=2.3e-16, xtol=2.3e-16)
    

    return popt, pcov


def plotRes(freq, real, imag, mag, phase, popt):
    xdata = freq/ (2 * np.pi)
    realRes = hangerFunc(freq, *popt)[::2]
    imagRes = hangerFunc(freq, *popt)[1::2]
    # realRes = reflectionFunc(freq, *popt)
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.title('real')
    plt.plot(xdata, real, '.')
    plt.plot(xdata, realRes)
    plt.subplot(1, 2, 2)
    plt.title('imag')
    plt.plot(xdata, imag, '.')
    plt.plot(xdata, imagRes)
    plt.show()


if __name__ == '__main__':
    # filepath = easygui.fileopenbox()
    filepath = r'X:/Data/HuntCollab2/hBN_cap/20210823_cooldown/2021-08-23/2021-08-23_0002_13_169_ghz_reso/2021-08-23_0002_13_169_ghz_reso.ddh5'
    (freq, real, imag, mag, phase) = getData_from_datadict(filepath, plot_data=0)
    ltrim = 0
    rtrim = 1
    freq = freq[ltrim:-rtrim]
    real = real[ltrim:-rtrim]
    imag = imag[ltrim:-rtrim]
    mag = mag[ltrim:-rtrim]
    phase = phase[ltrim:-rtrim]
    
    popt, pcov = fit(freq, real, imag, mag, phase, Qguess=(1e5, 1e4), magBackGuess = 1e-4, phaseGuess = 0, f0Guess = None)  #(ext, int)   
    print(f'f (Hz): {rounder(popt[2]/2/np.pi)}', )
    fitting_params = list(inspect.signature(hangerFunc).parameters.keys())[1:]
    for i in range(2):
        print(f'{fitting_params[i]}: {rounder(popt[i])} +- {rounder(np.sqrt(pcov[i, i]))}')
    Qtot = popt[0] * popt[1] / (popt[0] + popt[1])
    print('Q_tot: ', rounder(Qtot), '\nT1 (s):', rounder(Qtot/popt[2]), f"Kappa: {rounder(popt[2]/2/np.pi/Qtot)}", )
    print("Magback val: ", popt[3])
    

    plotRes(freq, real, imag, mag, phase, popt)

