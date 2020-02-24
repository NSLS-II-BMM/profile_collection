from ophyd import Component as Cpt, EpicsSignalWithRBV, Signal
from ophyd.scaler import EpicsScaler

run_report(__file__)


class toss():
    value = 1
ts = toss()

icrs = {'XF:06BM-ES:1{Sclr:1}.S3' : ts,
        'XF:06BM-ES:1{Sclr:1}.S4' : ts,
        'XF:06BM-ES:1{Sclr:1}.S5' : ts,
        'XF:06BM-ES:1{Sclr:1}.S6' : ts,

        'XF:06BM-ES:1{Sclr:1}.S15' : ts,
        'XF:06BM-ES:1{Sclr:1}.S16' : ts,
        'XF:06BM-ES:1{Sclr:1}.S17' : ts,
        'XF:06BM-ES:1{Sclr:1}.S18' : ts,

        'XF:06BM-ES:1{Sclr:1}.S19' : ts,
        'XF:06BM-ES:1{Sclr:1}.S20' : ts,
        'XF:06BM-ES:1{Sclr:1}.S21' : ts,
        'XF:06BM-ES:1{Sclr:1}.S22' : ts,}

ocrs = {'XF:06BM-ES:1{Sclr:1}.S3' : ts,
        'XF:06BM-ES:1{Sclr:1}.S4' : ts,
        'XF:06BM-ES:1{Sclr:1}.S5' : ts,
        'XF:06BM-ES:1{Sclr:1}.S6' : ts,

        'XF:06BM-ES:1{Sclr:1}.S15' : ts,
        'XF:06BM-ES:1{Sclr:1}.S16' : ts,
        'XF:06BM-ES:1{Sclr:1}.S17' : ts,
        'XF:06BM-ES:1{Sclr:1}.S18' : ts,

        'XF:06BM-ES:1{Sclr:1}.S19' : ts,
        'XF:06BM-ES:1{Sclr:1}.S20' : ts,
        'XF:06BM-ES:1{Sclr:1}.S21' : ts,
        'XF:06BM-ES:1{Sclr:1}.S22' : ts}


####################################################################################
####                  ROI           ICR              OCR             time       ####
class DTCorr(DerivedSignal):
    off = False
    def forward(self, value):
        return self.derived_from.value
    def inverse(self, value):
        df = self.derived_from.pvname

        return self.parent.dtcorrect(self.derived_from.value,
                                     icrs[df].value,
                                     ocrs[df].value,
                                     _locked_dwell_time.dwell_time.readback.value, self.off)

        # elif any(scal in df for scal in ('S4', 'S16', 'S20')):
        #     return self.parent.dtcorrect(self.derived_from.value,
        #                                  self.parent.channels.chan8.value,
        #                                  self.parent.channels.chan12.value,
        #                                  _locked_dwell_time.dwell_time.readback.value)

        # elif any(scal in df for scal in ('S5', 'S17', 'S21')):
        #     return self.parent.dtcorrect(self.derived_from.value,
        #                                  self.parent.channels.chan9.value,
        #                                  self.parent.channels.chan13.value,
        #                                  _locked_dwell_time.dwell_time.readback.value)

        # elif any(scal in df for scal in ('S6', 'S18', 'S22')):
        #     return self.parent.dtcorrect(self.derived_from.value,
        #                                  self.parent.channels.chan10.value,
        #                                  self.parent.channels.chan14.value,
        #                                  _locked_dwell_time.dwell_time.readback.value)

        # else:
        #     return self.parent.dtcorrect(self.derived_from.value,
        #                                  self.parent.channels.chan7.value,
        #                                  self.parent.channels.chan11.value,
        #                                  _locked_dwell_time.dwell_time.readback.value)




# class DTCorr1(DerivedSignal):
#     off = False
#     def forward(self, value):
#         return self.parent.channels.chan3.value
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan3.value, # 21: chan15   31: chan19
#                                      self.parent.channels.chan7.value,
#                                      self.parent.channels.chan11.value,
#                                      _locked_dwell_time.dwell_time.readback.value, self.off)

# class DTCorr2(DerivedSignal):
#     off = False
#     def forward(self, value):
#         return self.parent.channels.chan4.value
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan4.value, # 22: chan16   32: chan20
#                                      self.parent.channels.chan8.value,
#                                      self.parent.channels.chan12.value,
#                                      _locked_dwell_time.dwell_time.readback.value, self.off)

# class DTCorr3(DerivedSignal):
#     off = False
#     def forward(self, value):
#         return self.parent.channels.chan5.value
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan5.value, # 23: chan17   33: chan21
#                                      self.parent.channels.chan9.value,
#                                      self.parent.channels.chan13.value,
#                                      _locked_dwell_time.dwell_time.readback.value, self.off)

# class DTCorr4(DerivedSignal):
#     off = False
#     def forward(self, value):
#         return self.parent.channels.chan6.value
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan6.value, # 24: chan18   34: chan22
#                                      self.parent.channels.chan10.value,
#                                      self.parent.channels.chan14.value,
#                                      _locked_dwell_time.dwell_time.readback.value, self.off)


# class DTCorr2_1(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan15.value
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan15.value, # 21: chan15   31: chan19
#                                      self.parent.channels.chan7.value,
#                                      self.parent.channels.chan11.value,
#                                      _locked_dwell_time.dwell_time.readback.value, self.off)

# class DTCorr2_2(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan16.value
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan16.value, # 22: chan16   32: chan20
#                                      self.parent.channels.chan8.value,
#                                      self.parent.channels.chan12.value,
#                                      _locked_dwell_time.dwell_time.readback.value, self.off)

# class DTCorr2_3(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan17.value
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan17.value, # 23: chan17   33: chan21
#                                      self.parent.channels.chan9.value,
#                                      self.parent.channels.chan13.value,
#                                      _locked_dwell_time.dwell_time.readback.value, self.off)

# class DTCorr2_4(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan18.value
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan18.value, # 24: chan18   34: chan22
#                                      self.parent.channels.chan10.value,
#                                      self.parent.channels.chan14.value,
#                                      _locked_dwell_time.dwell_time.readback.value, self.off)

# class DTCorr3_1(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan19.value
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan19.value, # 21: chan15   31: chan19
#                                      self.parent.channels.chan7.value,
#                                      self.parent.channels.chan11.value,
#                                      _locked_dwell_time.dwell_time.readback.value, self.off)

# class DTCorr3_2(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan20.value
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan20.value, # 22: chan16   32: chan20
#                                      self.parent.channels.chan8.value,
#                                      self.parent.channels.chan12.value,
#                                      _locked_dwell_time.dwell_time.readback.value, self.off)

# class DTCorr3_3(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan21.value
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan21.value, # 23: chan17   33: chan21
#                                      self.parent.channels.chan9.value,
#                                      self.parent.channels.chan13.value,
#                                      _locked_dwell_time.dwell_time.readback.value, self.off)

# class DTCorr3_4(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan22.value
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan22.value, # 24: chan18   34: chan22
#                                      self.parent.channels.chan10.value,
#                                      self.parent.channels.chan14.value,
#                                      _locked_dwell_time.dwell_time.readback.value, self.off)

    
#from subprocess import call
#call(['caput', 'XF:06BM-ES:1{Sclr:1}.S3.PREC', '2'])

class BMMVortex(EpicsScaler):
    maxiter = 20
    niter   = 0
    state   = Cpt(EpicsSignal, '.CONT')

    # dtcorr1 = Cpt(DTCorr1, derived_from='channels.chan3')
    # dtcorr2 = Cpt(DTCorr2, derived_from='channels.chan4')
    # dtcorr3 = Cpt(DTCorr3, derived_from='channels.chan5')
    # dtcorr4 = Cpt(DTCorr4, derived_from='channels.chan6')

    # dtcorr21 = Cpt(DTCorr2_1, derived_from='channels.chan15')
    # dtcorr22 = Cpt(DTCorr2_2, derived_from='channels.chan16')
    # dtcorr23 = Cpt(DTCorr2_3, derived_from='channels.chan17')
    # dtcorr24 = Cpt(DTCorr2_4, derived_from='channels.chan18')
    
    # dtcorr31 = Cpt(DTCorr3_1, derived_from='channels.chan19')
    # dtcorr32 = Cpt(DTCorr3_2, derived_from='channels.chan20')
    # dtcorr33 = Cpt(DTCorr3_3, derived_from='channels.chan21')
    # dtcorr34 = Cpt(DTCorr3_4, derived_from='channels.chan22')


        
    dtcorr1 = Cpt(DTCorr, derived_from='channels.chan3')
    dtcorr2 = Cpt(DTCorr, derived_from='channels.chan4')
    dtcorr3 = Cpt(DTCorr, derived_from='channels.chan5')
    dtcorr4 = Cpt(DTCorr, derived_from='channels.chan6')

    dtcorr21 = Cpt(DTCorr, derived_from='channels.chan15')
    dtcorr21.off = True
    dtcorr22 = Cpt(DTCorr, derived_from='channels.chan16')
    dtcorr22.off = True
    dtcorr23 = Cpt(DTCorr, derived_from='channels.chan17')
    dtcorr23.off = True
    dtcorr24 = Cpt(DTCorr, derived_from='channels.chan18')
    dtcorr24.off = True
    
    dtcorr31 = Cpt(DTCorr, derived_from='channels.chan19')
    dtcorr31.off = True
    dtcorr32 = Cpt(DTCorr, derived_from='channels.chan20')
    dtcorr32.off = True
    dtcorr33 = Cpt(DTCorr, derived_from='channels.chan21')
    dtcorr33.off = True
    dtcorr34 = Cpt(DTCorr, derived_from='channels.chan22')
    dtcorr34.off = True
    

    def on(self):
        print('Turning {} on'.format(self.name))
        self.state.put(1)

    def off(self):
        print('Turning {} off'.format(self.name))
        self.state.put(0)

    def on_plan(self):
        yield from abs_set(self.state, 1, wait=True)

    def off_plan(self):
        yield from abs_set(self.state, 0, wait=True)

    def channel_names(self, one, two, three):
        self.names.name3.put('ROI1' + ' - %s'%one )
        self.names.name4.put('ROI2' + ' - %s'%one)
        self.names.name5.put('ROI3' + ' - %s'%one)
        self.names.name6.put('ROI4' + ' - %s'%one)
        self.names.name7.put('ICR1')
        self.names.name8.put('ICR2')
        self.names.name9.put('ICR3')
        self.names.name10.put('ICR4')
        self.names.name11.put('OCR1')
        self.names.name12.put('OCR2')
        self.names.name13.put('OCR3')
        self.names.name14.put('OCR4')
        self.names.name15.put('ROI2_1' + ' - %s'%two)
        self.names.name16.put('ROI2_2' + ' - %s'%two)
        self.names.name17.put('ROI2_3' + ' - %s'%two)
        self.names.name18.put('ROI2_4' + ' - %s'%two)
        self.names.name19.put('ROI3_1' + ' - %s'%three)
        self.names.name20.put('ROI3_2' + ' - %s'%three)
        self.names.name21.put('ROI3_3' + ' - %s'%three)
        self.names.name22.put('ROI3_4' + ' - %s'%three)
        self.names.name25.put('Bicron')
        self.names.name26.put('APD')
        self.names.name31.put('eyield')

    def channel_names_plan(self, one, two, three):
        yield from abs_set(self.names.name3,  'ROI1' + ' - %s'%one)
        yield from abs_set(self.names.name4,  'ROI2' + ' - %s'%one)
        yield from abs_set(self.names.name5,  'ROI3' + ' - %s'%one)
        yield from abs_set(self.names.name6,  'ROI4' + ' - %s'%one)
        yield from abs_set(self.names.name7,  'ICR1')
        yield from abs_set(self.names.name8,  'ICR2')
        yield from abs_set(self.names.name9,  'ICR3')
        yield from abs_set(self.names.name10, 'ICR4')
        yield from abs_set(self.names.name11, 'OCR1')
        yield from abs_set(self.names.name12, 'OCR2')
        yield from abs_set(self.names.name13, 'OCR3')
        yield from abs_set(self.names.name14, 'OCR4')
        yield from abs_set(self.names.name15, 'ROI2_1' + ' - %s'%two)
        yield from abs_set(self.names.name16, 'ROI2_2' + ' - %s'%two)
        yield from abs_set(self.names.name17, 'ROI2_3' + ' - %s'%two)
        yield from abs_set(self.names.name18, 'ROI2_4' + ' - %s'%two)
        yield from abs_set(self.names.name19, 'ROI3_1' + ' - %s'%three)
        yield from abs_set(self.names.name20, 'ROI3_2' + ' - %s'%three)
        yield from abs_set(self.names.name21, 'ROI3_3' + ' - %s'%three)
        yield from abs_set(self.names.name22, 'ROI3_4' + ' - %s'%three)
        yield from abs_set(self.names.name25, 'Bicron')
        yield from abs_set(self.names.name26, 'APD')
        yield from abs_set(self.names.name31, 'eyield')

    ## see Woicik et al, https://doi.org/10.1107/S0909049510009064
    def dtcorrect(self, roi, icr, ocr, inttime, dt=280.0, off=False):
        if off: return roi      # return ROI value for a channel not being considered at this time
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
        '''Set the dead time correction attributes to hinted for the selected,
        configured channels
        
        Channels

          1) top row of quad SCAs
          2) middle row of quad SCAs
          3) bottom row of quad SCAs
         10) setup for SDC experiment with single channel going into 2 quad SCAs
         21) single element Vortex, ROI1
         22) single element Vortex, ROI2
         23) single element Vortex, ROI3
        '''
        for pv in (self.dtcorr1,  self.dtcorr2,  self.dtcorr3,  self.dtcorr4,
                   self.dtcorr21, self.dtcorr22, self.dtcorr23, self.dtcorr24,
                   self.dtcorr31, self.dtcorr32, self.dtcorr33, self.dtcorr34):
            pv.kind = 'normal'
            pv.off = True
        BMMuser.detector = 4
            
        if chan == 1:
            for pv in (self.dtcorr1,  self.dtcorr2,  self.dtcorr3,  self.dtcorr4):
                pv.kind = 'hinted'
                pv.off = False
        elif chan == 2:
            for pv in (self.dtcorr21, self.dtcorr22, self.dtcorr23, self.dtcorr24):
                pv.kind = 'hinted'
                pv.off = False
        elif chan == 3:
            for pv in (self.dtcorr31, self.dtcorr32, self.dtcorr33, self.dtcorr34):
                pv.kind = 'hinted'
                pv.off = False
        elif chan == 10:
            for pv in (self.dtcorr1, self.dtcorr21, self.dtcorr31, self.dtcorr2, self.dtcorr22, self.dtcorr32):
                pv.kind = 'hinted'
                pv.off = False
        elif chan == 21:
            BMMuser.detector = 1
            for pv in (self.dtcorr1,):
                pv.kind = 'hinted'
                pv.off = False
        elif chan == 22:
            BMMuser.detector = 1
            for pv in (self.dtcorr21,):
                pv.kind = 'hinted'
                pv.off = False
        elif chan == 23:
            BMMuser.detector = 1
            for pv in (self.dtcorr31,):
                pv.kind = 'hinted'
                pv.off = False
            

    
vor = BMMVortex('XF:06BM-ES:1{Sclr:1}', name='vor')
icrs['XF:06BM-ES:1{Sclr:1}.S3']  = vor.channels.chan7
icrs['XF:06BM-ES:1{Sclr:1}.S4']  = vor.channels.chan8
icrs['XF:06BM-ES:1{Sclr:1}.S5']  = vor.channels.chan9
icrs['XF:06BM-ES:1{Sclr:1}.S6']  = vor.channels.chan10

icrs['XF:06BM-ES:1{Sclr:1}.S15'] = vor.channels.chan7
icrs['XF:06BM-ES:1{Sclr:1}.S16'] = vor.channels.chan8
icrs['XF:06BM-ES:1{Sclr:1}.S17'] = vor.channels.chan9
icrs['XF:06BM-ES:1{Sclr:1}.S18'] = vor.channels.chan10

icrs['XF:06BM-ES:1{Sclr:1}.S19'] = vor.channels.chan7
icrs['XF:06BM-ES:1{Sclr:1}.S20'] = vor.channels.chan8
icrs['XF:06BM-ES:1{Sclr:1}.S21'] = vor.channels.chan9
icrs['XF:06BM-ES:1{Sclr:1}.S22'] = vor.channels.chan10

ocrs['XF:06BM-ES:1{Sclr:1}.S3']  = vor.channels.chan11
ocrs['XF:06BM-ES:1{Sclr:1}.S4']  = vor.channels.chan12
ocrs['XF:06BM-ES:1{Sclr:1}.S5']  = vor.channels.chan13
ocrs['XF:06BM-ES:1{Sclr:1}.S6']  = vor.channels.chan14

ocrs['XF:06BM-ES:1{Sclr:1}.S15'] = vor.channels.chan11
ocrs['XF:06BM-ES:1{Sclr:1}.S16'] = vor.channels.chan12
ocrs['XF:06BM-ES:1{Sclr:1}.S17'] = vor.channels.chan13
ocrs['XF:06BM-ES:1{Sclr:1}.S18'] = vor.channels.chan14

ocrs['XF:06BM-ES:1{Sclr:1}.S19'] = vor.channels.chan11
ocrs['XF:06BM-ES:1{Sclr:1}.S20'] = vor.channels.chan12
ocrs['XF:06BM-ES:1{Sclr:1}.S21'] = vor.channels.chan13
ocrs['XF:06BM-ES:1{Sclr:1}.S22'] = vor.channels.chan14

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

vor.dtcorr21.name = 'DTC2_1'
vor.dtcorr22.name = 'DTC2_2'
vor.dtcorr23.name = 'DTC2_3'
vor.dtcorr24.name = 'DTC2_4'

vor.dtcorr31.name = 'DTC3_1'
vor.dtcorr32.name = 'DTC3_2'
vor.dtcorr33.name = 'DTC3_3'
vor.dtcorr34.name = 'DTC3_4'


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
vor.channels.chan15.name = 'ROI2_1'
vor.channels.chan16.name = 'ROI2_2'
vor.channels.chan17.name = 'ROI2_3'
vor.channels.chan18.name = 'ROI2_4'
vor.channels.chan19.name = 'ROI3_1'
vor.channels.chan20.name = 'ROI3_2'
vor.channels.chan21.name = 'ROI3_3'
vor.channels.chan22.name = 'ROI3_4'
vor.channels.chan25.name = 'Bicron'
vor.channels.chan26.name = 'APD'

## electron yield detector, via Keithley and v2f converter
vor.channels.chan31.name = 'eyield'
vor.channels.chan31.kind = 'omitted'

class GonioStruck(EpicsScaler):
    def on(self):
        print('Turning {} on'.format(self.name))
        self.state.put(1)

    def off(self):
        print('Turning {} off'.format(self.name))
        self.state.put(0)

    def on_plan(self):
        yield from abs_set(self.state, 1, wait=True)

    def off_plan(self):
        yield from abs_set(self.state, 0, wait=True)



    
bicron = GonioStruck('XF:06BM-ES:1{Sclr:1}', name='bicron')
for i in list(range(1,33)):
    text = 'bicron.channels.chan%d.kind = \'omitted\'' % i
    exec(text)
bicron.channels.chan25.kind = 'hinted'
bicron.channels.chan26.kind = 'hinted'
bicron.channels.chan25.name = 'Bicron'
bicron.channels.chan26.name = 'APD'
