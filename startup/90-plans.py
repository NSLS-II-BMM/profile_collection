import bluesky as bs
import bluesky.plans as bp
#import time as ttime
#from subprocess import call
#import os
#import signal


ionchambers = [quadem1.current1_mean_value_nano, quadem1.current2_mean_value_nano, quadem1.current3_mean_value_nano]
vortex_ch1  = [vortex_me4.channels.chan3, vortex_me4.channels.chan7,  vortex_me4.channels.chan11]
vortex_ch2  = [vortex_me4.channels.chan4, vortex_me4.channels.chan8,  vortex_me4.channels.chan12]
vortex_ch3  = [vortex_me4.channels.chan5, vortex_me4.channels.chan9,  vortex_me4.channels.chan13]
vortex_ch4  = [vortex_me4.channels.chan6, vortex_me4.channels.chan10, vortex_me4.channels.chan14]
vortex      = vortex_ch1 + vortex_ch2 + vortex_ch3 + vortex_ch4

transmission = ionchambers
fluorescence = ionchambers + vortex

        

def tune(step=0.004):
    '''
    Tune 2nd crystal pitch from the command line.  Argument is a value for the step, so a realtive motion.
    '''
    dcm_pitch.kill_cmd.value = 1
    dcm_pitch.user_setpoint.value = dcm_pitch.user_readback.value + step
    

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
    '''
    set integration times for electrometer and Struck from the command line
    '''
    vortex_me4.auto_count_time.value = time
    quadem1.averaging_time.value = time

def set_integration_plan(time=0.5):
    '''
    set integration times for electrometer and Struck from a plan
    '''
    yield from abs_set(vortex_me4.auto_count_time, time)
    yield from abs_set(quadem1.averaging_time, time)
    

