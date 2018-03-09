from ophyd import Component as Cpt, EpicsSignalWithRBV, Signal
from ophyd.scaler import EpicsScaler

scaler1 = EpicsScaler('XF:06BM-ES:1{Sclr:1}', name='scalar1')
