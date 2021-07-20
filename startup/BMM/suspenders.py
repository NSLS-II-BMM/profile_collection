from bluesky.suspenders import SuspendFloor, SuspendBoolHigh, SuspendBoolLow
from IPython import get_ipython
from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)


#RE.clear_suspenders()
all_BMM_suspenders = list()

## ----------------------------------------------------------------------------------
## suspend when I0 drops below 0.1 nA (not in use)
suspender_I0 = SuspendFloor(user_ns['quadem1'].I0, 0.1, resume_thresh=1, sleep=5)
#all_BMM_suspenders.append(suspender_I0)

## ----------------------------------------------------------------------------------
## suspend upon beam dump, resume 30 seconds after hitting 90% of fill target
try:
    if user_ns['ring'].filltarget.get() > 20:
        suspender_ring_current = SuspendFloor(user_ns['ring'].current, 10, resume_thresh=0.9 * user_ns['ring'].filltarget.get(), sleep=60)
        all_BMM_suspenders.append(suspender_ring_current)
except Exception as e:
    print(f'failed to create ring current suspender: {e}')
    pass

## ----------------------------------------------------------------------------------
## suspend if the BM photon shutter closes, resume 5 seconds after opening
try:
    suspender_bmps = SuspendBoolLow(user_ns['bmps'].state, sleep=60)
    all_BMM_suspenders.append(suspender_bmps)
except Exception as e:
    print(f'failed to create bpms suspender: {e}')
    pass

    
## ----------------------------------------------------------------------------------
## suspend if the main photon shutter closes, resume 5 seconds after opening
try:
    suspender_sha = SuspendBoolLow(user_ns['idps'].state, sleep=60)
    all_BMM_suspenders.append(suspender_sha)
except Exception as e:
    print(f'failed to create sha suspender: {e}')
    pass

## ----------------------------------------------------------------------------------
## suspend if the experimental photon shutter closes, resume 5 seconds after opening
from bluesky.plan_stubs import null
from BMM.logging import post_to_slack
def tell_slack_shb_closed():
    print('triggering closed message')
    post_to_slack('B shutter closed')
    return(yield from null())
def tell_slack_shb_opened():
    print('triggering opened message')
    post_to_slack('B shutter opened')
    return(yield from null())
try:
    suspender_shb = SuspendBoolHigh(user_ns['shb'].state, sleep=5,
                                    pre_plan=tell_slack_shb_closed(),
                                    post_plan=tell_slack_shb_opened())
    all_BMM_suspenders.append(suspender_shb)
except Exception as e:
    print(f'failed to create shb suspender: {e}')
    pass

    
def BMM_suspenders():
    BMMuser = user_ns['BMMuser']
    if BMMuser.suspenders_engaged:
        return
    for s in all_BMM_suspenders:
        user_ns['RE'].install_suspender(s)
    BMMuser.suspenders_engaged = True

def BMM_clear_suspenders():
    RE = user_ns['RE']
    BMMuser = user_ns['BMMuser']
    if BMMuser.running_macro is False:
        RE.clear_suspenders()
        BMMuser.suspenders_engaged = False
    

def BMM_clear_to_start():
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
