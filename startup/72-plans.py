import bluesky as bs
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import time
#from subprocess import call
#import os
#import signal




TUNE_STEP = 0.004
def tune_plan(step=0):
    '''
    Tune 2nd crystal pitch from a plan.  Argument is a value for the step, so a realtive motion.
    '''
    yield from abs_set(dcm_pitch.kill_cmd, 1)
    yield from mvr(dcm_pitch, step)
    yield from bps.sleep(1.0)
    yield from abs_set(dcm_pitch.kill_cmd, 1)
def tune_up():
    yield from tune_plan(step=TUNE_STEP)
def tune_down():
    yield from tune_plan(step=-1*TUNE_STEP)

def tune(step=0):
    '''
    Tune 2nd crystal pitch from the command line.  Argument is a value for the step, so a realtive motion.
    '''
    dcm_pitch.kill_cmd.put(1)
    dcm_pitch.user_setpoint.put(dcm_pitch.user_readback.value + step)
    time.sleep(2.0)
    dcm_pitch.kill_cmd.put(1)
def tu():
    tune(step=TUNE_STEP)
def td():
    tune(step=-1*TUNE_STEP)

def tweak_bct(step):
    if step is None:
        step = 0
    dm3_bct.kill_cmd.put(1)
    print(dm3_bct.user_readback.value, step, dm3_bct.user_readback.value + step)
    dm3_bct.user_setpoint.put(dm3_bct.user_readback.value + step)
    time.sleep(3.0)
    dm3_bct.kill_cmd.put(1)



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
    vor.auto_count_time.value = time
    quadem1.averaging_time.value = time

def set_integration_plan(time=0.5):
    '''
    set integration times for electrometer and Struck from a plan
    '''
    yield from abs_set(vor.auto_count_time, time)
    yield from abs_set(quadem1.averaging_time, time)
