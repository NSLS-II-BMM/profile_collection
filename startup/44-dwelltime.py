from ophyd import PVPositionerPC, EpicsSignal, EpicsSignalRO, PseudoPositioner, PseudoSingle
from ophyd import Component as Cpt

class QuadEMDwellTime(PVPositionerPC):
    setpoint = Cpt(EpicsSignal, 'AveragingTime')
    readback = Cpt(EpicsSignalRO, 'AveragingTime_RBV')

quadem_dwell_time = QuadEMDwellTime('XF:06BM-BI{EM:1}EM180:', name='quadem_dwell_time', egu='seconds')

class StruckDwellTime(PVPositionerPC):
    setpoint = Cpt(EpicsSignal, 'TP')
    readback = Cpt(EpicsSignalRO, 'TP')

struck_dwell_time = StruckDwellTime('XF:06BM-ES:1{Sclr:1}.', name='struck_dwell_time', egu='seconds')

####################################################################################################

## see
## http://nsls-ii.github.io/bluesky/tutorial.html#scan-multiple-motors-together
## for an explanation of the calling syntax for a bluesky scan plan
## the order of arguments is a bit confusing, this zips and flattens the arguments
## so that this test can call any number of dwelltime PVPositioner-s

## RE(test_dwelltimes([quadem_dwell_time,struck_dwell_time]))

from ophyd.sim import det
from bluesky.plans import scan
import bluesky.plan_stubs as bps
def test_dwelltimes(dt, md=None):
    dets  = [det]
    args  = [dets,]
    start = list(0.5*numpy.ones(len(dt)))
    stop  = list(2.5*numpy.ones(len(dt)))
    for q in zip(dt, start, stop):
        args.extend(q)
    args.append(5)              # five steps from 0.5 to 2.5
    yield from scan(*args, md=md)
