from ophyd import PVPositionerPC, EpicsSignal, EpicsSignalRO, PseudoPositioner, PseudoSingle
from ophyd import Component as Cpt
from ophyd.pseudopos import (pseudo_position_argument, real_position_argument)

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)



class QuadEMDwellTime(PVPositionerPC):
    setpoint = Cpt(EpicsSignal,   'AveragingTime')
    readback = Cpt(EpicsSignalRO, 'AveragingTime_RBV')

class StruckDwellTime(PVPositionerPC):
    setpoint = Cpt(EpicsSignal,   'TP')
    readback = Cpt(EpicsSignalRO, 'TP')

class DualEMDwellTime(QuadEMDwellTime):
    ...
    
class IC0DwellTime(QuadEMDwellTime):
    ...

class IC1DwellTime(QuadEMDwellTime):
    ...

class IC2DwellTime(QuadEMDwellTime):
    ...
    
    
class Xspress3DwellTime(PVPositionerPC):
    setpoint = Cpt(EpicsSignal,   'det1:AcquireTime')
    readback = Cpt(EpicsSignalRO, 'det1:AcquireTime_RBV')

from BMM.user_ns.dwelltime import with_quadem, with_struck, with_xspress3 #with_dualem,
from BMM.user_ns.dwelltime import with_ic0, with_ic1, with_ic2


class LockedDwellTimes(PseudoPositioner):
    '''Sync QuadEM, Xspress3, and other dwell times to one pseudo-axis
    dwell time.  These signal chains are enabled/disabled in
    BMM/user_ns/dwelltime.py.  Those global parameters are imported
    just above and used to set attributes of the class.  In this way,
    only the enabled signal chains will be set, but ALL of the enabled
    signal chains will be set.
    '''
    dwell_time = Cpt(PseudoSingle, kind='hinted')
    if with_quadem is True:
        quadem_dwell_time = Cpt(QuadEMDwellTime, 'XF:06BM-BI{EM:1}EM180:', egu='seconds') # main ion chambers
    if with_struck is True:
        struck_dwell_time = Cpt(StruckDwellTime, 'XF:06BM-ES:1{Sclr:1}.',  egu='seconds') # analog detector readout
    #if with_dualem is True:
    #    dualem_dwell_time = Cpt(DualEMDwellTime, 'XF:06BM-BI{EM:3}EM180:', egu='seconds') # new I0 chamber
    if with_ic0 is True:
        ic0_dwell_time = Cpt(IC0DwellTime, 'XF:06BM-BI{IC:0}EM180:', egu='seconds') # new I0 chamber
    if with_ic1 is True:
        ic1_dwell_time = Cpt(IC1DwellTime, 'XF:06BM-BI{IC:1}EM180:', egu='seconds') # new It chamber
    if with_ic2 is True:
        ic2_dwell_time = Cpt(IC2DwellTime, 'XF:06BM-BI{IC:2}EM180:', egu='seconds') # new Ir chamber
    if with_xspress3 is True:
        xspress3_dwell_time = Cpt(Xspress3DwellTime, 'XF:06BM-ES{Xsp:1}:', egu='seconds') # Xspress3
    
    @property
    def settle_time(self):
        return self.quadem_dwell_time.settle_time

    @settle_time.setter
    def settle_time(self, val):
        if hasattr(self, 'quadem_dwell_time'):
            self.quadem_dwell_time.settle_time = val
        if hasattr(self, 'struck_dwell_time'):
            self.struck_dwell_time.settle_time = val
        #if hasattr(self, 'dualem_dwell_time'):
        #    self.dualem_dwell_time.settle_time = val
        if hasattr(self, 'ic0_dwell_time'):
            self.ic0_dwell_time.settle_time = val
        if hasattr(self, 'ic1_dwell_time'):
            self.ic1_dwell_time.settle_time = val
        if hasattr(self, 'ic2_dwell_time'):
            self.ic2_dwell_time.settle_time = val
        if hasattr(self, 'xspress3_dwell_time'):
            self.xspress3_dwell_time.settle_time = val

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        #pseudo_pos = self.PseudoPosition(*pseudo_pos)
        #print('forward %s'% pseudo_pos)

        # signal chains are enabled/disabled in BMM/user_ns/dwelltime.py
        # see above
        # only talk to the signal chains that are enabled, so construct
        # a dict, then unpack it as keyword arguments in self.RealPosition
        signal_chains = {}
        if hasattr(self, 'quadem_dwell_time'):
            signal_chains['quadem_dwell_time'] = pseudo_pos.dwell_time
        if hasattr(self, 'struck_dwell_time'):
            signal_chains['struck_dwell_time'] = pseudo_pos.dwell_time
        #if hasattr(self, 'dualem_dwell_time'):
        #    signal_chains['dualem_dwell_time'] = pseudo_pos.dwell_time
        if hasattr(self, 'ic0_dwell_time'):
            signal_chains['ic0_dwell_time'] = pseudo_pos.dwell_time
        if hasattr(self, 'ic1_dwell_time'):
            signal_chains['ic1_dwell_time'] = pseudo_pos.dwell_time
        if hasattr(self, 'ic2_dwliell_time'):
            signal_chains['ic2_dwell_time'] = pseudo_pos.dwell_time
        if hasattr(self, 'xspress3_dwell_time'):
            signal_chains['xspress3_dwell_time'] = pseudo_pos.dwell_time

        return self.RealPosition(**signal_chains)

        ## how I used to do this....
        # if 'xspress3_dwell_time' in self.read_attrs and 'dualem_dwell_time' in self.read_attrs:
        #     return self.RealPosition(
        #         quadem_dwell_time=pseudo_pos.dwell_time,
        #         #struck_dwell_time=pseudo_pos.dwell_time,
        #         dualem_dwell_time=pseudo_pos.dwell_time,
        #         xspress3_dwell_time=pseudo_pos.dwell_time,
        #     )
            
    @real_position_argument
    def inverse(self, real_pos):
        #real_pos = self.RealPosition(*real_pos)
        return self.PseudoPosition(dwell_time=real_pos.quadem_dwell_time)
