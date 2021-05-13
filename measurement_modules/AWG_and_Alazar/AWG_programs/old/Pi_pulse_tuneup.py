# -*- coding: utf-8 -*-
"""
Created on Tue Jun 13 14:32:04 2017

@author: HatLab_Xi Cao
"""

# Pi pulse tune up v2
# Pi Pulse tune-up sequence

import numpy as np
from hatdrivers.AWG_utilities.pulse import Gaussian, Square, Marker
from hatdrivers.AWG_utilities.sequence import Sequence
from timeit import default_timer
from hatdrivers.AWG_utilities import AWGFile
#import sys
#sys.path.append(r'C:\qtlab-lite\\')
#import qt
from hatdrivers.AWG_utilities import AWGclean as clean


ge = True
clean.clean(AWG1)

### Define the file name and instrument
name = 'Pipulse_tuneup.awg'
filename = 'E:\Data\Cooldown_20210408\SNAIL_Amps\C1\AWG' + name
awgname = 'E:\Data\Cooldown_20210408\SNAIL_Amps\C1\AWG' + name
AWGInst = AWG1
###
#AWGInst.set_sequence_length(0)
#AWGInst.deleteall()
time1 = default_timer()


if ge:
    ### Parameters of Gaussian wave
    sigma = 25 #25#40#20
    gaussian_width = 6*sigma
    gaussian_num = 81 #161 
    amp = np.linspace(-8000, 8000, gaussian_num)
    amp = amp.tolist()
    amp.append(0)
    ###
else:
    sigma = 30
    gaussian_width = 6*sigma
    gaussian_num = 81 #161  #81 #
    amp = np.linspace(-4000, 4000, gaussian_num)
    amp = amp.tolist()
    amp.append(0)
    ###

### Parameters of Square wave
#square_width = 2000 #1500#1200 #3000 #1500 DOUBLED 06/29/2020 MMM
#square_height = 600#800#600#6250



square_width = 500 #800#2000 #900 #900 #2500 #1500 #500#1500
square_height = 2000#800 #800

###

### Parameters of Markers
marker1_delay = 10
marker1_width = gaussian_width + 2*marker1_delay
marker1_on = 5
marker1_off = marker1_width -5

marker2_delay = 10
marker2_width = square_width + 2*marker2_delay #+100
marker2_on = 5
marker2_off = marker2_width - 5

alazar_marker_width = 100
alazar_marker_on = 5
alazar_marker_off = 95
###

### Pulse init 

# Parameters
#ssb_freq = -0.1
#iqscale = 1.0/0.847
#phase = 0
#skewphase = (-4.812)*0.1*2*np.pi

if ge:
    ssb_freq = 0.08 #0.08#0.0#0.1
    iqscale = 1.04# 1.005#1.063#1.050#1
    phase = 0
    skewphase = (0.520)*ssb_freq*2*np.pi

else:
    ssb_freq = 0.123 #0.1
    iqscale = 0.98
    phase = 0
    skewphase = (2.235)*0.123*2*np.pi#(4.862)*0.1*2*np.pi#(0.248)*0.1*2*np.pi #(4.521)*0.1*2*np.pi
    #

###############################################################################

# This following block is to create all the pulses that we are going to use 
# in the measurement.
# Note that two pulse with same pulse type but different pulse parameters should 
# be considered as differet pulses. (e.g Two Gaussian with different amp is two pulses)
pulsenum = 6 + gaussian_num + 1
pulse = np.empty(pulsenum, dtype = object)
i = 0
pulse[i] = Square(i, square_width, 0, 1, 0, square_height)
pulse[i].data_generator()    
i = i + 1
pulse[i] = Marker(i, marker1_width, 1, marker1_on, marker1_off)
pulse[i].data_generator() 
i = i + 1
pulse[i] = Marker(i, marker2_width, 5, marker2_on, marker2_off)
pulse[i].data_generator() 
i = i + 1
pulse[i] = Marker(i, alazar_marker_width, 6, alazar_marker_on, alazar_marker_off)
pulse[i].data_generator() 
i = i + 1
pulse[i] = Marker(i, marker1_width, 2, marker1_on, marker1_off)
pulse[i].data_generator() 
i = i + 1

#TWPA
pulse[i] = Marker(i, marker2_width, 7, marker2_on, marker2_off)
pulse[i].data_generator()
i = i + 1

while i < pulsenum:
    print(i-6)
    pulse[i] = Gaussian(i, gaussian_width, ssb_freq, iqscale, phase, sigma, amp[i-6], skew_phase = skewphase)
    pulse[i].data_generator()
    i = i + 1


###############################################################################


###############################################################################
### Parameters for the sequence
start = 0
wait_time = 150# 200#5#1000
###


### Sequence 
shotsnum = gaussian_num # This is how many shots we will do in this experiment, i.e how many wait trigger
shotsnum = shotsnum + 1 # TODO: there is something wrong with the code, the shots number always have one shift...
totwavenum = 7*shotsnum # This is how many waves are going to be used in the whole sequence
sequence = Sequence(shotsnum, totwavenum, pulse)

# The following while loop is where you create you sequence. 
# Tell the sequence where you want a certain pulse to start at which channel

i = 0
while i < shotsnum:
    sequence.get_block(pulse[4].name, start, channel = 1, wait_trigger = True)
    sequence.get_block(pulse[1].name, start, channel = 1)
    start = start + marker1_delay
    sequence.get_block(pulse[i+6].name, start, channel = 1)
    start = start + pulse[i+6].width + wait_time*1

    sequence.get_block(pulse[2].name, start - marker2_delay, channel = 3)
    sequence.get_block(pulse[3].name, start - marker2_delay, channel = 3)
#    sequence.get_block(pulse[5].name, start - marker2_delay, channel = 3)
    sequence.get_block(pulse[0].name, start, channel = 3)
    start = start + pulse[0].width + marker2_delay
    
    i = i+1
###

### Call difference method from Sequence to do the calculation to find where to put the waveforms
i = 0 
while i < shotsnum-1:
    sequence.sequence_block[i].make_block()
    i = i + 1
#    print 'Hello'
#    print i
    

AWG = AWGFile.AWGFile(filename)
sequence.sequence_upload(AWG)
###

AWGInst.restore(awgname)
print('Confucius says it takes the following seconds to finish the code')
print(default_timer() - time1)

AWGInst.channel_on(1)
AWGInst.channel_on(2)
AWGInst.channel_on(3)
AWGInst.channel_on(4)

change_setting = True
if change_setting:
    # Set the DC offset
    if ge:
    # Set the DC offset
        ch1_offset = 1.387#0.141#-0.021#-0.015#0.006#-0.019# -0.01#-0.045#-0.183
        ch2_offset = 1.017#-0.196#-0.032#-0.023#-0.013#-0.050#0.008#-0.147#-0.148
        ch3_offset = -0.016#-0.046
        ch4_offset = 0.008#0.010
        
        ch1_amp = 1.0#0.5#2.5#1.5
        ch2_amp = 1.0#0.5#2.5#1.5
        ch3_amp = 1.0
        ch4_amp = 1.0

    else:
        ch1_offset = 0.748#-0.045#-0.183
        ch2_offset = 0.652#-0.147#-0.148
        ch3_offset = -0.04
        ch4_offset = 0.015
    
    # Set the channel voltage
        ch1_amp = 2.5
        ch2_amp = 2.5
        ch3_amp = 3.0
        ch4_amp = 3.0    
    
    AWGInst.ch1offset(ch1_offset)
    AWGInst.ch2offset(ch2_offset)
    AWGInst.ch3offset(ch3_offset)
    AWGInst.ch4offset(ch4_offset)
    

    AWGInst.ch1amp(ch1_amp)
    AWGInst.ch2amp(ch2_amp)
    AWGInst.ch3amp(ch3_amp)
    AWGInst.ch4amp(ch4_amp)


AWGInst.run()