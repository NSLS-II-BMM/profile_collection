
from bluesky.plan_stubs import abs_set, mv


from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

from BMM.logging    import BMM_msg_hook
from BMM.suspenders import BMM_suspenders, BMM_clear_suspenders
from BMM.workspace  import rkvs

from BMM.user_ns.bmm         import BMMuser
from BMM.user_ns.dcm         import dcm
from BMM.user_ns.detectors   import _locked_dwell_time, quadem1, vor
from BMM.user_ns.instruments import xafs_wheel

def resting_redis():
    return()
    # rkvs = user_ns['rkvs']
    # rkvs.set('BMM:scan:type',      '')
    # rkvs.set('BMM:scan:starttime', '')
    # rkvs.set('BMM:scan:estimated', 0)

def resting_state():
    '''
    Command line tool to bring controls into their resting state:

    - quadEM and Struck scaler enabled and measuring
    - dwell time set to 1/2 second
    - electron yield channel (quadEM channel 4) hinted as 'omitted'
    - user prompt set to True. macro dry-run set to False, RE.msg_hook set to BMM_msg_hook
    '''
    
    BMMuser.prompt, BMMuser.macro_dryrun, BMMuser.instrument , quadem1.Iy.kind = True, False, '', 'omitted'
    quadem1.on()
    vor.on()
    _locked_dwell_time.move(0.3)
    _locked_dwell_time.move(0.5)
    dcm.kill()
    #user_ns['RE'].msg_hook = BMM_msg_hook
    resting_redis()
    
def resting_state_plan():
    '''
    Plan for bringing controls into their resting state:

    - dwell time set to 1/2 second
    - electron yield channel (quadEM channel 4) hinted as 'omitted'
    - RE.msg_hook set to BMM_msg_hook
    '''

    #BMMuser.prompt = True
    BMMuser.macro_dryrun = False
    #yield from quadem1.on_plan()
    #yield from vor.on_plan()
    quadem1.Iy.kind = 'omitted'
    #BMMuser.instrument = ''
    yield from mv(_locked_dwell_time, 0.5)
    dcm.kill()
    #user_ns['RE'].msg_hook = BMM_msg_hook
    resting_redis()
    

def end_of_macro():
    '''Plan for bringing controls into their resting state at the end of
    a macro or when a macro is stopped or aborted:

    - quadEM and Struck scaler enabled and measuring
    - dwell time set to 1/2 second
    - electron yield channel (quadEM channel 4) hinted as 'omitted'
    - user prompt set to True. macro dry-run set to False, RE.msg_hook set to BMM_msg_hook
    '''
    
    BMMuser.prompt, BMMuser.macro_dryrun, BMMuser.instrument , quadem1.Iy.kind = True, False, '', 'omitted'
    BMMuser.running_macro, BMMuser.lims = False, True
    yield from quadem1.on_plan()
    yield from vor.on_plan()
    yield from mv(_locked_dwell_time, 0.5)
    yield from dcm.kill_plan()
    yield from xafs_wheel.recenter()
    user_ns['RE'].msg_hook = BMM_msg_hook
    resting_redis()
    BMM_clear_suspenders()

