from ophyd import (SingleTrigger, Component as Cpt, Device, DeviceStatus, EpicsSignal)

class EPS_Shutter(Device):
    state = Cpt(EpicsSignal, 'Pos-Sts')
    cls = Cpt(EpicsSignal, 'Cmd:Cls-Cmd')
    opn = Cpt(EpicsSignal, 'Cmd:Opn-Cmd')
    error = Cpt(EpicsSignal,'Err-Sts')
    permit = Cpt(EpicsSignal, 'Permit:Enbl-Sts')
    enabled = Cpt(EpicsSignal, 'Enbl-Sts')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.color = 'red'

    def open_plan(self):
        yield from mv(self.opn, 1)

    def close_plan(self):
        yield from mv(self.cls, 1)

    def open(self):
        print('Opening {}'.format(self.name))
        self.opn.put(1)

    def close(self):
        print('Closing {}'.format(self.name))
        self.cls.put(1)

class BMPS_Shutter(Device):
    state = Cpt(EpicsSignal, 'Sts:BM_BMPS_Opn-Sts')

bmps = BMPS_Shutter('SR:C06-EPS{PLC:1}', name='BMPS')

class IDPS_Shutter(Device):
    state = Cpt(EpicsSignal, 'Sts:BM_PS_OpnA3-Sts')

idps = IDPS_Shutter('SR:C06-EPS{PLC:1}', name = 'IDPS')


sha = EPS_Shutter('XF:06BM-PPS{Sh:FE}', name = 'Front-End Shutter')
sha.shutter_type = 'FE'
shb = EPS_Shutter('XF:06BM-PPS{Sh:A}', name = 'Photon Shutter')
shb.shutter_type = 'PH'

fs1 = EPS_Shutter('XF:06BMA-OP{FS:1}', name = 'Fluorescent Screen')
fs1.shutter_type = 'FS'


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
