from bluesky.plan_stubs import abs_set, sleep, mv, mvr
import time

from BMM.modes import MODEDATA

from IPython import get_ipython
user_ns = get_ipython().user_ns


TUNE_STEP = 0.004
def tune_plan(step=0):
    '''
    Tune 2nd crystal pitch from a plan.  Argument is a value for the step, so a relative motion.
    '''
    yield from abs_set(dcm_pitch.kill_cmd, 1, wait=True)
    yield from mvr(dcm_pitch, step)
    yield from sleep(1.0)
    yield from abs_set(dcm_pitch.kill_cmd, 1, wait=True)
def tune_up():
    yield from tune_plan(step=TUNE_STEP)
def tune_down():
    yield from tune_plan(step=-1*TUNE_STEP)

def tune(step=0):
    '''
    Tune 2nd crystal pitch from the command line.  Argument is a value for the step, so a relative motion.
    '''
    dcm_pitch = user_ns['dcm_pitch']
    dcm_pitch.kill_cmd.put(1)
    dcm_pitch.user_setpoint.put(dcm_pitch.user_readback.get() + step)
    time.sleep(2.0)
    dcm_pitch.kill_cmd.put(1)
def tu():
    tune(step=TUNE_STEP)
def td():
    tune(step=-1*TUNE_STEP)

def tweak_bct(step):
    dm3_bct = user_ns['dm3_bct']
    if step is None:
        step = 0
    yield from abs_set(dm3_bct.kill_cmd,1, wait=True)
    print('Moving from %.4f to %.4f' % (dm3_bct.user_readback.get(), dm3_bct.user_readback.get() + step))
    yield from mvr(dm3_bct, step)
    time.sleep(3.0)
    yield from abs_set(dm3_bct.kill_cmd,1, wait=True)



def kmv(*args):
    for m in args[0::2]:
        if 'Vacuum' in str(type(m)):
            yield from abs_set(m.kill_cmd, 1, wait=True)
    yield from mv(*args)

def kmvr(*args):
    for m in args[0::2]:
        if 'Vacuum' in str(type(m)):
            yield from abs_set(m.kill_cmd, 1, wait=True)
    yield from mvr(*args)


def set_integration_time(time=0.5):
    '''
    set integration times for electrometers and Struck from the command line
    '''
    user_ns['vor'].auto_count_time.value = time
    user_ns['quadem1'].averaging_time.value = time
    user_ns['dualio'].averaging_time.value = time

def set_integration_plan(time=0.5):
    '''
    set integration times for electrometers and Struck from a plan
    '''
    yield from abs_set(user_ns['vor'].auto_count_time, time, wait=True)
    yield from abs_set(user_ns['quadem1'].averaging_time, time, wait=True)
    yield from abs_set(user_ns['dualio'].averaging_time, time, wait=True)



def recover_screens():
    dm2_fs  = user_ns['dm2_fs']
    dm3_fs  = user_ns['dm3_fs']
    dm3_bct = user_ns['dm3_bct']
    yield from abs_set(dm2_fs.home_signal,  1)
    yield from abs_set(dm3_fs.home_signal,  1)
    yield from abs_set(dm3_bct.home_signal, 1)
    yield from sleep(1.0)
    print('Begin homing dm2_fs, dm3_fs, and dm3_bct:\n')
    hvalues = (dm2_fs.hocpl.get(), dm3_fs.hocpl.get(), dm3_bct.hocpl.get())
    while any(v == 0 for v in hvalues):
        hvalues = (dm2_fs.hocpl.get(), dm3_fs.hocpl.get(), dm3_bct.hocpl.get())
        strings = ['dm2_fs', 'dm3_fs', 'dm3_bct']
        for i,v in enumerate(hvalues):
            strings[i] = go_msg(strings[i]) if hvalues[i] == 1 else error_msg(strings[i])
        print('  '.join(strings), end='\r')
        yield from sleep(1.0)
    print('\n')
    yield from abs_set(dm3_bct.kill_cmd, 1, wait=True)
    yield from mv(dm2_fs, 67, dm3_fs, 55, dm3_bct, 43.6565) # MODEDATA['dm3_bct']['E'])

    
def recover_mirror2():
    m2_xu, m2_xd, m2_yu, m2_ydo, m2_ydi = user_ns['m2_xu'], user_ns['m2_xd'], user_ns['m2_yu'], user_ns['m2_ydo'], user_ns['m2_ydi']
    yield from abs_set(m2_xu.home_signal,  1) # xu and xd home together
    yield from abs_set(m2_yu.home_signal,  1) # yu, ydi, and ydo home together
    yield from sleep(1.0)
    print('Begin homing lateral and vertical motors in M2:\n')
    hvalues = (m2_yu.hocpl.get(), m2_ydo.hocpl.get(), m2_ydi.hocpl.get(), m2_xu.hocpl.get(), m2_xd.hocpl.get())
    while any(v == 0 for v in hvalues):
        hvalues = (m2_yu.hocpl.get(), m2_ydo.hocpl.get(), m2_ydi.hocpl.get(), m2_xu.hocpl.get(), m2_xd.hocpl.get())
        strings = ['m2_yu', 'm2_ydo', 'm2_ydi', 'm2_xu', 'm2_xd',]
        for i,v in enumerate(hvalues):
            strings[i] = go_msg(strings[i]) if hvalues[i] == 1 else error_msg(strings[i])
        print('  '.join(strings), end='\r')
        yield from sleep(1.0)
    print('\n')
    yield from mv(m2_yu,  MODEDATA['m2_yu']['E'],
                  m2_ydo, MODEDATA['m2_ydo']['E'],
                  m2_ydi, MODEDATA['m2_ydi']['E'],
                  m2_xu,  MODEDATA['m2_xu']['E'],
                  m2_xd,  MODEDATA['m2_xd']['E'])


def recover_mirrors():
    m2_xu, m2_xd, m2_yu, m2_ydo, m2_ydi = user_ns['m2_xu'], user_ns['m2_xd'], user_ns['m2_yu'], user_ns['m2_ydo'], user_ns['m2_ydi']
    m3_xu, m3_xd, m3_yu, m3_ydo, m3_ydi = user_ns['m3_xu'], user_ns['m3_xd'], user_ns['m3_yu'], user_ns['m3_ydo'], user_ns['m3_ydi']
    yield from abs_set(m2_yu.home_signal,  1)
    yield from abs_set(m2_xu.home_signal,  1)
    yield from abs_set(m3_yu.home_signal,  1)
    yield from abs_set(m3_xu.home_signal,  1)
    yield from sleep(1.0)
    print('Begin homing lateral and vertical motors in M2 and M3:\n')
    hvalues = (m2_yu.hocpl.get(), m2_ydo.hocpl.get(), m2_ydi.hocpl.get(), m2_xu.hocpl.get(), m2_xd.hocpl.get(),
               m3_yu.hocpl.get(), m3_ydo.hocpl.get(), m3_ydi.hocpl.get(), m3_xu.hocpl.get(), m3_xd.hocpl.get())
    while any(v == 0 for v in hvalues):
        hvalues = (m2_yu.hocpl.get(), m2_ydo.hocpl.get(), m2_ydi.hocpl.get(), m2_xu.hocpl.get(), m2_xd.hocpl.get(),
                   m3_yu.hocpl.get(), m3_ydo.hocpl.get(), m3_ydi.hocpl.get(), m3_xu.hocpl.get(), m3_xd.hocpl.get())
        strings = ['m2_yu', 'm2_ydo', 'm2_ydi', 'm2_xu', 'm2_xd', 'm3_yu', 'm3_ydo', 'm3_ydi', 'm3_xu', 'm3_xd',]
        for i,v in enumerate(hvalues):
            strings[i] = go_msg(strings[i]) if hvalues[i] == 1 else error_msg(strings[i])
        print('  '.join(strings), end='\r')
        yield from sleep(1.0)
    print('\n')
    yield from mv(m2_yu,  MODEDATA['m2_yu']['E'],
                  m2_ydo, MODEDATA['m2_ydo']['E'],
                  m2_ydi, MODEDATA['m2_ydi']['E'],
                  m2_xu,  MODEDATA['m2_xu']['E'],
                  m2_xd,  MODEDATA['m2_xd']['E'],
                  m3_yu,  MODEDATA['m3_yu']['E'],
                  m3_ydo, MODEDATA['m3_ydo']['E'],
                  m3_ydi, MODEDATA['m3_ydi']['E'],
                  m3_xu,  MODEDATA['m3_xu']['E'],
                  m3_xd,  MODEDATA['m3_xd']['E'])





def mvbct(target=None):
    '''
    A workaround to kill the BCT motor, then do an absolute movement
    '''
    dm3_bct = user_ns['dm3_bct']
    if target is None:
        target = dm3_bct.user_readback.get()
    yield from abs_set(dm3_bct.kill_cmd, 1, wait=True)
    yield from mv(dm3_bct, target)

def mvrbct(target=None):
    '''
    A workaround to kill the BCT motor, then do a relative movement
    '''
    dm3_bct = user_ns['dm3_bct']
    if target is None:
        target = 0
    yield from abs_set(dm3_bct.kill_cmd, 1, wait=True)
    yield from mvr(dm3_bct, target)


def mvbender(target=None):
    '''
    A workaround to kill the M2 bender motor, then do an absolute movement
    '''
    m2_bender = user_ns['m2_bender']
    if target is None:
        target = m2_bender.user_readback.get()
    yield from abs_set(m2_bender.kill_cmd, 1, wait=True)
    yield from mv(m2_bender, target)

def mvrbender(target=None):
    '''
    A workaround to kill the M2 bender motor, then do a relative movement
    '''
    m2_bender = user_ns['m2_bender']
    if target is None:
        target = 0
    yield from abs_set(m2_bender.kill_cmd, 1, wait=True)
    yield from mvr(m2_bender, target)
    
