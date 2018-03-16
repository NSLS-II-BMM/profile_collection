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
        yield from abs_set(shutter_fe.opn, 1)
    elif shutter is 'b':
        yield from abs_set(shutter_ph.opn, 1)
    elif shutter is 'fs':
        yield from abs_set(fs1.opn, 1)
    else:
        pass
    yield from null()
        
def shcl(shutter):
    if shutter is 'a':
        yield from abs_set(shutter_fe.cls, 1)
    elif shutter is 'b':
        yield from abs_set(shutter_ph.cls, 1)
    elif shutter is 'fs':
        yield from abs_set(fs1.cls, 1)
    else:
        pass
    yield from null()
        

def tune(step=0.004):
    abs_set(dcm_pitch.kill_cmd, 1)
    mvr(dcm_pitch, step)
    

def kmv(*args):
    for m in args[0::2]:
        if 'Vacuum' in str(type(m)):
            yield from abs_set(m.kill_cmd, 1)
    yield from mv(*args)
    
def kmvr(*args):
    for m in args[0::2]:
        if 'Vacuum' in str(type(m)):
            yield from abs_set(m.kill_cmd, 1)
    yield from mvr(*args)


def set_integration_time(time=0.5):
    yield from abs_set(scalar1.auto_count_time, time)
    yield from abs_set(quadem1.averaging_time, time)
    

