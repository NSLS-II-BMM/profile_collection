from bluesky.suspenders import SuspendFloor, SuspendBoolHigh, SuspendBoolLow

from bluesky_queueserver.manager.profile_tools import set_user_ns

# from IPython import get_ipython
# user_ns = get_ipython().user_ns


#RE.clear_suspenders()
all_BMM_suspenders = list()

## ----------------------------------------------------------------------------------
## suspend when I0 drops below 0.1 nA (not in use)

@set_user_ns
def get_suspender_I0(user_ns):
    return SuspendFloor(user_ns['quadem1'].I0, 0.1, resume_thresh=1, sleep=5)
suspender_I0 = get_suspender_I0()

#all_BMM_suspenders.append(suspender_I0)

## ----------------------------------------------------------------------------------
## suspend upon beam dump, resume 30 seconds after hitting 90% of fill target

@set_user_ns
def add_suspender_ring_current(user_ns):
    try:
        if user_ns['ring'].filltarget.get() > 20:
            suspender_ring_current = SuspendFloor(user_ns['ring'].current, 10,
                                                  resume_thresh=0.9 * user_ns['ring'].filltarget.get(),
                                                  sleep=60)
            all_BMM_suspenders.append(suspender_ring_current)
    except:
        pass

add_suspender_ring_current()

## ----------------------------------------------------------------------------------
## suspend if the BM photon shutter closes, resume 5 seconds after opening
@set_user_ns
def add_suspender_bmps(user_ns):
    try:
        suspender_bmps = SuspendBoolLow(user_ns['bmps'].state, sleep=60)
        all_BMM_suspenders.append(suspender_bmps)
    except:
        pass

add_suspender_bmps()

## ----------------------------------------------------------------------------------
## suspend if the main photon shutter closes, resume 5 seconds after opening
@set_user_ns
def add_suspender_sha(user_ns):
    try:
        suspender_sha = SuspendBoolLow(user_ns['idps'].state, sleep=60)
        all_BMM_suspenders.append(suspender_sha)
    except:
        pass

add_suspender_sha()

## ----------------------------------------------------------------------------------
## suspend if the experimental photon shutter closes, resume 5 seconds after opening
@set_user_ns
def add_suspender_shb(user_ns):
    try:
        suspender_shb = SuspendBoolHigh(user_ns['shb'].state, sleep=5)
        all_BMM_suspenders.append(suspender_shb)
    except:
        pass

add_suspender_shb()

@set_user_ns
def BMM_suspenders(user_ns):
    for s in all_BMM_suspenders:
        user_ns['RE'].install_suspender(s)

@set_user_ns
def BMM_clear_to_start(user_ns):
    ok = True
    text = ''
    # return (ok, text)
    if user_ns['ring'].current.get() < 10:
        ok = False
        text += 'There is no current in the storage ring. Solution: wait for beam to come back\n'
    if user_ns['bmps'].state.get() == 0:
        ok = False
        text += 'BMPS is closed. Solution: call floor coordinator\n'
    if user_ns['idps'].state.get() == 0:
        ok = False
        text += 'Front end shutter (sha) is closed. Solution: do sha.open()\n'
    if user_ns['shb'].state.get() == 1:
        ok = False
        text += 'Photon shutter (shb) is closed. Solution: search the hutch then do shb.open()\n'
    # if quadem1.I0.get() < 0.1:
    #     ok = 0
    #     text += 'There is no signal on I0\n'
    return (ok, text)
