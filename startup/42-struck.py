from ophyd import Component as Cpt, EpicsSignalWithRBV, Signal
from ophyd.scaler import EpicsScaler


class BMMVortex(EpicsScaler):
    state = Cpt(EpicsSignal, '.CONT')
    name3 = Cpt(EpicsSignal, '.NM3')
    name4 = Cpt(EpicsSignal, '.NM4')
    name5 = Cpt(EpicsSignal, '.NM5')
    name6 = Cpt(EpicsSignal, '.NM6')
    name7 = Cpt(EpicsSignal, '.NM7')
    name8 = Cpt(EpicsSignal, '.NM8')
    name9 = Cpt(EpicsSignal, '.NM9')
    name10 = Cpt(EpicsSignal, '.NM10')
    name11 = Cpt(EpicsSignal, '.NM11')
    name12 = Cpt(EpicsSignal, '.NM12')
    name13 = Cpt(EpicsSignal, '.NM13')
    name14 = Cpt(EpicsSignal, '.NM14')

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

    def channel_names(self):
        self.name3.put('ROI1')
        self.name4.put('ROI2')
        self.name5.put('ROI3')
        self.name6.put('ROI4')
        self.name7.put('ICR1')
        self.name8.put('ICR2')
        self.name9.put('ICR3')
        self.name10.put('ICR4')
        self.name11.put('OCR1')
        self.name12.put('OCR2')
        self.name13.put('OCR3')
        self.name14.put('OCR4')
        
    def channel_names_plan(self):
        yield from abs_set(self.name3,  'ROI1')
        yield from abs_set(self.name4,  'ROI2')
        yield from abs_set(self.name5,  'ROI3')
        yield from abs_set(self.name6,  'ROI4')
        yield from abs_set(self.name7,  'ICR1')
        yield from abs_set(self.name8,  'ICR2')
        yield from abs_set(self.name9,  'ICR3')
        yield from abs_set(self.name10, 'ICR4')
        yield from abs_set(self.name11, 'OCR1')
        yield from abs_set(self.name12, 'OCR2')
        yield from abs_set(self.name13, 'OCR3')
        yield from abs_set(self.name14, 'OCR4')
        
        

vortex_me4 = BMMVortex('XF:06BM-ES:1{Sclr:1}', name='vortex_me4')

