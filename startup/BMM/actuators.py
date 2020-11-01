from ophyd import (SingleTrigger, Component as Cpt, Device, DeviceStatus, EpicsSignal)
from bluesky.plan_stubs import null, abs_set, sleep, mv, mvr
import time

from BMM.logging import report, BMM_msg_hook
## from IPython import get_ipython
## user_ns = get_ipython().user_ns

try:
    from bluesky_queueserver.manager.profile_tools import set_user_ns
except ModuleNotFoundError:
    from ._set_user_ns import set_user_ns


class EPS_Shutter(Device):

    state = Cpt(EpicsSignal, 'Pos-Sts')
    cls = Cpt(EpicsSignal, 'Cmd:Cls-Cmd')
    opn = Cpt(EpicsSignal, 'Cmd:Opn-Cmd')
    error = Cpt(EpicsSignal,'Err-Sts')
    permit = Cpt(EpicsSignal, 'Permit:Enbl-Sts')
    enabled = Cpt(EpicsSignal, 'Enbl-Sts')
    maxcount = 3
    openval = 1                 # normal shutter values, FS1 is reversed
    closeval = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.color = 'red'

    def status(self):
        if self.state.get() == 1:
            return 'closed'
        else:
            return 'open'

    @set_user_ns
    def open_plan(self, *, user_ns):
        RE = user_ns['RE']
        RE.msg_hook = None
        count = 0
        while self.state.get() != self.openval:
            count += 1
            print(u'\u231b', end=' ', flush=True)
            yield from mv(self.opn, 1)
            if count >= self.maxcount:
                print('tried %d times and failed to open %s %s' % (count, self.name, ':('))  # u'\u2639'  unicode frown
                return(yield from null())
            time.sleep(1.5)
        report('Opened {}'.format(self.name))
        RE.msg_hook = BMM_msg_hook

    @set_user_ns
    def close_plan(self, *, user_ns,):
        RE = user_ns['RE']
        RE.msg_hook = None
        count = 0
        while self.state.get() != self.closeval:
            count += 1
            print(u'\u231b', end=' ', flush=True)
            yield from mv(self.cls, 1)
            if count >= self.maxcount:
                print('tried %d times and failed to close %s %s' % (count, self.name, ':('))
                return(yield from null())
            time.sleep(1.5)
        report('Closed {}'.format(self.name))
        RE.msg_hook = BMM_msg_hook

    @set_user_ns
    def open(self, *, user_ns):
        RE = user_ns['RE']
        RE.msg_hook = None
        if self.state.get() != self.openval:
            count = 0
            while self.state.get() != self.openval:
                count += 1
                print(u'\u231b', end=' ', flush=True)
                self.opn.put(1)
                if count >= self.maxcount:
                    print('tried %d times and failed to open %s %s' % (count, self.name, ':('))
                    return
                time.sleep(1.5)
            report(' Opened {}'.format(self.name))
        else:
            print('{} is open'.format(self.name))
        RE.msg_hook = BMM_msg_hook

    @set_user_ns
    def close(self, *, user_ns):
        RE = user_ns['RE']
        RE.msg_hook = None
        if self.state.get() != self.closeval:
            count = 0
            while self.state.get() != self.closeval:
                count += 1
                print(u'\u231b', end=' ', flush=True)
                self.cls.put(1)
                if count >= self.maxcount:
                    print('tried %d times and failed to close %s %s' % (count, self.name, ':('))
                    return
                time.sleep(1.5)
            report(' Closed {}'.format(self.name))
        else:
            print('{} is closed'.format(self.name))
        RE.msg_hook = BMM_msg_hook

    def _state(self):
        if self.state.get():
            state = 'closed'
            if self.name == 'FS1': state = 'in place'
            return error(state)
        state = 'open'
        if self.name == 'FS1': state = 'retracted'
        return(state + '  ')

    
class BMPS_Shutter(Device):
    state = Cpt(EpicsSignal, 'Sts:BM_BMPS_Opn-Sts')

class IDPS_Shutter(Device):
    state = Cpt(EpicsSignal, 'Sts:BM_PS_OpnA3-Sts')

class Spinner(Device):
    state = Cpt(EpicsSignal, 'On_Off')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on(self):
        report('Turning {} on'.format(self.name))
        self.state.put(1)
    start = on

    def off(self):
        report('Turning {} off'.format(self.name))
        self.state.put(0)
    stop = off

    def on_plan(self):
        report('Turning {} off'.format(self.name))
        yield from abs_set(self.state, 1, wait=True)

    def off_plan(self):
        report('Turning {} off'.format(self.name))
        yield from abs_set(self.state, 0, wait=True)

