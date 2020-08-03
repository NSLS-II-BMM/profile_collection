from ophyd import PVPositionerPC, EpicsSignal, EpicsSignalRO, PseudoPositioner, PseudoSingle
from ophyd import Component as Cpt
from ophyd.pseudopos import (pseudo_position_argument,
                             real_position_argument)
from BMM.metadata import bmm_metadata

class QuadEMDwellTime(PVPositionerPC):
    setpoint = Cpt(EpicsSignal,   'AveragingTime')
    readback = Cpt(EpicsSignalRO, 'AveragingTime_RBV')

class StruckDwellTime(PVPositionerPC):
    setpoint = Cpt(EpicsSignal,   'TP')
    readback = Cpt(EpicsSignalRO, 'TP')

class DualEMDwellTime(PVPositionerPC):
    setpoint = Cpt(EpicsSignal,   'AveragingTime')
    readback = Cpt(EpicsSignalRO, 'AveragingTime_RBV')
    
class Xspress3DwellTime(PVPositionerPC):
    setpoint = Cpt(EpicsSignal,   'AcquireTime')
    readback = Cpt(EpicsSignalRO, 'AcquireTime_RBV')
    
####################################################################################################

## see
## http://nsls-ii.github.io/bluesky/tutorial.html#scan-multiple-motors-together
## for an explanation of the calling syntax for a bluesky scan plan
## the order of arguments is a bit confusing, this zips and flattens the arguments
## so that this test can call any number of dwelltime PVPositioner-s

## RE(test_dwelltimes([quadem_dwell_time,struck_dwell_time]))

from IPython import get_ipython
user_ns = get_ipython().user_ns


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
    "Sync QuadEM, Struck, DualEM, and Xspress3 dwell times to one pseudo-axis dwell time."
    dwell_time = Cpt(PseudoSingle, kind='hinted')
    if user_ns['with_quadem'] is True:
        quadem_dwell_time = Cpt(QuadEMDwellTime, 'XF:06BM-BI{EM:1}EM180:', egu='seconds') # main ion chambers
    if user_ns['with_struck'] is True:
        struck_dwell_time = Cpt(StruckDwellTime, 'XF:06BM-ES:1{Sclr:1}.',  egu='seconds') # analog detector readout
    if user_ns['with_dualem'] is True:
        dualem_dwell_time = Cpt(DualEMDwellTime, 'XF:06BM-BI{EM:3}EM180:', egu='seconds') # new I0 chamber
    if user_ns['with_xspress3'] is True:
        xspress3_dwell_time = Cpt(Xspress3DwellTime, 'XF:06BM-ES{Xsp:1}:', egu='seconds') # Xspress3
    
    @property
    def settle_time(self):
        return self.quadem_dwell_time.settle_time

    @settle_time.setter
    def settle_time(self, val):
        if 'quadem_dwell_time' in self.read_attrs:
            self.quadem_dwell_time.settle_time = val
        if 'struck_dwell_time' in self.read_attrs:
            self.struck_dwell_time.settle_time = val
        if 'dualem_dwell_time' in self.read_attrs:
            self.dualem_dwell_time.settle_time = val
        if 'xspress3_dwell_time' in self.read_attrs:
            self.xspress3_dwell_time.settle_time = val

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        #pseudo_pos = self.PseudoPosition(*pseudo_pos)
        #print('forward %s'% pseudo_pos)
        if 'xspress3_dwell_time' in self.read_attrs and 'dualem_dwell_time' in self.read_attrs:
            return self.RealPosition(
                quadem_dwell_time=pseudo_pos.dwell_time,
                struck_dwell_time=pseudo_pos.dwell_time,
                dualem_dwell_time=pseudo_pos.dwell_time,
                xspress3_dwell_time=pseudo_pos.dwell_time,
            )
        elif 'xspress3_dwell_time' in self.read_attrs:
            return self.RealPosition(
                quadem_dwell_time=pseudo_pos.dwell_time,
                struck_dwell_time=pseudo_pos.dwell_time,
                xspress3_dwell_time=pseudo_pos.dwell_time,
            )
        elif 'dualem_dwell_time' in self.read_attrs:
            return self.RealPosition(
                quadem_dwell_time=pseudo_pos.dwell_time,
                struck_dwell_time=pseudo_pos.dwell_time,
                dualem_dwell_time=pseudo_pos.dwell_time,
            )
        else:
            return self.RealPosition(
                quadem_dwell_time=pseudo_pos.dwell_time,
                struck_dwell_time=pseudo_pos.dwell_time,
            )
            

    @real_position_argument
    def inverse(self, real_pos):
        #real_pos = self.RealPosition(*real_pos)
        return self.PseudoPosition(dwell_time=real_pos.quadem_dwell_time)
