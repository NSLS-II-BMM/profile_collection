from ophyd import (SingleTrigger, Component as Cpt, Device, DeviceStatus, EpicsSignal)
import time

run_report(__file__)

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
        if shb.state.value == 1:
            return 'closed'
        else:
            return 'open'

    def open_plan(self):
        RE.msg_hook = None
        count = 0
        while self.state.value == self.openval:
            count += 1
            print(u'\u231b', end=' ', flush=True)
            yield from mv(self.opn, 1)
            if count >= self.maxcount:
                print('tried %d times and failed to open %s %s' % (count, self.name, ':('))  # u'\u2639'  unicode frown
                yield from null()
                return
            time.sleep(1.5)
        BMM_log_info('Opened {}'.format(self.name))
        print(' Opened {}'.format(self.name))
        RE.msg_hook = BMM_msg_hook

    def close_plan(self):
        RE.msg_hook = None
        count = 0
        while self.state.value == self.closeval:
            count += 1
            print(u'\u231b', end=' ', flush=True)
            yield from mv(self.cls, 1)
            if count >= self.maxcount:
                print('tried %d times and failed to close %s %s' % (count, self.name, ':('))
                yield from null()
                return
            time.sleep(1.5)
        BMM_log_info('Closed {}'.format(self.name))
        print(' Closed {}'.format(self.name))
        RE.msg_hook = BMM_msg_hook

    def open(self):
        RE.msg_hook = None
        if self.state.value == self.openval:
            count = 0
            while self.state.value == self.openval:
                count += 1
                print(u'\u231b', end=' ', flush=True)
                self.opn.put(1)
                if count >= self.maxcount:
                    print('tried %d times and failed to open %s %s' % (count, self.name, ':('))
                    return
                time.sleep(1.5)
            print(' Opened {}'.format(self.name))
            BMM_log_info('Opened {}'.format(self.name))
        else:
            print('{} is open'.format(self.name))
        RE.msg_hook = BMM_msg_hook

    def close(self):
        RE.msg_hook = None
        if self.state.value == self.closeval:
            count = 0
            while self.state.value == self.closeval:
                count += 1
                print(u'\u231b', end=' ', flush=True)
                self.cls.put(1)
                if count >= self.maxcount:
                    print('tried %d times and failed to close %s %s' % (count, self.name, ':('))
                    return
                time.sleep(1.5)
            print(' Closed {}'.format(self.name))
            BMM_log_info('Closed {}'.format(self.name))
        else:
            print('{} is closed'.format(self.name))
        RE.msg_hook = BMM_msg_hook


class BMPS_Shutter(Device):
    state = Cpt(EpicsSignal, 'Sts:BM_BMPS_Opn-Sts')

try:
    bmps = BMPS_Shutter('SR:C06-EPS{PLC:1}', name='BMPS')
except:
    pass

class IDPS_Shutter(Device):
    state = Cpt(EpicsSignal, 'Sts:BM_PS_OpnA3-Sts')

try:
    idps = IDPS_Shutter('SR:C06-EPS{PLC:1}', name = 'IDPS')
except:
    pass


sha = EPS_Shutter('XF:06BM-PPS{Sh:FE}', name = 'Front-End Shutter')
sha.shutter_type = 'FE'
sha.openval  = 1
sha.closeval = 0
shb = EPS_Shutter('XF:06BM-PPS{Sh:A}', name = 'Photon Shutter')
shb.shutter_type = 'PH'
shb.openval  = 1
shb.closeval = 0

fs1 = EPS_Shutter('XF:06BMA-OP{FS:1}', name = 'Fluorescent Screen')
fs1.shutter_type = 'FS'
fs1.openval  = 0
fs1.closeval = 1


class Spinner(Device):
    state = Cpt(EpicsSignal, 'On_Off')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on(self):
        print('Turning {} on'.format(self.name))
        self.state.put(1)

    def start(self):
        print('Turning {} on'.format(self.name))
        self.state.put(1)

    def off(self):
        print('Turning {} off'.format(self.name))
        self.state.put(0)

    def stop(self):
        print('Turning {} off'.format(self.name))
        self.state.put(0)

    def on_plan(self):
        yield from abs_set(self.state, 1)

    def off_plan(self):
        yield from abs_set(self.state, 0)


fan = Spinner('XF:06BM-EPS{Fan}', name = 'spinner')
