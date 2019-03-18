from bluesky.suspenders import SuspendFloor, SuspendBoolHigh, SuspendBoolLow

run_report(__file__)

RE.clear_suspenders()
all_BMM_suspenders = list()

## ----------------------------------------------------------------------------------
## suspend when I0 drops below 0.1 nA (not in use)
suspender_I0 = SuspendFloor(quadem1.I0, 0.1, resume_thresh=1, sleep=5)
#all_BMM_suspenders.append(suspender_I0)

## ----------------------------------------------------------------------------------
## suspend upon beam dump, resume 30 seconds after hitting 90% of fill target
try:
    if ring.filltarget.value > 20:
        suspender_ring_current = SuspendFloor(ring.current, 10, resume_thresh=0.9 * ring.filltarget.value, sleep=60)
        all_BMM_suspenders.append(suspender_ring_current)
except:
    pass

## ----------------------------------------------------------------------------------
## suspend if the BM photon shutter closes, resume 5 seconds after opening
try:
    suspender_bmps = SuspendBoolLow(bmps.state, sleep=60)
    all_BMM_suspenders.append(suspender_bmps)
except:
    pass

    
## ----------------------------------------------------------------------------------
## suspend if the main photon shutter closes, resume 5 seconds after opening
try:
    suspender_sha = SuspendBoolLow(idps.state, sleep=60)
    all_BMM_suspenders.append(suspender_sha)
except:
    pass

## ----------------------------------------------------------------------------------
## suspend if the experimental photon shutter closes, resume 5 seconds after opening
try:
    suspender_shb = SuspendBoolHigh(shb.state, sleep=5)
    all_BMM_suspenders.append(suspender_shb)
except:
    pass

    
def BMM_suspenders():
    for s in all_BMM_suspenders:
        RE.install_suspender(s)

def BMM_clear_to_start():
    ok = True
    text = ''
    # return (ok, text)
    if ring.current.value < 10:
        ok = False
        text += 'There is no current in the storage ring. Solution: wait for beam to come back\n'
    if bmps.state.value == 0:
        ok = False
        text += 'BMPS is closed. Solution: call floor coordinator\n'
    if idps.state.value == 0:
        ok = False
        text += 'Front end shutter (sha) is closed. Solution: do sha.open()\n'
    if shb.state.value == 1:
        ok = False
        text += 'Photon shutter (shb) is closed. Solution: search the hutch then do shb.open()\n'
    # if quadem1.I0.value < 0.1:
    #     ok = 0
    #     text += 'There is no signal on I0\n'
    return (ok, text)
