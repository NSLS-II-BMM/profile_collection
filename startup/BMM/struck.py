from ophyd import Component as Cpt, EpicsSignalWithRBV, EpicsSignal, Signal, DerivedSignal
from ophyd.scaler import EpicsScaler

from numpy import exp

from bluesky.plan_stubs import abs_set

from IPython import get_ipython
user_ns = get_ipython().user_ns


class toss():
    '''The point of this throw-away class to be sure that the DTCorr class
    loads and initializes sensibly as we are setting up to use the
    analog fluorescence signal chains.  The values in icrs and ocrs
    will soon be overwritten with proper signals.'''
    value = 1
    def get(self):
        return self.value
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
        return self.derived_from.get()
    def inverse(self, value):
        df = self.derived_from.pvname
        dwell_time = user_ns['dwell_time']
        return self.parent.dtcorrect(self.derived_from.get(),
                                     icrs[df].get(),
                                     ocrs[df].get(),
                                     dwell_time.readback.get(),
                                     off=self.off)

        # elif any(scal in df for scal in ('S4', 'S16', 'S20')):
        #     return self.parent.dtcorrect(self.derived_from.get(),
        #                                  self.parent.channels.chan8.get(),
        #                                  self.parent.channels.chan12.get(),
        #                                  _locked_dwell_time.dwell_time.readback.get())

        # elif any(scal in df for scal in ('S5', 'S17', 'S21')):
        #     return self.parent.dtcorrect(self.derived_from.get(),
        #                                  self.parent.channels.chan9.get(),
        #                                  self.parent.channels.chan13.get(),
        #                                  _locked_dwell_time.dwell_time.readback.get())

        # elif any(scal in df for scal in ('S6', 'S18', 'S22')):
        #     return self.parent.dtcorrect(self.derived_from.get(),
        #                                  self.parent.channels.chan10.get(),
        #                                  self.parent.channels.chan14.get(),
        #                                  _locked_dwell_time.dwell_time.readback.get())

        # else:
        #     return self.parent.dtcorrect(self.derived_from.get(),
        #                                  self.parent.channels.chan7.get(),
        #                                  self.parent.channels.chan11.get(),
        #                                  _locked_dwell_time.dwell_time.readback.get())




# class DTCorr1(DerivedSignal):
#     off = False
#     def forward(self, value):
#         return self.parent.channels.chan3.get()
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan3.get(), # 21: chan15   31: chan19
#                                      self.parent.channels.chan7.get(),
#                                      self.parent.channels.chan11.get(),
#                                      _locked_dwell_time.dwell_time.readback.get(), self.off)

# class DTCorr2(DerivedSignal):
#     off = False
#     def forward(self, value):
#         return self.parent.channels.chan4.get()
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan4.get(), # 22: chan16   32: chan20
#                                      self.parent.channels.chan8.get(),
#                                      self.parent.channels.chan12.get(),
#                                      _locked_dwell_time.dwell_time.readback.get(), self.off)

# class DTCorr3(DerivedSignal):
#     off = False
#     def forward(self, value):
#         return self.parent.channels.chan5.get()
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan5.get(), # 23: chan17   33: chan21
#                                      self.parent.channels.chan9.get(),
#                                      self.parent.channels.chan13.get(),
#                                      _locked_dwell_time.dwell_time.readback.get(), self.off)

# class DTCorr4(DerivedSignal):
#     off = False
#     def forward(self, value):
#         return self.parent.channels.chan6.get()
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan6.get(), # 24: chan18   34: chan22
#                                      self.parent.channels.chan10.get(),
#                                      self.parent.channels.chan14.get(),
#                                      _locked_dwell_time.dwell_time.readback.get(), self.off)


# class DTCorr2_1(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan15.get()
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan15.get(), # 21: chan15   31: chan19
#                                      self.parent.channels.chan7.get(),
#                                      self.parent.channels.chan11.get(),
#                                      _locked_dwell_time.dwell_time.readback.get(), self.off)

# class DTCorr2_2(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan16.get()
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan16.get(), # 22: chan16   32: chan20
#                                      self.parent.channels.chan8.get(),
#                                      self.parent.channels.chan12.get(),
#                                      _locked_dwell_time.dwell_time.readback.get(), self.off)

# class DTCorr2_3(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan17.get()
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan17.get(), # 23: chan17   33: chan21
#                                      self.parent.channels.chan9.get(),
#                                      self.parent.channels.chan13.get(),
#                                      _locked_dwell_time.dwell_time.readback.get(), self.off)

# class DTCorr2_4(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan18.get()
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan18.get(), # 24: chan18   34: chan22
#                                      self.parent.channels.chan10.get(),
#                                      self.parent.channels.chan14.get(),
#                                      _locked_dwell_time.dwell_time.readback.get(), self.off)

# class DTCorr3_1(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan19.get()
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan19.get(), # 21: chan15   31: chan19
#                                      self.parent.channels.chan7.get(),
#                                      self.parent.channels.chan11.get(),
#                                      _locked_dwell_time.dwell_time.readback.get(), self.off)

# class DTCorr3_2(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan20.get()
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan20.get(), # 22: chan16   32: chan20
#                                      self.parent.channels.chan8.get(),
#                                      self.parent.channels.chan12.get(),
#                                      _locked_dwell_time.dwell_time.readback.get(), self.off)

# class DTCorr3_3(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan21.get()
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan21.get(), # 23: chan17   33: chan21
#                                      self.parent.channels.chan9.get(),
#                                      self.parent.channels.chan13.get(),
#                                      _locked_dwell_time.dwell_time.readback.get(), self.off)

# class DTCorr3_4(DerivedSignal):
#     off = True
#     def forward(self, value):
#         return self.parent.channels.chan22.get()
#     def inverse(self, value):
#         return self.parent.dtcorrect(self.parent.channels.chan22.get(), # 24: chan18   34: chan22
#                                      self.parent.channels.chan10.get(),
#                                      self.parent.channels.chan14.get(),
#                                      _locked_dwell_time.dwell_time.readback.get(), self.off)

    
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
        BMMuser = user_ns['BMMuser']
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



    
