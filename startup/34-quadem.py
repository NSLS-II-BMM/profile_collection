from ophyd import QuadEM, Component as Cpt, EpicsSignalWithRBV, Signal, DerivedSignal, EpicsSignal
from ophyd.quadem import QuadEMPort

from numpy import log, exp

run_report(__file__)

## need to do something like this:
##    caput XF:06BM-BI{EM:1}EM180:Current3:MeanValue_RBV.PREC 7
## to get a sensible reporting precision from the Ix channels


class Nanoize(DerivedSignal):
    def forward(self, value):
        return value * 1e-9 / _locked_dwell_time.dwell_time.readback.value
    def inverse(self, value):
        return value * 1e9 * _locked_dwell_time.dwell_time.readback.value

# class Normalized(DerivedSignal):
#     def forward(self, value):
#         return value * self.parent.current1.mean_value.value
#     def inverse(self, value):
#         return value / self.parent.current1.mean_value.value

# class TransXmu(DerivedSignal):
#     def forward(self, value):
#         return self.parent.current1.mean_value.value / exp(value)
#     def inverse(self, value):
#         arg = self.parent.current1.mean_value.value / value
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
        yield from abs_set(self.acquire, 1)
        yield from abs_set(self.acquire_mode, 0)

    def off_plan(self):
        yield from abs_set(self.acquire, 0)
        yield from abs_set(self.acquire_mode, 2)


        
quadem1 = BMMQuadEM('XF:06BM-BI{EM:1}EM180:', name='quadem1')

def set_precision(pv, val):
    EpicsSignal(pv.pvname + ".PREC", name='').put(val)

set_precision(quadem1.current1.mean_value, 3)
toss = quadem1.I0.describe()
set_precision(quadem1.current2.mean_value, 3)
toss = quadem1.It.describe()
set_precision(quadem1.current3.mean_value, 3)
toss = quadem1.Ir.describe()
set_precision(quadem1.current4.mean_value, 3)
toss = quadem1.Iy.describe()


quadem1.I0.kind = 'hinted'
quadem1.It.kind = 'hinted'
quadem1.Ir.kind = 'hinted'
quadem1.Iy.kind = 'omitted'      # 'hinted'

quadem1.I0.name = 'I0'
quadem1.It.name = 'It'
quadem1.Ir.name = 'Ir'
quadem1.Iy.name = 'Iy'


#quadem1.current4_mean_value_nano.kind = 'omitted'

def dark_current():
    print('Closing photon shutter')
    yield from shb.close_plan()
    print('Measuring current offsets, this will take several seconds')
    yield from abs_set(_locked_dwell_time.quadem_dwell_time.setpoint, 2.0)
    yield from abs_set(quadem1.current_offset_calcs.ch1, 1) # is this right?
    yield from abs_set(quadem1.current_offset_calcs.ch2, 1)
    yield from abs_set(quadem1.current_offset_calcs.ch3, 1)
    yield from abs_set(quadem1.current_offset_calcs.ch4, 1)
    yield from abs_set(_locked_dwell_time.quadem_dwell_time.setpoint, 0.5)
    yield from shb.open_plan()
    print('Photon shutter is open again')

    
