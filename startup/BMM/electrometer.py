from ophyd import QuadEM, Component as Cpt, EpicsSignalWithRBV, Signal, DerivedSignal, EpicsSignal
from ophyd.quadem import QuadEMPort

from numpy import log, exp
from bluesky.plan_stubs import abs_set, sleep

from BMM.logging import BMM_log_info

from IPython import get_ipython
user_ns = get_ipython().user_ns

_locked_dwell_time = user_ns['_locked_dwell_time']

class Nanoize(DerivedSignal):
    def forward(self, value):
        return value * 1e-9 / _locked_dwell_time.dwell_time.readback.get()
    def inverse(self, value):
        return value * 1e9 * _locked_dwell_time.dwell_time.readback.get()

# class Normalized(DerivedSignal):
#     def forward(self, value):
#         return value * self.parent.current1.mean_value.get()
#     def inverse(self, value):
#         return value / self.parent.current1.mean_value.get()

# class TransXmu(DerivedSignal):
#     def forward(self, value):
#         return self.parent.current1.mean_value.get() / exp(value)
#     def inverse(self, value):
#         arg = self.parent.current1.mean_value.get() / value
#         return log(abs(arg))

class BMMQuadEM(QuadEM):
    _default_read_attrs = ['I0',
                           'It',
                           'Ir',
                           'Iy']
    port_name = Cpt(Signal, value='EM180')
    conf = Cpt(QuadEMPort, port_name='EM180')
    em_range  = Cpt(EpicsSignalWithRBV, 'Range', string=True)
    I0 = Cpt(Nanoize, derived_from='current1.mean_value')
    It = Cpt(Nanoize, derived_from='current2.mean_value')
    Ir = Cpt(Nanoize, derived_from='current3.mean_value')
    Iy = Cpt(Nanoize, derived_from='current4.mean_value')
    #iti0   = Cpt(Normalized, derived_from='current2.mean_value')
    #lni0it = Cpt(TransXmu,   derived_from='current2.mean_value')
    state  = Cpt(EpicsSignal, 'Acquire')
    #  = Cpt(EpicsSignal, 'PREC')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #for c in ['current{}'.format(j) for j in range(1, 5)]:
        #     getattr(self, c).read_attrs = ['mean_value']

        # self.read_attrs = ['current{}'.format(j) for j in range(1, 5)]
        self._acquisition_signal = self.acquire
        self.configuration_attrs = ['integration_time', 'averaging_time','em_range','num_averaged','values_per_read']

    def on(self):
        print('Turning {} on'.format(self.name))
        self.acquire_mode.put(0)
        self.acquire.put(1)

    def off(self):
        print('Turning {} off'.format(self.name))
        self.acquire_mode.put(2)
        self.acquire.put(0)

    def on_plan(self):
        yield from abs_set(self.acquire, 1, wait=True)
        yield from abs_set(self.acquire_mode, 0, wait=True)

    def off_plan(self):
        yield from abs_set(self.acquire, 0, wait=True)
        yield from abs_set(self.acquire_mode, 2, wait=True)




class BMMDualEM(QuadEM):
    _default_read_attrs = ['Ia',
                           'Ib']
    port_name = Cpt(Signal, value='NSLS2_IC')
    conf = Cpt(QuadEMPort, port_name='NSLS2_IC')
    em_range = Cpt(EpicsSignalWithRBV, 'Range', string=True)
    Ia = Cpt(Nanoize, derived_from='current1.mean_value')
    Ib = Cpt(Nanoize, derived_from='current2.mean_value')
    state = Cpt(EpicsSignal, 'Acquire')

    calibration_mode = Cpt(EpicsSignal, 'CalibrationMode')
    copy_adc_offsets = Cpt(EpicsSignal, 'CopyADCOffsets.PROC')
    compute_current_offset1 = Cpt(EpicsSignal, 'ComputeCurrentOffset1.PROC')
    compute_current_offset2 = Cpt(EpicsSignal, 'ComputeCurrentOffset2.PROC')

    sigma1 = Cpt(EpicsSignal, 'Current1:Sigma_RBV')
    sigma2 = Cpt(EpicsSignal, 'Current1:Sigma_RBV')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #for c in ['current{}'.format(j) for j in range(1, 5)]:
        #     getattr(self, c).read_attrs = ['mean_value']

        # self.read_attrs = ['current{}'.format(j) for j in range(1, 5)]
        self._acquisition_signal = self.acquire
        self.configuration_attrs = ['integration_time', 'averaging_time','em_range','num_averaged','values_per_read']

    def on(self):
        print('Turning {} on'.format(self.name))
        self.acquire_mode.put(0)
        self.acquire.put(1)

    def off(self):
        print('Turning {} off'.format(self.name))
        self.acquire_mode.put(2)
        self.acquire.put(0)

    def on_plan(self):
        yield from abs_set(self.acquire, 1, wait=True)
        yield from abs_set(self.acquire_mode, 0, wait=True)

    def off_plan(self):
        yield from abs_set(self.acquire, 0, wait=True)
        yield from abs_set(self.acquire_mode, 2, wait=True)

    def dark_current(self):
        reopen = shb.state.get() == shb.openval 
        if reopen:
            print('\nClosing photon shutter')
            yield from shb.close_plan()
        print('Measuring current offsets, this will take several seconds')

        ######################################################################
        # from Pete (email Feb 7, 2020):                                     #
        #   caput XF:06BM-BI{EM:3}EM180:CalibrationMode 1                    #
        #   caput XF:06BM-BI{EM:3}EM180:CopyADCOffsets.PROC 1                #
        #   caput XF:06BM-BI{EM:3}EM180:CalibrationMode 0                    #
        # ADC offset values should be around 3800, might need to hit Compute #
        # buttons to get lovely low dark current values                      #
        ######################################################################

        ## this almost works....
        self.current_offsets.ch1.put(0.0)
        self.current_offsets.ch2.put(0.0)
        self.calibration_mode.put(1)
        yield from sleep(0.5)
        self.copy_adc_offsets.put(1)
        yield from sleep(0.5)
        self.calibration_mode.put(0)
        yield from sleep(0.5)
        self.compute_current_offset1.put(1)
        self.compute_current_offset1.put(2)
        # EpicsSignal("XF:06BM-BI{EM:3}EM180:CalibrationMode", name='').put(1)
        # EpicsSignal("XF:06BM-BI{EM:3}EM180:CopyADCOffsets.PROC", name='').put(1)
        # EpicsSignal("XF:06BM-BI{EM:3}EM180:CalibrationMode", name='').put(0)
        # EpicsSignal("XF:06BM-BI{EM:1}EM180:ComputeCurrentOffset1.PROC", name='').put(1)
        # EpicsSignal("XF:06BM-BI{EM:1}EM180:ComputeCurrentOffset2.PROC", name='').put(1)
        yield from sleep(0.5)
        print(self.sigma1.get(), self.sigma2.get())
        BMM_log_info('Measured dark current on dualio ion chamber')
        if reopen:
            print('Opening photon shutter')
            yield from shb.open_plan()
            print('You are ready to measure!\n')
        
def dark_current():
    shb = user_ns['shb']
    reopen = shb.state.get() == shb.openval 
    if reopen:
        print('\nClosing photon shutter')
        yield from shb.close_plan()
    print('Measuring current offsets, this will take several seconds')
    EpicsSignal("XF:06BM-BI{EM:1}EM180:ComputeCurrentOffset1.PROC", name='').put(1)
    EpicsSignal("XF:06BM-BI{EM:1}EM180:ComputeCurrentOffset2.PROC", name='').put(1)
    EpicsSignal("XF:06BM-BI{EM:1}EM180:ComputeCurrentOffset3.PROC", name='').put(1)
    EpicsSignal("XF:06BM-BI{EM:1}EM180:ComputeCurrentOffset4.PROC", name='').put(1)
    yield from sleep(3)
    BMM_log_info('Measured dark current on quadem1')
    if reopen:
        print('Opening photon shutter')
        yield from shb.open_plan()
        print('You are ready to measure!\n')
