# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 13:50:37 2016

A module that allows users to select between 3 different methods,
    - 1: hanger_transmission
    - 2: reflection
    - 3: transmission
to supplied data. It uses lmfit for fitting and Hatlab defined initial guesses.

@license:  Use only under the permission of Dr. Michael Hatridge
Unauthorized use will result in termination(from the planet)

@author: Olivia Lanes and Alex Rowden and Erick Brindock and Xi Cao
aka the best people in Hatlab (Erick wrote that I swear)
"""

# Use lmfit to fit S11

import lmfit as lmf
import numpy as np
import matplotlib.pyplot as plt
import csv
import math
import h5py as h5
#import hdf5_data as h5


def linear_model(params, freq):
    values = params.valuesdict()
    slope = values['slope']
    offset = values['offset']
    
    return slope * freq + offset
    
def linear(phase, freq):
    offset = phase[0]
    slope = (phase[-1] - phase[0]) / (freq[-1] - freq[0])
    
    params = lmf.Parameters()
    params.add('slope', value = slope)
    params.add('offset', value = offset)
    
    return lmf.minimize(linear_residuals, params, args=(linear_model, phase, freq))
    
def linear_residuals(params, model, phase, freq):
    return model(params, freq) - phase

def transmission_model(params, f, do_float = True):
    '''
    This is the model will be used for the fitting.
    
    Input:
    ------
        **params**:
        (dict type), include all the initial guess for the fitting
        **f**:
        (np.array), the frequency
        **do_float**:
        (boolean), control if we want the output to be float number or complex number
    
    Output:
    -------
    
        value of S21, float or complex number
        
    Raises:
        None
    '''
    value = params.valuesdict() 
    f0 = value['f0']
    Q1 = value['Q1']
    Q2 = value['Q2']
    A = value['A']
    B = value['B']
    C = value['C']
    
    omega = f
    omega0 = f0    
    q1 = np.sqrt(1.0/Q1)
    q2 = np.sqrt(1.0/Q2)
    delta = - omega + omega0
    k1 = (q1**2)*omega
    k2 = (q2**2)*omega
    T0 = np.sqrt(k1*k2)/((k1+k2)/2.0)
    S21 = C*T0/(1-1j*delta/((k1+k2)/2.0))*np.exp(1j*(A*omega + B))

    if not do_float:
        return S21
    return S21.view(np.float)


def reflection_model(params, omega, do_float=True):
    '''
    This function will produce a curve for reflection based off of the parameters in the given dictionary.
    
    **Input**:
    ---------
        **params**:
        A dictionary of parameters which contains the following
            - f_0
            - Q_ext
            - Q_int
            - A
            - B
            - E
        **omega**:
        An array of floats
    Output:
    -------
        An numpy array of floats that represents the model.
    Raises:
    -------
        None
    '''
    value = params.valuesdict() 
    f0 = value['f0']
    Q_ext = value['Q_ext']
    Q_int = value['Q_int']
    A = value['A']
    B = value['B']
    E = value['E']

    
    omega0 = f0
    delta = omega - omega0
    
    S_11_up = 1.0/(1j*delta*(2+delta/omega0)/(1+delta/omega0) + omega0/Q_int) - Q_ext/omega0
    S_11_down = 1.0/(1j*delta*(2+delta/omega0)/(1+delta/omega0) + omega0/Q_int) + Q_ext/omega0

    S_11 = A*(S_11_up/S_11_down)*np.exp(1j*(E*omega+B))

    if not do_float:
        return S_11

    return S_11.view(np.float)    





def hanger_transmission_model(params, omega, do_float=True):
    '''
    This function will produce a curve for hanger_transmission based off of the parameters in the given dictionary.
    
    Input:
    ------
        **params**: 
        A dictionary of parameters which contains the following
            - f_0
            - Q_ext
            - Q_int
            - deltaf
            - A
            - B
            - E
        **omega**: 
        An array of floats
    Output:
    ------
        An numpy array of floats that represents the model.
    Raises:
    ------
        None
    '''
    value = params.valuesdict() 
    f0 = value['f0']
    Q_ext = value['Q_ext']
    Q_int = value['Q_int']
    deltaf = value['deltaf']
    # A = value['A']
    B = value['B']
    E = value['E']
    slope =value ['slope']
    
    omega0=f0
    x = -(omega - omega0 - deltaf)/(omega0 + deltaf)
    S_21_up = Q_ext + 1j * Q_ext * Q_int * (2 * x + 2 * deltaf / omega0)
    S_21_down = (Q_int + Q_ext) + 2 * 1j * Q_ext * Q_int * x

    S_21=slope * (S_21_up / S_21_down) * np.exp(1j * (E * omega + B))
#    S_21 = A * np.conjugate((S_21_up / S_21_down)) * np.exp(1j * (E * omega + B))

    if not do_float:
        return S_21

    return S_21.view(np.float64)


def get_phase(x,y):
    '''
    Calculates the phase angle between x and y.  Behavior is identical to 
    numpy.arctan2(y,x).
    
    Input:
    ------
        **x**: 
        array_like, real_valued numerator to be given to arctan2.
        
        **y**:
        array_like, real_valued denominator to be given to arctan2.
    Output:
    -------
        numpy array of phase angles in radians
    Raises:
    -------
        None
    '''
    return np.arctan2(y,x)
  
def getData(filename, method = 1):
    '''
    Function that takes a filename and processes it if it is of a known type and returns 3 arrays.
    Current known types include:
        - .csv
        - .txt
        - .tab
    Input:
    ------
        **filename**: A string that points to a file which contains properly formatted data.
    Output:
    -------
        2D array that contains three arrays.  These arrays are:
        
            - **freq**: Frequency.
            - **real**: Real component.
            - **imag**: Imaginary component.
    Raises:
    -------
        **IOError**: if file extension is not .csv or .txt
    '''
    #Find the file type to learn how to process it.    
    file_components = filename.split(".")
    file_ext = file_components[-1]
        
        
    if(file_ext == "csv"):
        # Open .csv file and read the frequencies, real parts, and imaginary parts
        with open(filename, 'rb') as   csvfile:
            csvData=list(csv.reader(csvfile))
            if method != 4 and method != 5:
                csvData.pop(0) # Remove the header
            data=np.zeros((len(csvData[0]),len(csvData)))
            for x in range(len(csvData)):
                for y in range(len(csvData[0])):
                    data[y][x]=csvData[x][y]
        return data
    elif(file_ext == "txt"):
        rawdata = np.genfromtxt(filename, delimiter='\t', skip_header = 1)
        
        # Here Olivia processes the raw data into handy arrays and then NEVER calls rawdata again.
        freq = rawdata[:,0]
        s11_data_real = rawdata[:,1]
        s11_data_imag = rawdata[:,2]
        return (freq, s11_data_real, s11_data_imag)
    elif(file_ext == "tab"):
        rawdata = np.genfromtxt(filename, delimiter='\t', skip_header = 1, skip_footer = 1)
        
        # Here Olivia processes the raw data into handy arrays and then NEVER calls rawdata again.
        freq = rawdata[:,0]
        s11_data_real = rawdata[:,1]
        s11_data_imag = rawdata[:,2]
        return (freq, s11_data_real, s11_data_imag)
    else:
        try:
            f = h5.File(filename)
            freq =  np.array(f["Freq"].value)
            mag = np.array(f["S21"].value[0])
            phase = np.array(f["S21"].value[1])*np.pi/180.0
            lin = 10**(mag/20.0)
            
            imag = lin*np.sin(phase)
            real = lin*np.cos(phase)
            
            return (freq, real, imag)
        except IOError:
            print("IOError occurred.")
        

def _residuals(params, model, real, imag, omega):    
    '''Used internally (should be private but NO)'''
    model_data = model(params, omega)
    sample_data = (real + imag * 1j).view(np.float)
    print("Model Data size: ", np.shape(model_data))
    print(model_data)
    print("sample size: ", np.shape(sample_data))
    print(sample_data)
    print(model_data - np.array(sample_data))
    return (model_data - np.array(sample_data)).view(np.float64) 
    
def printParams(dictionary):
    '''
    A function which will print all of the enteries in the parameter list
    
    Input:
    -----

        **dictionary**:
        A dictionary of parameters to be printed.
    
    Output:
    -------
    
        None
        
    Raises:
    -------
    
        None
    '''
    
    for key in dictionary.keys():
        print("Key: " + str(key) + " Value: %e" % dictionary[key])
    
def get_f0(out):
    '''
    A get for the resonant frequency.
    
    Input:
    -----
        **out**:
        The output from a call to lmf.minimize().
        
    Output:
    -------
        **f_0**:
        The resonant frequency.
        
    Raises:
    -------
        None
    '''
    return out.params.valuesdict()['f0']
    
def get_Q1(out):
    '''
    A get for the quality factor corresponding to port 1.
    
    Input:
    -----
        **out**:
        The output from a call to lmf.minimize().
        
    Output:
    -------
        **Q1**:
        The quality factor corresponding to port 1.
        
    Raises:
    -------
        None
    '''
    return out.params.valuesdict()['Q1']

def get_Q2(out):
    '''
    A get for the quality factor corresponding to port 2.
    
    Input:
    -----
        **out**:
        The output from a call to lmf.minimize().
        
    Output:
    -------
        **Q2**:
        The quality factor corresponding to port 2.
        
    Raises:
    -------
        None
    '''
    return out.params.valuesdict()['Q2']
    
def get_Q_int(out):
    '''
    A get for the Internal Q.
    
    Input:
    -----
        **out**:
        The output from a call to lmf.minimize().
        
    Output:
    -------
        **Q_int**:
        The Internal Q.
        
    Raises:
    -------
        None
    '''
    return out.params.valuesdict()['Q_int']

def get_Q_ext(out):
    '''
    A get for the external Q.
    
    Input:
    -----
        **out**:
        The output from a call to lmf.minimize().
        
    Output:
    -------
        **Q_ext**: 
        The External Q.
        
    Raises:
    -------
        None
    '''
    return out.params.valuesdict()['Q_ext']
    
    
def file_fit(filename, plot = False, method = None, conjugate = False):
    '''
    This method calls for the method to be unpacked by getData and then calls the fit function.
    
    Input: 
    ------
        **filename**:
        A string that points to a file to be processed that will provide freq, real, and imag for fit.
        
        *Keyword Arguements*
        
        **params**:
        A dictionary of parameters.
        
        **plot**:
        A boolean that indicates if plots should be created.
        
        **method**:
        A number that determines what method should be used. If none is given, an error is thrown.
        
        **conjugate**: 
        A boolean saying whether or not to take the conjugate of the data
        
    Output:
    -------
    
        **F0**: Resonant frequency.
        
        **Q_ext**: External Q.
        
        **Q_int**: Internal Q.
        
        **out**: Fit output.
        
    Raises:
    ------
        Error if no method is selected or if get Data or fit return an error.
    '''
    if filename is not None:
        if method != 5:
            freq, real, imag = getData(filename, method) 
        else:
            real, imag = getData(filename, method)
            freq = np.arange(0, 3e-7*len(real), 3e-7)
          
    else:
        raise ValueError("No file given")
    return fit(freq, real, imag, plot = plot, method = method, conjugate = conjugate)
  
def fit(freq, real, imag, plot = False, method = None, conjugate = False):
    '''
    This is the function you call to actual fit your data. Use Method 1 for all normal data.         
    Add fit parameters you need to fit parameter class.
    
    Input: 
    ------
        **freq**: 
        An array of floats of size n.
        
        **real**:
        An array of floats of size n.
        
        **imag**:
        An array of floats of size n.
        
        *Keyword Arguements*
        
        **params**: 
        A dictionary of parameters.
        
        **plot**:
        A boolean that indicates if plots should be created.
        
        **method**: 
        A number that determines what method should be used. If none is given, an error is thrown.
        
        **conjugate**: 
        A boolean saying whether or not to take the conjugate of the data
        
    Output:
    -------
        
        - Method 1 and 2
    
            **F0**: Resonant frequency.
            
            **Q_ext**: External Q.
            
            **Q_int**: Internal Q.
            
            **out**: Fit output.
            
            
        - Method 3
        
            **F0**: Resonant frequency.
            
            **Q_1**: The Q corresponding to the first port.
            
            **Q_2**: The Q corresponding to the second port.
            
            **out**: Fit output.
        
    Raises:
    -------
        Error if no method is selected.
    '''     
    
    if conjugate:
        imag *= -1
    
    if method is None:
        raise ValueError("No method selected")

    if method == 1 :
        out = hanger_transmission(freq, real, imag)
        
        F0, Q_E, Q_I = get_f0(out), get_Q_ext(out), get_Q_int(out)
        printParams(out.params.valuesdict())
    
        if plot:
            result = hanger_transmission_model(out.params ,freq)
            
            
    elif method == 2:
        out = reflection(freq, real, imag)
        F0, Q_E, Q_I = get_f0(out), get_Q_ext(out), get_Q_int(out)
        printParams(out.params.valuesdict())
        
        if plot:
            result = reflection_model(out.params, freq)
    elif method == 3:
        out = transmission(freq, real, imag)
        F0, Q_E, Q_I = get_f0(out), get_Q1(out), get_Q2(out)
        printParams(out.params.valuesdict())
        
        if plot:
            result = transmission_model(out.params, freq)
            
    elif method == 4:
        out = t1(freq, real, imag)
        F0, Q_E, Q_I = 0,0,0
        printParams(out.params.valuesdict())
        
        if plot:
            result = t1_model(out.params, freq)

    elif method == 5:
        out = t2(freq, real, imag)
        F0, Q_E, Q_I = 0,0,0
        printParams(out.params.valuesdict())
        
        if plot:
            result = t2_model(out.params, freq)
            
    if plot:
        plot_fit(freq, real, imag, result, method = method)
 


    return (F0, Q_E, Q_I, out)

def plot_fit(freq, real, imag, result, method = 1):
    '''
    This function plots the recieved data against the fit.
    
    Input:
    ------
        
        **freq**:
        An array of floats of size n that represents frequencies.
        
        **real**:
        An array of floats of size n that represents the real component of that which is fitted.
        
        **imag**:
        An array of floats of size n that represents the imag component of that which is fitted.
        
        **result**:
        An array of floats that contains the representation of the final fit function.
        
    Output:
    ------
        None
        
    Raises:
    -------
        None
    '''
    if method != 4 and method != 5:
        result_real = np.zeros(len(result)/2)
        result_imag = np.zeros(len(result)/2)
      #          result_mag = np.zeros(len(result)/2)
        result_phase = np.zeros(len(result)/2)
        real_phase = np.zeros(len(result)/2)
           
        for i in range(len(result)/2):
            result_real[i] = result[2*i]
            result_imag[i] = result[2*i+1]
    #                result_mag[i] = np.sqrt(result[2*i]**2+result[2*i+1])
            result_phase[i] = get_phase(result[2*i],result[2*i+1])
            real_phase[i] = get_phase(real[i], imag[i])
               
        plt.close('all')
       
        plt.figure(1)   
        plt.plot(freq,result_real, 'r')
        plt.plot(freq, real, 'b+')
        plt.legend(['Fit','Data'])
        plt.xticks(rotation = 45)
        plt.xlabel("Frequency (GHz)")
        plt.ylabel("S11 Real")
        plt.title("S11 Real")
        
    
        plt.figure(2) 
        plt.plot(freq,result_imag, 'r')
        plt.plot(freq, imag, 'b+')
        plt.legend(['Fit','Data'])
        plt.xlabel("Frequency (GHz)")
        plt.xticks(rotation = 45)
        plt.ylabel("S11 Imaginary")
        plt.title("S11 Imaginary")
    
        plt.figure(3)
        plt.plot(freq, np.unwrap(result_phase), 'r')
        plt.plot(freq, np.unwrap(real_phase),'b+') 
        plt.legend(['Fit','Data'])
        plt.xlabel("Frequency (GHz)")
        plt.xticks(rotation = 45)
        plt.ylabel("Phase")
        plt.title("Phase")    
    
        
        plt.figure(4)
        plt.plot(result_real, result_imag, 'r')
        plt.plot(real, imag, 'b+')
        plt.legend(['Fit','Data'])
        plt.xlim([-1,1])
        plt.ylim([-1,1])
        plt.title("Smith Chart")    
    
        plt.figure(5)
        MagV = np.sqrt(real**2+imag**2)
        logMag = 20*np.log10(MagV)
        result_MagV = np.sqrt(result_real**2+result_imag**2)
        result_log_Mag=20*np.log10(result_MagV)
        plt.plot(freq,result_log_Mag,'r')
        plt.plot(freq,logMag,'b+')
        plt.xticks(rotation = 45)
        plt.legend(['Fit','Data'])
        plt.xlabel("Frequency (GHz)")
        plt.ylabel("Mag (lin pwr)")
        plt.title("Mag in dB")
        plt.show()
    else:
        plt.plot(freq, real)
        plt.plot(freq, result[0:-1:2])
        plt.xlabel("Time(s)")
        plt.ylabel("probably volts")
        plt.title("T1 or T2R or T2E whatevs")
        plt.show()
        

#method1
def hanger_transmission(freq, real, imag):
    '''
    Function that calculates paramaeters and fits the data using hanger transmission
    
    Input:
    ------
    
        **freq**:
        An array of floats of size n that represents frequencies.
        
        **real**:
        An array of floats of size n that represents the real component of that which is fitted.
        
        **imag**:
        An array of floats of size n that represents the imag component of that which is fitted.
        
    Output:
    -------
        
        (`MinimizerResult <https://lmfit.github.io/lmfit-py/fitting.html#lmfit.minimizer.MinimizerResult>`_) see documentation for specifics 
        
    Raises:
    -------
        
        None
    '''
    s21data=real+1j*imag

    #find min power S21 and f@ which min occurs
    mins21=np.min(abs(s21data)**2)
    fmin=freq[np.argmin(abs(s21data)**2)]
    f0_guess=fmin
    #A is scaling factor we extract from left end of array (in power units)
    B=abs(s21data[0]**2)
    
    #average power 1/2 height we use to calc. half width or Qtot
    halfheight=((B+mins21)/2.0)
    
    
    #use half height ot calc. freq @ 1/2 amplitude response and use for bandwidth
    reached = False
    
    f1 = None
    f2= None
    
    for point in range(len(s21data)):
        if abs(s21data[point])**2 <= halfheight and not reached:
            f1 = freq[point]
            reached=True
        elif(abs(s21data[point])**2 >= halfheight) and reached:
            f2 = freq[point]
            break;
            
    bandwidth = f2 - f1
    Q_tot_guess = f0_guess/ bandwidth
    
    #use minimum s21 to calc. Qint as fcn. of total Q
    
    Q_int_guess=np.sqrt(B/mins21)*Q_tot_guess
    
    Q_ext_guess=(-1/Q_int_guess+1/Q_tot_guess)**(-1) 
    
    slope = (s21data[9]-s21data[0])/(freq[9]-freq[0])
    
    #calc phase slope of first 10 points for guess
    phase=np.unwrap(np.arctan2(np.imag(s21data),np.real(s21data)),discont=np.pi*3/2)
    E_guess=(phase[9]-phase[0])/(freq[9]-freq[0])
    
    fit_params = lmf.Parameters()
        

    fit_params.add('f0',value = f0_guess,  vary= True)
    fit_params.add('deltaf', value = 0, vary = True)
    fit_params.add('Q_ext',value = Q_ext_guess, min=0, vary = True)
    fit_params.add('Q_int',value = Q_int_guess, min=0, vary = True)
#    fit_params.add('A',value = 1,  vary = True)
    fit_params.add('B', value = B, vary = True)
    fit_params.add('E', value = E_guess, vary = True)
    fit_params.add('slope', value =slope, vary = True)

    out=lmf.minimize(_residuals, fit_params, args=(hanger_transmission_model ,real, imag, freq))
    
    return out
    
    
#method 2
def reflection(freq, real, imag):
    '''
    Function that calculates paramaeters and fits the data to reflection
    
    Input:
    ------
    
        **freq**:
        An array of floats of size n that represents frequencies.
        
        **real**:
        An array of floats of size n that represents the real component of that which is fitted.
        
        **imag**:
        An array of floats of size n that represents the imag component of that which is fitted.
        
    Output:
    -------
        
        (`MinimizerResult <https://lmfit.github.io/lmfit-py/fitting.html#lmfit.minimizer.MinimizerResult>`_) see documentation for specifics 
        
    Raises:
    -------
        
        None
    '''
    s11data=real+1j*imag

#   Need to find the break in the circle in the IQ space. Break comes after 1st point and before last.
    phase=np.unwrap(np.arctan2(np.imag(s11data),np.real(s11data)))
    
    slice_cutoff = int(np.floor(len(phase) * .02))
    
    out = linear(phase[0:slice_cutoff], freq[0:slice_cutoff]).params.valuesdict()  
    
    s11data_corr = s11data * np.exp(1j * -out['slope'] * freq)
    
    phase_corr=np.unwrap(np.arctan2(np.imag(s11data_corr),np.real(s11data_corr)))
    
#     s21 at infinity
    
    #infinity point 
    pleft=(s11data_corr[0]+s11data_corr[-1])/2.0
    
    
    distance=np.abs(s11data_corr-pleft)
    index_pright = np.argmax(distance)
    pright=s11data_corr[index_pright]
    
    
    #Point of f0
    pcenter=(pleft + pright)/2.0
    
    
    #radius of circle
    rad=np.abs(pleft-pright)/2.0
    print(rad)   
    
    newarray=np.abs(distance-np.sqrt(2)*rad)
    
    #90 degree points which will give us the bandwidth and thus the Q total
    extrema = list([np.argmin(newarray[:index_pright]), np.argmin(newarray[index_pright:-1]) + index_pright])
    
    bandwidth=np.abs(freq[extrema[0]]-freq[extrema[1]])
   
    #Find the Q's
    f_0 = freq[index_pright]
    
    Qtot = f_0 / bandwidth
    
    denominator =(np.abs(pleft) - np.abs(s11data_corr[index_pright])) / np.abs(pleft)
           

    Q_int = -Qtot * 2 / denominator
    if (Q_int > Qtot):
        Q_ext = (1 / Qtot - 1 / Q_int)**(-1)
    else:
       Q_ext=10**3 * Qtot
    print(f_0)
    print(Q_int)
    print(Q_ext)
    fit_params = lmf.Parameters()
    
#    Q_int = 500
#    Q_ext = 50
#    f_0 = 4.84e9
    f_0 = 7.146e9
    
    fit_params.add('f0',value = f_0, min=0, vary = False) #min = 9.2e9, max = 9.31e9,
    fit_params.add('Q_int',value = Q_int, min=0, vary= True)
    fit_params.add('Q_ext', value = Q_ext, min=0, vary = True)
    fit_params.add('A', value = 0.01 , min=0, vary=True)
    fit_params.add('B', value = np.pi - out['offset'],  vary= True)
    fit_params.add('E', value = out['slope'], vary = True)
      
    
    # Do the fitting and print out the result
    return lmf.minimize(_residuals, fit_params, args=(reflection_model, real, imag, freq))
    
def transmission(freq, data_real, data_imag):
    '''
    Read the raw data and gives the initial guess for the fitting. 
    TODO: Have a better, more descriptive name for Q1, Q2
    Input:
    -----
    
        **data_real**
        (np.array), the real part of the data
        **data_imag**
        (np.array), the imag part of the data  
        
    Output:
    ------
    
         (`MinimizerResult <https://lmfit.github.io/lmfit-py/fitting.html#lmfit.minimizer.MinimizerResult>`_) see documentation for specifics 
         
    Raises:
    -------
    
        None
    '''
    mag = np.sqrt(data_real ** 2 + data_imag ** 2)
    data_phase = np.arctan2(data_imag, data_real)
    
    A = (data_phase[10] - data_phase[0]) / (freq[10] - freq[0]) / (2 * np.pi)
    B = -A*freq[0] + data_phase[0]
        
    f0 = freq[mag.tolist().index(max(mag))]
    mag_max = mag.max()
    left_bw = freq[np.where(mag > mag.max() / 2)[0][0]]
    right_bw = freq[np.where(mag > mag.max() / 2)[0][-1]]
    Q_tot = 2 * f0/(right_bw - left_bw)
    Q1 = 4 * Q_tot * (1 - np.sqrt(1 - mag_max**2)) / (2 * mag_max ** 2)
    Q2 = 4 * Q_tot * (1 + np.sqrt(1 - mag_max ** 2)) / (2 * mag_max ** 2)
    fit_params = lmf.Parameters()
    
    
    fit_params.add('f0', value = f0, vary=True)
    fit_params.add('Q1',value = Q1, min = 0.0,  vary = True)
    fit_params.add('Q2',value = Q2, min = 0.0,  vary = True)
    fit_params.add('A',value = A, min = -10, max = 10, vary = True)
    fit_params.add('B',value = B, min = 0.0, max = 2 * np.pi, vary = True)
    fit_params.add('C',value = 1., min = 0.0, max = 1, vary = True)
    
    
    out=lmf.minimize(_residuals, fit_params, args=(transmission_model, data_real, data_imag, freq))

    return out
    
def t1_model(params, f, do_float = True):
    value = params.valuesdict()
    A = value['A']
    Ao = value['Ao']
    t1 = value['t1']
#    for num in range(len(f)):
#        f[num] = -1*f[num] / float(t1)
    S_21 = (np.exp(-f/t1)) * A + Ao + 0 * 1j
    if not do_float:
        return S_21
    return S_21.view(np.float)
    
def t1(freq, data_real, data_imag):
    A = (data_real[0]) - (data_real[-1])
    Ao = (data_real[-1])
    t1 = (1/3)*(freq[ -1] - freq[0])
    fit_params = lmf.Parameters()
    fit_params.add('A', value = A, vary = True)
    fit_params.add('Ao', value = Ao, vary = True)
    fit_params.add('t1', value = t1, min = 0, vary = True)
    out = lmf.minimize(_residuals, fit_params, args = (t1_model, data_real, data_imag, freq))
    return out
    
    
    
    
def t2_model(params, t, do_float = True):
    value = params.valuesdict()
    A = value['A']
    f_max = value['f_max']
    B = value['B']
    T2 = value['T2']
    D = value['D']
    
    S_21= A*np.cos(f_max*np.pi*2*t+B)*np.exp(-t/T2)+D+0*1j
    if not do_float:
        return S_21
    return S_21.view(np.float)
    
    
    
def t2(freq, data_real, data_imag):
   
    
    A = (np.max(data_real)-np.min(data_real))/2.0
    T2 = (1/4.0)*(freq[-1]-freq[0])
    D = data_real[-1]
    
    fourier_transform=np.fft.fft(data_real)
    
    
    max_point = np.argmax(np.abs(fourier_transform[1: len(fourier_transform)/2]))
   
    time_spacing = freq[1]-freq[0]
    f_array = np.fft.fftfreq(len(fourier_transform), d=time_spacing)
    f_max = f_array[max_point]
    B = np.arctan2(np.imag(fourier_transform[max_point]), np.real(fourier_transform[max_point]))
    
 
   
    
    fit_params = lmf.Parameters()
    fit_params.add('A', value =A, vary=True)
    fit_params.add('D', value = D, vary= True)
    fit_params.add('T2', value = T2, min= 0 , vary= True)
    fit_params.add('B', value = B, min=0, max=2*np.pi, vary= True)
    fit_params.add('f_max', value = f_max, min = 0, vary =True)
    
    out = lmf.minimize(_residuals, fit_params, args =(t2_model, data_real, data_imag, freq))
    return out 

