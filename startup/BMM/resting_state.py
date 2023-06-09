try:
    from bluesky_queueserver import is_re_worker_active
except ImportError:
    # TODO: delete this when 'bluesky_queueserver' is distributed as part of collection environment
    def is_re_worker_active():
        return False

from bluesky.plan_stubs import mv, sleep
import datetime
import matplotlib

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

from BMM.functions  import now
from BMM.kafka      import kafka_message
from BMM.logging    import BMM_msg_hook
from BMM.suspenders import BMM_suspenders, BMM_clear_suspenders
from BMM.workspace  import rkvs

from BMM.user_ns.bmm         import BMMuser
from BMM.user_ns.dcm         import *
from BMM.user_ns.dwelltime   import _locked_dwell_time
from BMM.user_ns.detectors   import quadem1, vor
from BMM.user_ns.instruments import xafs_wheel

def resting_redis():
    user_ns['rkvs'].set('BMM:scan:type', 'idle')
    user_ns['rkvs'].set('BMM:scan:starttime', datetime.datetime.timestamp(datetime.datetime.now()))
    user_ns['rkvs'].set('BMM:scan:estimated', 0)
    return

def resting_state():
    '''
    Command line tool to bring controls into their resting state:

    - quadEM and Struck scaler enabled and measuring
    - dwell time set to 1/2 second
    - electron yield channel (quadEM channel 4) hinted as 'omitted'
    - user prompt set to True. macro dry-run set to False, RE.msg_hook set to BMM_msg_hook
    '''
    
    BMMuser.prompt, BMMuser.macro_dryrun, BMMuser.instrument , quadem1.Iy.kind = True, False, '', 'omitted'
    ## NEVER prompt when using queue server
    if is_re_worker_active() is True:
        BMMuser.prompt = False
    quadem1.on(quiet=True)
    #vor.on()
    _locked_dwell_time.move(0.3)
    _locked_dwell_time.move(0.5)
    dcm.kill()
    dcm.mode = 'fixed'
    kafka_message({'resting_state': True,})
    #user_ns['RE'].msg_hook = BMM_msg_hook
    if is_re_worker_active() is False:
        matplotlib.use('Qt5Agg')
    resting_redis()
    
def resting_state_plan():
    '''
    Plan for bringing controls into their resting state:

    - dwell time set to 1/2 second
    - electron yield channel (quadEM channel 4) hinted as 'omitted'
    - RE.msg_hook set to BMM_msg_hook
    '''

    #BMMuser.prompt = True
    #BMMuser.prompt, BMMuser.macro_dryrun, BMMuser.instrument , quadem1.Iy.kind = True, False, '', 'omitted'
    #yield from quadem1.on_plan()
    #yield from vor.on_plan()
    quadem1.Iy.kind = 'omitted'
    #BMMuser.instrument = ''
    yield from mv(_locked_dwell_time, 0.5)
    #yield from mv(user_ns['dm3_bct'].kill_cmd, 1)
    yield from sleep(0.2)
    yield from dcm.kill_plan()
    dcm.mode = 'fixed'
    kafka_message({'resting_state': True,})
    #user_ns['RE'].msg_hook = BMM_msg_hook
    if is_re_worker_active() is False:
        matplotlib.use('Qt5Agg')
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
    ## NEVER prompt when using queue server
    if is_re_worker_active() is True:
        BMMuser.prompt = False
    BMMuser.running_macro, BMMuser.lims = False, True
    yield from quadem1.on_plan()
    #yield from vor.on_plan()
    yield from mv(_locked_dwell_time, 0.5)
    #yield from mv(user_ns['dm3_bct'].kill_cmd, 1)
    yield from sleep(0.2)
    yield from dcm.kill_plan()
    yield from xafs_wheel.recenter()
    dcm.mode = 'fixed'
    user_ns['RE'].msg_hook = BMM_msg_hook
    if is_re_worker_active() is False:
        matplotlib.use('Qt5Agg')
    resting_redis()
    BMM_clear_suspenders()

