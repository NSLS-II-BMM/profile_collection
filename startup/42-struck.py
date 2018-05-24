from ophyd import Component as Cpt, EpicsSignalWithRBV, Signal
from ophyd.scaler import EpicsScaler




class DTCorr1(DerivedSignal):
    def forward(self, value):
        return self.dtcorrect(value, self.parent.channels.chan7.value, self.parent.channels.chan11.value, _locked_dwell_time.dwell_time.readback.value)
    def inverse(self, value):
        return self.parent.channels.chan3.value

class DTCorr2(DerivedSignal):
    def forward(self, value):
        return self.dtcorrect(value, self.parent.channels.chan8.value, self.parent.channels.chan12.value, _locked_dwell_time.dwell_time.readback.value)
    def inverse(self, value):
        return self.parent.channels.chan4.value

class DTCorr3(DerivedSignal):
    def forward(self, value):
        return self.dtcorrect(value, self.parent.channels.chan9.value, self.parent.channels.chan13.value, _locked_dwell_time.dwell_time.readback.value)
    def inverse(self, value):
        return self.parent.channels.chan5.value

class DTCorr4(DerivedSignal):
    def forward(self, value):
        return self.dtcorrect(value, self.parent.channels.chan10.value, self.parent.channels.chan14.value, _locked_dwell_time.dwell_time.readback.value)
    def inverse(self, value):
        return self.parent.channels.chan6.value


class BMMVortex(EpicsScaler):
    maxiter = 20
    niter = 0
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

    dtcorr1 = Cpt(DTCorr1, derived_from='channels.chan3')
    dtcorr2 = Cpt(DTCorr2, derived_from='channels.chan4')
    dtcorr3 = Cpt(DTCorr3, derived_from='channels.chan5')
    dtcorr4 = Cpt(DTCorr4, derived_from='channels.chan6')


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

    def dtcorrect(self, roi, icr, ocr, inttime=1, dt=280):
        dt = dt*1e-9
        if dt<1e-9:
            return roi*icr/ocr
        totn  = 0.0
        test  = 1.0
        count = 0
        toto  = icr/inttime
        if icr <= 1:
            totn = ocr
            test = 0
        while test > dt:
            totn = (icr/inttime) * exp(toto*dt)
            test = (totn - toto) / toto
            toto = totn
            count = count+1
            if (count > self.maxiter):
                test = 0
        self.niter = count
        return roi * (totn*inttime/ocr)


vortex_me4 = BMMVortex('XF:06BM-ES:1{Sclr:1}', name='vortex_me4')
vortex_me4.dtcorr1.kind = 'hinted'
vortex_me4.dtcorr2.kind = 'hinted'
vortex_me4.dtcorr3.kind = 'hinted'
vortex_me4.dtcorr4.kind = 'hinted'
for i in range(3,15):
    text = 'vortex_me4.name%d.kind = \'normal\'' % i
    exec(text)
for i in range(1,33):
    text = 'vortex_me4.channels.chan%d.kind = \'normal\'' % i
    exec(text)
