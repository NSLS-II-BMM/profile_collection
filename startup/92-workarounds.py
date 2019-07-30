
run_report(__file__)


def mvbct(target=None):
    '''
    A workaround to kill the BCT motor, then do an absolute movement
    '''
    if target is None:
        target = dm3_bct.user_readback.value
    yield from abs_set(dm3_bct.kill_cmd, 1, wait=True)
    yield from mv(dm3_bct, target)

def mvrbct(target=None):
    '''
    A workaround to kill the BCT motor, then do a relative movement
    '''
    if target is None:
        target = 0
    yield from abs_set(dm3_bct.kill_cmd, 1, wait=True)
    yield from mvr(dm3_bct, target)


def mvbender(target=None):
    '''
    A workaround to kill the M2 bender motor, then do an absolute movement
    '''
    if target is None:
        target = dm3_bct.user_readback.value
    yield from abs_set(m2_bender.kill_cmd, 1, wait=True)
    yield from mv(m2_bender, target)

def mvrbender(target=None):
    '''
    A workaround to kill the M2 bender motor, then do a relative movement
    '''
    if target is None:
        target = 0
    yield from abs_set(m2_bender.kill_cmd, 1, wait=True)
    yield from mvr(m2_bender, target)
    
