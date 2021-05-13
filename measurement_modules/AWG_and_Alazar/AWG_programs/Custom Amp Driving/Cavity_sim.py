# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 09:16:02 2021

@author: Hatlab_3
"""

import broadbean as bb
from broadbean.plotting import plotter
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['figure.figsize'] = (8, 3)
mpl.rcParams['figure.subplot.bottom'] = 0.15 

#%%
#practicing on a gaussian pulse, this is how you can use broadbean's primitives
g = bb.broadbean.PulseAtoms.gaussian(1, 10e-9, 0, 0, 1e9, 200)
s = bb.broadbean.PulseAtoms.sine(50e6, 1, 0, np.pi/2, 1e9, 100*2)
t = np.linspace(0, 200/1e9, 200)
plt.plot(t, g*s) #a guassian pulse at 50MHz!
#make the custom function #first t
def gaussian_pulse(freq, phase, ampl, sigma, mu, offset, SR, npts):
    g = bb.broadbean.PulseAtoms.gaussian(ampl, sigma, mu, offset, SR, npts)
    s = bb.broadbean.PulseAtoms.sine(freq, ampl, offset, phase, SR, npts)
    return g*s

#%%
#now you can insert this into a blueprint 
#question: what if I want a custom function? -> probably make it according to PulseAtoms framework
sine = bb.PulseAtoms.sine  # args: freq, ampl, off, phase
bp1 = bb.BluePrint()
bp1.setSR(1e9)
# bp1.insertSegment(1, gaussian_pulse, (50e6,np.pi/2,1,10e-9,0,0), name = 'mypulse', dur = 100e-9)
bp1.insertSegment(1, sine, (50e6, 1e-3, 1e-3, 0), name='mysine', dur=500e-9)
bp1.showPrint()
plotter(bp1)

