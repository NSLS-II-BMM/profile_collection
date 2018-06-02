from ophyd import Component as Cpt, EpicsSignalWithRBV, Signal
from ophyd.scaler import EpicsScaler


##################################################################################################################################
####                         ROI                 ICR                                OCR                            time       ####
class DTCorr1(DerivedSignal):
    def forward(self, value):
        return self.parent.channels.chan3.value
    def inverse(self, value):
        return self.parent.dtcorrect(value, self.parent.channels.chan7.value, self.parent.channels.chan11.value, inttime=_locked_dwell_time.dwell_time.readback.value)

class DTCorr2(DerivedSignal):
    def forward(self, value):
        return self.parent.channels.chan4.value
    def inverse(self, value):
        return self.parent.dtcorrect(value, self.parent.channels.chan8.value, self.parent.channels.chan12.value, inttime=_locked_dwell_time.dwell_time.readback.value)

class DTCorr3(DerivedSignal):
    def forward(self, value):
        return self.parent.channels.chan5.value
    def inverse(self, value):
        return self.parent.dtcorrect(value, self.parent.channels.chan9.value, self.parent.channels.chan13.value, inttime=_locked_dwell_time.dwell_time.readback.value)

class DTCorr4(DerivedSignal):
    def forward(self, value):
        return self.parent.channels.chan6.value
    def inverse(self, value):
        return self.parent.dtcorrect(value, self.parent.channels.chan10.value, self.parent.channels.chan14.value, inttime=_locked_dwell_time.dwell_time.readback.value)


class BMMVortex(EpicsScaler):
    maxiter = 20
    niter   = 0
    state   = Cpt(EpicsSignal, '.CONT')

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
        self.names.name3.put('ROI1')
        self.names.name4.put('ROI2')
        self.names.name5.put('ROI3')
        self.names.name6.put('ROI4')
        self.names.name7.put('ICR1')
        self.names.name8.put('ICR2')
        self.names.name9.put('ICR3')
        self.names.name10.put('ICR4')
        self.names.name11.put('OCR1')
        self.names.name12.put('OCR2')
        self.names.name13.put('OCR3')
        self.names.name14.put('OCR4')

    def channel_names_plan(self):
        yield from abs_set(self.names.name3,  'ROI1')
        yield from abs_set(self.names.name4,  'ROI2')
        yield from abs_set(self.names.name5,  'ROI3')
        yield from abs_set(self.names.name6,  'ROI4')
        yield from abs_set(self.names.name7,  'ICR1')
        yield from abs_set(self.names.name8,  'ICR2')
        yield from abs_set(self.names.name9,  'ICR3')
        yield from abs_set(self.names.name10, 'ICR4')
        yield from abs_set(self.names.name11, 'OCR1')
        yield from abs_set(self.names.name12, 'OCR2')
        yield from abs_set(self.names.name13, 'OCR3')
        yield from abs_set(self.names.name14, 'OCR4')

    def dtcorrect(self, roi, icr, ocr, inttime=1.0, dt=280.0):
        dt = dt*1e-9
        if icr<1:
            icr=1
        if ocr<1:
            ocr=1
        if inttime<0.001:
            inttime=0.001
        if dt<1e-9:
            return float(roi*icr)/float(ocr)
        totn  = 0.0
        test  = 1.0
        count = 0
        toto  = float(icr)/float(inttime)
        if icr <= 1:
            totn = float(ocr)
            test = 0
        while test > dt:
            totn = (icr/inttime) * exp(toto*dt)
            test = (totn - toto) / toto
            toto = totn
            count = count+1
            if (count > self.maxiter):
                test = 0
        self.niter = count
        return float(roi) * (totn*inttime/float(ocr))


vor = BMMVortex('XF:06BM-ES:1{Sclr:1}', name='vor')
vor.dtcorr1.kind = 'hinted'
vor.dtcorr2.kind = 'hinted'
vor.dtcorr3.kind = 'hinted'
vor.dtcorr4.kind = 'hinted'
for i in list(range(1,3)) + list(range(15,33)):
    text = 'vor.channels.chan%d.kind = \'omitted\'' % i
    exec(text)

vor.state.kind = 'omitted'

vor.dtcorr1.name = 'DTC1'
vor.dtcorr2.name = 'DTC2'
vor.dtcorr3.name = 'DTC3'
vor.dtcorr4.name = 'DTC4'

vor.channels.chan3.name = 'ROI1'
vor.channels.chan4.name = 'ROI2'
vor.channels.chan5.name = 'ROI3'
vor.channels.chan6.name = 'ROI4'
vor.channels.chan7.name = 'ICR1'
vor.channels.chan8.name = 'ICR2'
vor.channels.chan9.name = 'ICR3'
vor.channels.chan10.name = 'ICR4'
vor.channels.chan11.name = 'OCR1'
vor.channels.chan12.name = 'OCR2'
vor.channels.chan13.name = 'OCR3'
vor.channels.chan14.name = 'OCR4'
