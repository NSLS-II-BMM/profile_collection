from ophyd import Component as Cpt, EpicsSignalWithRBV, Signal
from ophyd.scaler import EpicsScaler


class BMMVortex(EpicsScaler):
    state = Cpt(EpicsSignal, '.CONT')

    def on(self):
        print('Turning {} on'.format(self.name))
        self.state.put(1)

    def off(self):
        print('Turning {} off'.format(self.name))
        self.state.put(0)

    def on_plan(self):
        yield from abs_set(self.state, 1)

    def off_plan(self):
        yield from abs_set(self.state, 0)

    

scalar1 = BMMVortex('XF:06BM-ES:1{Sclr:1}', name='scalar1')
