
run_report(__file__)


def mvbct(target=None):
    '''
    A workaround to kill the BCT motor, then do an absolute movement
    '''
    if target is None:
        target = dm3_bct.user_readback.value
    yield from abs_set(dm3_bct.kill_cmd, 1)
    yield from mv(dm3_bct, target)

def mvrbct(target=None):
    '''
    A workaround to kill the BCT motor, then do a relative movement
    '''
    if target is None:
        target = 0
    yield from abs_set(dm3_bct.kill_cmd, 1)
    yield from mvr(dm3_bct, target)
