import bluesky as bs
import bluesky.plans as bp
#import time as ttime
#from subprocess import call
#import os
#import signal


ionchambers = [quadem1.current1_mean_value_nano, quadem1.current2_mean_value_nano, quadem1.current3_mean_value_nano]
vortex_ch1  = [scaler1.channels.chan2, scaler1.channels.chan10, scaler1.channels.chan18]
vortex_ch2  = [scaler1.channels.chan4, scaler1.channels.chan12, scaler1.channels.chan20]
vortex_ch3  = [scaler1.channels.chan6, scaler1.channels.chan14, scaler1.channels.chan22]
vortex_ch4  = [scaler1.channels.chan8, scaler1.channels.chan16, scaler1.channels.chan24]
vortex      = vortex_ch1 + vortex_ch2 + vortex_ch3 + vortex_ch4

transmission = ionchambers
fluorescence = ionchambers + vortex

def shop(shutter):
    if shutter is 'a':
        shutter_fe.opn.value = 1
    elif shutter is 'b':
        shutter_ph.opn.value = 1
    elif shutter is 'fs':
        fs1.opn.value = 1
    else:
        pass
    yield from null()
        
def shcl(shutter):
    if shutter is 'a':
        shutter_fe.cls.value = 1
    elif shutter is 'b':
        shutter_ph.cls.value = 1
    elif shutter is 'fs':
        fs1.cls.value = 1
    else:
        pass
    yield from null()
        
