
run_report(__file__)

def resting_state():
    '''
    Command line tool to bring controls into their resting state:

    - quadEM and Struck scaler enabled and measuring
    - dwell time set to 1/2 second
    - electron yield channel (quadEM channel 4) hinted as 'omitted'
    - user prompt set to True. macro dry-run set to False, RE.msg_hook set to BMM_msg_hook
    '''
    BMMuser.prompt = True
    BMMuser.macro_dryrun = False
    quadem1.on()
    vor.on()
    _locked_dwell_time.move(0.3)
    _locked_dwell_time.move(0.5)
    quadem1.Iy.kind = 'omitted'
    dcm.kill()
    RE.msg_hook = BMM_msg_hook

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
    yield from abs_set(_locked_dwell_time, 0.5, wait=True)
    dcm.kill()
    RE.msg_hook = BMM_msg_hook

def end_of_macro():
    '''
    Plan for bringing controls into their resting state at the end of a macro:

    - quadEM and Struck scaler enabled and measuring
    - dwell time set to 1/2 second
    - electron yield channel (quadEM channel 4) hinted as 'omitted'
    - user prompt set to True. macro dry-run set to False, RE.msg_hook set to BMM_msg_hook
    '''
    BMMuser.prompt = True
    BMMuser.macro_dryrun = False
    quadem1.Iy.kind = 'omitted'
    yield from quadem1.on_plan()
    yield from vor.on_plan()
    yield from abs_set(_locked_dwell_time, 0.5, wait=True)
    yield from dcm.kill_plan()
    yield from xafs_wheel.recenter()
    RE.msg_hook = BMM_msg_hook

