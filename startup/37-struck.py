from ophyd import Component as Cpt, EpicsSignalWithRBV, Signal
from ophyd.scaler import EpicsScaler

run_report(__file__)


####################################################################################
####                  ROI           ICR              OCR             time       ####
class DTCorr(DerivedSignal):
    def forward(self, value):
        return self.derived_from.value
    def inverse(self, value):
        df = self.derived_from.pvname
        if   any(scal in df for scal in ('S3', 'S15', 'S19')):
            return self.parent.dtcorrect(self.derived_from.value,
                                         self.parent.channels.chan7.value,
                                         self.parent.channels.chan11.value,
                                         _locked_dwell_time.dwell_time.readback.value)

        elif any(scal in df for scal in ('S4', 'S16', 'S20')):
            return self.parent.dtcorrect(self.derived_from.value,
                                         self.parent.channels.chan8.value,
                                         self.parent.channels.chan12.value,
                                         _locked_dwell_time.dwell_time.readback.value)

        elif any(scal in df for scal in ('S5', 'S17', 'S21')):
            return self.parent.dtcorrect(self.derived_from.value,
                                         self.parent.channels.chan9.value,
                                         self.parent.channels.chan13.value,
                                         _locked_dwell_time.dwell_time.readback.value)

        elif any(scal in df for scal in ('S6', 'S18', 'S22')):
            return self.parent.dtcorrect(self.derived_from.value,
                                         self.parent.channels.chan10.value,
                                         self.parent.channels.chan14.value,
                                         _locked_dwell_time.dwell_time.readback.value)

        else:
            return self.parent.dtcorrect(self.derived_from.value,
                                         self.parent.channels.chan7.value,
                                         self.parent.channels.chan11.value,
                                         _locked_dwell_time.dwell_time.readback.value)




class DTCorr1(DerivedSignal):
    def forward(self, value):
        return self.parent.channels.chan3.value
    def inverse(self, value):
        return self.parent.dtcorrect(self.parent.channels.chan3.value, # 21: chan15   31: chan19
                                     self.parent.channels.chan7.value,
                                     self.parent.channels.chan11.value,
                                     _locked_dwell_time.dwell_time.readback.value)

class DTCorr2(DerivedSignal):
    def forward(self, value):
        return self.parent.channels.chan4.value
    def inverse(self, value):
        return self.parent.dtcorrect(self.parent.channels.chan4.value, # 22: chan16   32: chan20
                                     self.parent.channels.chan8.value,
                                     self.parent.channels.chan12.value,
                                     _locked_dwell_time.dwell_time.readback.value)

class DTCorr3(DerivedSignal):
    def forward(self, value):
        return self.parent.channels.chan5.value
    def inverse(self, value):
        return self.parent.dtcorrect(self.parent.channels.chan5.value, # 23: chan17   33: chan21
                                     self.parent.channels.chan9.value,
                                     self.parent.channels.chan13.value,
                                     _locked_dwell_time.dwell_time.readback.value)

class DTCorr4(DerivedSignal):
    def forward(self, value):
        return self.parent.channels.chan6.value
    def inverse(self, value):
        return self.parent.dtcorrect(self.parent.channels.chan6.value, # 24: chan18   34: chan22
                                     self.parent.channels.chan10.value,
                                     self.parent.channels.chan14.value,
                                     _locked_dwell_time.dwell_time.readback.value)

#from subprocess import call
#call(['caput', 'XF:06BM-ES:1{Sclr:1}.S3.PREC', '2'])

class BMMVortex(EpicsScaler):
    maxiter = 20
    niter   = 0
    state   = Cpt(EpicsSignal, '.CONT')

    dtcorr1 = Cpt(DTCorr1, derived_from='channels.chan3')
    dtcorr2 = Cpt(DTCorr2, derived_from='channels.chan4')
    dtcorr3 = Cpt(DTCorr3, derived_from='channels.chan5')
    dtcorr4 = Cpt(DTCorr4, derived_from='channels.chan6')

    dtcorr21 = Cpt(DTCorr, derived_from='channels.chan15')
    dtcorr22 = Cpt(DTCorr, derived_from='channels.chan16')
    dtcorr23 = Cpt(DTCorr, derived_from='channels.chan17')
    dtcorr24 = Cpt(DTCorr, derived_from='channels.chan18')
    
    dtcorr31 = Cpt(DTCorr, derived_from='channels.chan19')
    dtcorr32 = Cpt(DTCorr, derived_from='channels.chan20')
    dtcorr33 = Cpt(DTCorr, derived_from='channels.chan21')
    dtcorr34 = Cpt(DTCorr, derived_from='channels.chan22')
    

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
        self.names.name15.put('ROI2.1')
        self.names.name16.put('ROI2.2')
        self.names.name17.put('ROI2.3')
        self.names.name18.put('ROI2.4')
        self.names.name19.put('ROI3.1')
        self.names.name20.put('ROI3.2')
        self.names.name21.put('ROI3.3')
        self.names.name22.put('ROI3.4')
        self.names.name25.put('Bicron')
        self.names.name26.put('APD')

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
        yield from abs_set(self.names.name15, 'ROI2.1')
        yield from abs_set(self.names.name16, 'ROI2.2')
        yield from abs_set(self.names.name17, 'ROI2.3')
        yield from abs_set(self.names.name18, 'ROI2.4')
        yield from abs_set(self.names.name19, 'ROI3.1')
        yield from abs_set(self.names.name20, 'ROI3.2')
        yield from abs_set(self.names.name21, 'ROI3.3')
        yield from abs_set(self.names.name22, 'ROI3.4')
        yield from abs_set(self.names.name25, 'Bicron')
        yield from abs_set(self.names.name26, 'APD')

    ## see Woicik et al, https://doi.org/10.1107/S0909049510009064
    def dtcorrect(self, roi, icr, ocr, inttime, dt=280.0):
        if roi is None: roi = 1.0
        if icr is None: icr = 1.0
        if ocr is None: ocr = 1.0
        if inttime is None: inttime = 1.0
        if icr is None or icr<1.0:
            icr=1.0
        if ocr is None or ocr<1.0:
            ocr=1.0
        rr = float(roi)
        ii = float(icr)
        oo = float(ocr)
        tt = float(inttime)
        dt = dt*1e-9
        if tt<0.001:
            tt=0.001
        if dt<1e-9:
            return rr*ii/oo
        totn  = 0.0
        test  = 1.0
        count = 0
        toto  = ii/tt
        if icr <= 1.0:
            totn = oo
            test = 0
        while test > dt:
            totn = (ii/tt) * exp(toto*dt)
            test = (totn - toto) / toto
            toto = totn
            count = count+1
            if (count > self.maxiter):
                test = 0
        self.niter = count
        return float(rr * (totn*tt/oo))

    def set_hints(self, chan):
        '''Set the dead time correction attributes to hinted for the selected, configured channel'''
        for pv in (self.dtcorr1,  self.dtcorr2,  self.dtcorr3,  self.dtcorr4,
                   self.dtcorr21, self.dtcorr22, self.dtcorr23, self.dtcorr24,
                   self.dtcorr31, self.dtcorr32, self.dtcorr33, self.dtcorr34):
            pv.kind = 'normal'
        if chan == 1:
            for pv in (self.dtcorr1,  self.dtcorr2,  self.dtcorr3,  self.dtcorr4):
                pv.kind = 'hinted'
        elif chan == 2:
            for pv in (self.dtcorr21, self.dtcorr22, self.dtcorr23, self.dtcorr24):
                pv.kind = 'hinted'
        elif chan == 3:
            for pv in (self.dtcorr31, self.dtcorr32, self.dtcorr33, self.dtcorr34):
                pv.kind = 'hinted'
            

    
vor = BMMVortex('XF:06BM-ES:1{Sclr:1}', name='vor')
vor.set_hints(1)

for i in list(range(3,23)):
    text = 'vor.channels.chan%d.kind = \'normal\'' % i
    exec(text)
for i in list(range(1,3)) + list(range(23,33)):
    text = 'vor.channels.chan%d.kind = \'omitted\'' % i
    exec(text)

vor.state.kind = 'omitted'


vor.dtcorr1.name = 'DTC1'
vor.dtcorr2.name = 'DTC2'
vor.dtcorr3.name = 'DTC3'
vor.dtcorr4.name = 'DTC4'

vor.dtcorr21.name = 'DTC2.1'
vor.dtcorr22.name = 'DTC2.2'
vor.dtcorr23.name = 'DTC2.3'
vor.dtcorr24.name = 'DTC2.4'

vor.dtcorr31.name = 'DTC3.1'
vor.dtcorr32.name = 'DTC3.2'
vor.dtcorr33.name = 'DTC3.3'
vor.dtcorr34.name = 'DTC3.4'


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
vor.channels.chan15.name = 'ROI2.1'
vor.channels.chan16.name = 'ROI2.2'
vor.channels.chan17.name = 'ROI2.3'
vor.channels.chan18.name = 'ROI2.4'
vor.channels.chan19.name = 'ROI3.1'
vor.channels.chan20.name = 'ROI3.2'
vor.channels.chan21.name = 'ROI3.3'
vor.channels.chan22.name = 'ROI3.4'
vor.channels.chan25.name = 'Bicron'
vor.channels.chan26.name = 'APD'


class GonioStruck(EpicsScaler):
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



    
bicron = GonioStruck('XF:06BM-ES:1{Sclr:1}', name='bicron')
for i in list(range(1,33)):
    text = 'bicron.channels.chan%d.kind = \'omitted\'' % i
    exec(text)
bicron.channels.chan25.kind = 'hinted'
bicron.channels.chan26.kind = 'hinted'
bicron.channels.chan25.name = 'Bicron'
bicron.channels.chan26.name = 'APD'
