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
        self.color = 'red'

    def open_plan(self):
        yield from bp.mv(self.opn, 1)

    def close_plan(self):
        yield from bp.mv(self.cls, 1)

    def open(self):
        print('Opening {}'.format(self.name))
        self.opn.put(1)

    def close(self):
        print('Closing {}'.format(self.name))
        self.cls.put(1)

shutter_fe = EPS_Shutter('XF:06BM-PPS{Sh:FE}', name = 'FE Shutter')
shutter_fe.shutter_type = 'FE'
shutter_ph = EPS_Shutter('XF:06BM-PPS{Sh:A}', name = 'PH Shutter')
shutter_ph.shutter_type = 'PH'

fs1 = EPS_Shutter('XF:06BMA-OP{FS:1}', name = 'Fluorescent Screen')
fs1.shutter_type = 'FS'
