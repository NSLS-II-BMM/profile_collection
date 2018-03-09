from ophyd import QuadEM, Component as Cpt, EpicsSignalWithRBV, Signal


# This is cargo-culted from ophyd to fix a bug in it.
# The next release of ophyd will include a bug fix which has already
# been merged into the master branch. When it released,
# this can be deleted (and imported from ophyd instead).
class DerivedSignal(Signal):
    def __init__(self, derived_from, *, name=None, parent=None, **kwargs):
        '''A signal which is derived from another one

        Parameters
        ----------
        derived_from : Signal
            The signal from which this one is derived
        name : str, optional
            The signal name
        parent : Device, optional
            The parent device
        '''
        super().__init__(name=name, parent=parent, **kwargs)

        if isinstance(derived_from, str):
            derived_from = getattr(parent, derived_from)
        self._derived_from = derived_from
        connected = self._derived_from.connected
        if connected:
            # set up the initial timestamp reporting, if connected
            self._timestamp = self._derived_from.timestamp

        self._derived_from.subscribe(self._derived_value_callback,
                                     event_type=self.SUB_VALUE, run=connected)

    @property
    def derived_from(self):
        '''Signal that this one is derived from'''
        return self._derived_from

    def describe(self):
        '''Description based on the original signal description'''
        desc = self._derived_from.describe()[self._derived_from.name]
        desc['derived_from'] = self._derived_from.name
        return {self.name: desc}

    def _derived_value_callback(self, value=None, timestamp=None, **kwargs):
        value = self.inverse(value)
        self._run_subs(sub_type=self.SUB_VALUE, timestamp=timestamp,
                       value=value)

    def get(self, **kwargs):
        '''Get the value from the original signal'''
        value = self._derived_from.get(**kwargs)
        value = self.inverse(value)
        self._timestamp = self._derived_from.timestamp
        return value

    def inverse(self, value):
        '''Compute original signal value -> derived signal value'''
        return value

    def put(self, value, **kwargs):
        '''Put the value to the original signal'''
        value = self.forward(value)
        res = self._derived_from.put(value, **kwargs)
        self._timestamp = self._derived_from.timestamp
        return res

    def forward(self, value):
        '''Compute derived signal value -> original signal value'''
        return value

    def wait_for_connection(self, timeout=0.0):
        '''Wait for the original signal to connect'''
        return self._derived_from.wait_for_connection(timeout=timeout)

    @property
    def connected(self):
        '''Mirrors the connection state of the original signal'''
        return self._derived_from.connected

    @property
    def limits(self):
        '''Limits from the original signal'''
        return self._derived_from.limits

    def _repr_info(self):
        yield from super()._repr_info()
        yield ('derived_from', self._derived_from)



class Nanoize(DerivedSignal):
    def forward(self, value):
        return value * 1e-9
    def inverse(self, value):
        return value * 1e9

class Normalized(DerivedSignal):
    def forward(self, value):
        return value * self.parent.current1.mean_value.value
    def inverse(self, value):
        return value / self.parent.current1.mean_value.value

class BMMQuadEM(QuadEM):
    _default_read_attrs = ['current1_mean_value_nano',
                           'current2_mean_value_nano',
                           'current3_mean_value_nano',
                           'current4_mean_value_nano']
    port_name = Cpt(Signal, value='EM180')
    em_range = Cpt(EpicsSignalWithRBV, 'Range', string=True)
    current1_mean_value_nano = Cpt(Nanoize, derived_from='current1.mean_value')
    current2_mean_value_nano = Cpt(Nanoize, derived_from='current2.mean_value')
    current3_mean_value_nano = Cpt(Nanoize, derived_from='current3.mean_value')
    current4_mean_value_nano = Cpt(Nanoize, derived_from='current4.mean_value')
    iti0 = Cpt(Normalized, derived_from='current2.mean_value')
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #for c in ['current{}'.format(j) for j in range(1, 5)]:
        #     getattr(self, c).read_attrs = ['mean_value']

        # self.read_attrs = ['current{}'.format(j) for j in range(1, 5)]
        self.stage_sigs.update([(self.acquire_mode, 0), #'Single'),  # single mode
                                (self.acquire, 1)
                            ])
        self._acquisition_signal = self.acquire
        self.configuration_attrs = ['integration_time', 'averaging_time','em_range','num_averaged','values_per_read']


quadem1 = BMMQuadEM('XF:06BM-BI{EM:1}EM180:', name='quadem1')
quadem1.hints = {'fields': ['_'.join([quadem1.name, read_attr])
                            for read_attr in quadem1.read_attrs]}

