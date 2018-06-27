from bluesky.suspenders import SuspendFloor, SuspendBoolHigh, SuspendBoolLow

RE.clear_suspenders()
## ----------------------------------------------------------------------------------
## suspend when I0 drops below 0.1 nA (not in use)
suspender_I0 = SuspendFloor(quadem1.I0, 0.1, resume_thresh=1, sleep=5)
#RE.install_suspender(suspender_I0)

## ----------------------------------------------------------------------------------
## suspend upon beam dump, resume at 90% operating current
OPERATING_CURRENT = 375
suspender_ring_current = SuspendFloor(ring.current, 10, resume_thresh=0.9 * OPERATING_CURRENT, sleep=5)
RE.install_suspender(suspender_ring_current)

## ----------------------------------------------------------------------------------
## suspend if the BM photon shutter closes, resume 5 seconds after opening
suspender_bmps = SuspendBoolLow(bmps.state, sleep=5)
RE.install_suspender(suspender_bmps)

## ----------------------------------------------------------------------------------
## suspend if the main photon shutter closes, resume 5 seconds after opening
suspender_sha = SuspendBoolLow(idps.state, sleep=5)
RE.install_suspender(suspender_sha)

## ----------------------------------------------------------------------------------
## suspend if the experimental photon shutter closes, resume 5 seconds after opening
suspender_shb = SuspendBoolHigh(shb.state, sleep=5)
RE.install_suspender(suspender_shb)

def BMM_suspenders():
    for s in (suspender_ring_current, suspender_bmps, suspender_sha, suspender_shb):
        RE.install_suspender(s)
