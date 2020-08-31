
from bluesky.plan_stubs import abs_set


from IPython import get_ipython
user_ns = get_ipython().user_ns

from BMM.logging import BMM_msg_hook

def resting_state():
    '''
    Command line tool to bring controls into their resting state:

    - quadEM and Struck scaler enabled and measuring
    - dwell time set to 1/2 second
    - electron yield channel (quadEM channel 4) hinted as 'omitted'
    - user prompt set to True. macro dry-run set to False, RE.msg_hook set to BMM_msg_hook
    '''
    user_ns['BMMuser'].prompt = True
    user_ns['BMMuser'].macro_dryrun = False
    user_ns['BMMuser'].wheel = False
    user_ns['quadem1'].on()
    user_ns['vor'].on()
    user_ns['_locked_dwell_time'].move(0.3)
    user_ns['_locked_dwell_time'].move(0.5)
    user_ns['quadem1'].Iy.kind = 'omitted'
    user_ns['dcm'].kill()
    #user_ns['RE'].msg_hook = BMM_msg_hook

def resting_state_plan():
    '''
    Plan for bringing controls into their resting state:

    - dwell time set to 1/2 second
    - electron yield channel (quadEM channel 4) hinted as 'omitted'
    - RE.msg_hook set to BMM_msg_hook
    '''
    #user_ns['BMMuser'].prompt = True
    user_ns['BMMuser'].macro_dryrun = False
    #yield from user_ns['quadem1'].on_plan()
    #yield from user_ns['vor'].on_plan()
    user_ns['quadem1'].Iy.kind = 'omitted'
    #user_ns['BMMuser'].wheel = False
    yield from abs_set(user_ns['_locked_dwell_time'], 0.5, wait=True)
    user_ns['dcm'].kill()
    #user_ns['RE'].msg_hook = BMM_msg_hook

def end_of_macro():
    '''Plan for bringing controls into their resting state at the end of
    a macro or when a macro is stopped/aborted:

    - quadEM and Struck scaler enabled and measuring
    - dwell time set to 1/2 second
    - electron yield channel (quadEM channel 4) hinted as 'omitted'
    - user prompt set to True. macro dry-run set to False, RE.msg_hook set to BMM_msg_hook
    '''
    user_ns['BMMuser'].prompt = True
    user_ns['BMMuser'].macro_dryrun = False
    user_ns['BMMuser'].wheel = False
    user_ns['quadem1'].Iy.kind = 'omitted'
    yield from user_ns['quadem1'].on_plan()
    yield from user_ns['vor'].on_plan()
    yield from abs_set(user_ns['_locked_dwell_time'], 0.5, wait=True)
    yield from user_ns['dcm'].kill_plan()
    yield from user_ns['xafs_wheel'].recenter()
    user_ns['RE'].msg_hook = BMM_msg_hook

