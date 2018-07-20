from ophyd import PVPositionerPC, EpicsSignal, EpicsSignalRO, PseudoPositioner, PseudoSingle
from ophyd import Component as Cpt

run_report(__file__)

class QuadEMDwellTime(PVPositionerPC):
    setpoint = Cpt(EpicsSignal, 'AveragingTime')
    readback = Cpt(EpicsSignalRO, 'AveragingTime_RBV')

class StruckDwellTime(PVPositionerPC):
    setpoint = Cpt(EpicsSignal, 'TP')
    readback = Cpt(EpicsSignalRO, 'TP')

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
    md = bmm_metadata(measurement='fluorescence')
    dets  = [det]
    args  = [dets,]
    start = list(0.5*numpy.ones(len(dt)))
    stop  = list(2.5*numpy.ones(len(dt)))
    for q in zip(dt, start, stop):
        args.extend(q)
    args.append(5)              # five steps from 0.5 to 2.5
    yield from scan(*args, md=md)


class LockedDwellTimes(PseudoPositioner):
    "Sync QuadEM and Struck dwell times to one pseudo-axis dwell time."
    dwell_time = Cpt(PseudoSingle, kind='hinted')
    quadem_dwell_time = Cpt(QuadEMDwellTime, 'XF:06BM-BI{EM:1}EM180:', egu='seconds')
    struck_dwell_time = Cpt(StruckDwellTime, 'XF:06BM-ES:1{Sclr:1}.',  egu='seconds')

    @property
    def settle_time(self):
        return self.quadem_dwell_time.settle_time

    @settle_time.setter
    def settle_time(self, val):
        self.quadem_dwell_time.settle_time = val
        self.struck_dwell_time.settle_time = val

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        # logger.debug('forward %s', pseudo_pos)
        return self.RealPosition(quadem_dwell_time=pseudo_pos.dwell_time,
                                 struck_dwell_time=pseudo_pos.dwell_time)

    @real_position_argument
    def inverse(self, real_pos):
        real_pos = self.RealPosition(*real_pos)
        return self.PseudoPosition(dwell_time=real_pos.quadem_dwell_time)

_locked_dwell_time = LockedDwellTimes('', name='dwti')
dwell_time = _locked_dwell_time.dwell_time
dwell_time.name = 'inttime'
