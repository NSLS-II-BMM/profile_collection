from ophyd import (EpicsMotor, PseudoPositioner, PseudoSingle, Component as Cpt, EpicsSignal, EpicsSignalRO)
from ophyd.pseudopos import (pseudo_position_argument,
                             real_position_argument)

run_report(__file__)


## harmonic rejection mirror
m3_yu     = EpicsMotor('XF:06BMA-OP{Mir:M3-Ax:YU}Mtr',   name='m3_yu')
m3_ydo    = EpicsMotor('XF:06BMA-OP{Mir:M3-Ax:YDO}Mtr',  name='m3_ydo')
m3_ydi    = EpicsMotor('XF:06BMA-OP{Mir:M3-Ax:YDI}Mtr',  name='m3_ydi')
m3_xu     = EpicsMotor('XF:06BMA-OP{Mir:M3-Ax:XU}Mtr',   name='m3_xu')
m3_xd     = EpicsMotor('XF:06BMA-OP{Mir:M3-Ax:XD}Mtr',   name='m3_xd')



from numpy import tan, arctan2


class Mirrors(PseudoPositioner):
    def __init__(self, *args, mirror_length, mirror_width, **kwargs):
        self.mirror_length = mirror_length
        self.mirror_width  = mirror_width
        super().__init__(*args, **kwargs)

    def _done_moving(self, *args, **kwargs):
        ## this method is originally defined as Positioner, a base class of EpicsMotor
        ## tack on instructions for killing the motor after movement
        super()._done_moving(*args, **kwargs)
        self.xd.kill_cmd.put(1)
        self.xu.kill_cmd.put(1)

    def where(self):
        print("%s:" % self.name.upper())
        print("\tvertical = %7.3f mm\t\tYU  = %7.3f"   % (self.vertical.readback.value, self.yu.user_readback.value))
        print("\tlateral  = %7.3f mm\t\tYDO = %7.3f"   % (self.lateral.readback.value,  self.ydo.user_readback.value))
        print("\tpitch    = %7.3f mrad\t\tYDI = %7.3f" % (self.pitch.readback.value,    self.ydi.user_readback.value))
        print("\troll     = %7.3f mrad\t\tXU  = %7.3f" % (self.roll.readback.value,     self.xu.user_readback.value))
        print("\tyaw      = %7.3f mrad\t\tXD  = %7.3f" % (self.yaw.readback.value,      self.xd.user_readback.value))
    def wh(self):
        self.where()

    # The pseudo positioner axes:
    vertical = Cpt(PseudoSingle, limits=(-8, 8))
    lateral  = Cpt(PseudoSingle, limits=(-16, 16))
    pitch    = Cpt(PseudoSingle, limits=(-5.5, 5.5))
    roll     = Cpt(PseudoSingle, limits=(-3, 3))
    yaw      = Cpt(PseudoSingle, limits=(-3, 3))


    # The real (or physical) positioners:
    yu  = Cpt(EpicsMotor, 'YU}Mtr')
    ydo = Cpt(EpicsMotor, 'YDO}Mtr')
    ydi = Cpt(EpicsMotor, 'YDI}Mtr')
    xu  = Cpt(VacuumEpicsMotor, 'XU}Mtr')
    xd  = Cpt(VacuumEpicsMotor, 'XD}Mtr')

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        '''Run a forward (pseudo -> real) calculation'''
        return self.RealPosition(xu  = pseudo_pos.lateral  - 0.5 * self.mirror_length * tan(pseudo_pos.yaw   / 1000),
                                 xd  = pseudo_pos.lateral  + 0.5 * self.mirror_length * tan(pseudo_pos.yaw   / 1000),

                                 yu  = pseudo_pos.vertical - 0.5 * self.mirror_length * tan(pseudo_pos.pitch / 1000),
                                 ydo = pseudo_pos.vertical + 0.5 * self.mirror_length * tan(pseudo_pos.pitch / 1000) + 0.5 * self.mirror_width * tan(pseudo_pos.roll/1000),
                                 ydi = pseudo_pos.vertical + 0.5 * self.mirror_length * tan(pseudo_pos.pitch / 1000) - 0.5 * self.mirror_width * tan(pseudo_pos.roll/1000)
                                 )

    @real_position_argument
    def inverse(self, real_pos):
        '''Run an inverse (real -> pseudo) calculation'''
        return self.PseudoPosition(lateral  = (real_pos.xu + real_pos.xd) / 2,
                                   yaw      = 1000*arctan2( real_pos.xd  - real_pos.xu,                    self.mirror_length),

                                   vertical = (real_pos.yu + (real_pos.ydo + real_pos.ydi) / 2 ) / 2,
                                   pitch    = 1000*arctan2( (real_pos.ydo + real_pos.ydi)/2 - real_pos.yu, self.mirror_length),
                                   roll     = 1000*arctan2( real_pos.ydo - real_pos.ydi,                   self.mirror_width ))




m1 = Mirrors('XF:06BM-OP{Mir:M1-Ax:',  name='m1', mirror_length=556,  mirror_width=240)
m1.vertical._limits = (-5.0, 5.0)
m1.lateral._limits  = (-5.0, 5.0)
m1.pitch._limits    = (-5.0, 5.0)
m1.roll._limits     = (-5.0, 5.0)
m1.yaw._limits      = (-5.0, 5.0)

m2 = Mirrors('XF:06BMA-OP{Mir:M2-Ax:', name='m2', mirror_length=1288, mirror_width=240)
m2.vertical._limits = (-6.0, 8.0)
m2.lateral._limits  = (-2, 2)
m2.pitch._limits    = (-0.5, 5.0)
m2.roll._limits     = (-2, 2)
m2.yaw._limits      = (-1, 1)

m3 = Mirrors('XF:06BMA-OP{Mir:M3-Ax:', name='m3', mirror_length=667,  mirror_width=240)
m3.vertical._limits = (-9, 1)
m3.lateral._limits  = (-16, 16)
m3.pitch._limits    = (-1, 6)
m3.roll._limits     = (-2, 2)
m3.yaw._limits      = (-1, 1)



class XAFSTable(PseudoPositioner):
    def __init__(self, *args, mirror_length, mirror_width, **kwargs):
        self.mirror_length = mirror_length
        self.mirror_width  = mirror_width
        super().__init__(*args, **kwargs)

    def where(self):
        print("%s:" % self.name.upper())
        print("\tvertical = %7.3f mm\t\tYU  = %7.3f"   % (self.vertical.readback.value, self.yu.user_readback.value))
        print("\tpitch    = %7.3f mrad\t\tYDO = %7.3f" % (self.pitch.readback.value,    self.ydo.user_readback.value))
        print("\troll     = %7.3f mrad\t\tYDI = %7.3f" % (self.roll.readback.value,     self.ydi.user_readback.value))
    def wh(self):
        self.where()

    # The pseudo positioner axes:
    vertical = Cpt(PseudoSingle, limits=(5, 145))
    pitch    = Cpt(PseudoSingle, limits=(-8, 1))
    roll     = Cpt(PseudoSingle, limits=(5, 5))


    # The real (or physical) positioners:
    yu  = Cpt(EpicsMotor, 'YU}Mtr')
    ydo = Cpt(EpicsMotor, 'YDO}Mtr')
    ydi = Cpt(EpicsMotor, 'YDI}Mtr')

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        '''Run a forward (pseudo -> real) calculation'''
        return self.RealPosition(yu  = pseudo_pos.vertical - 0.5 * self.mirror_length * tan(pseudo_pos.pitch / 1000),
                                 ydo = pseudo_pos.vertical + 0.5 * self.mirror_length * tan(pseudo_pos.pitch / 1000) + 0.5 * self.mirror_width * tan(pseudo_pos.roll/1000),
                                 ydi = pseudo_pos.vertical + 0.5 * self.mirror_length * tan(pseudo_pos.pitch / 1000) - 0.5 * self.mirror_width * tan(pseudo_pos.roll/1000)
                                 )

    @real_position_argument
    def inverse(self, real_pos):
        '''Run an inverse (real -> pseudo) calculation'''
        return self.PseudoPosition(vertical = (real_pos.yu + (real_pos.ydo + real_pos.ydi) / 2 ) / 2,
                                   pitch    = 1000*arctan2( (real_pos.ydo + real_pos.ydi)/2 - real_pos.yu, self.mirror_length),
                                   roll     = 1000*arctan2( real_pos.ydo - real_pos.ydi,                   self.mirror_width ))




xafs_table = XAFSTable('XF:06BMA-BI{XAFS-Ax:Tbl_', name='xafs_table', mirror_length=1160,  mirror_width=558)


class GonioTable(PseudoPositioner):
    def __init__(self, *args, mirror_length, mirror_width, **kwargs):
        self.mirror_length = mirror_length
        self.mirror_width  = mirror_width
        super().__init__(*args, **kwargs)

    def where(self):
        print("%s:" % self.name.upper())
        print("\tvertical = %7.3f mm\t\tYUO = %7.3f"   % (self.vertical.readback.value, self.yuo.user_readback.value))
        print("\tpitch    = %7.3f mrad\t\tYUI = %7.3f" % (self.pitch.readback.value,    self.yui.user_readback.value))
        print("\troll     = %7.3f mrad\t\tYD  = %7.3f" % (self.roll.readback.value,     self.yd.user_readback.value))
    def wh(self):
        self.where()

    # The pseudo positioner axes:
    vertical = Cpt(PseudoSingle, limits=(291, 412))
    pitch    = Cpt(PseudoSingle, limits=(-8, 1))
    roll     = Cpt(PseudoSingle, limits=(5, 5))


    # The real (or physical) positioners:
    yui = Cpt(EpicsMotor, 'YUI}Mtr')
    yuo = Cpt(EpicsMotor, 'YUO}Mtr')
    yd  = Cpt(EpicsMotor, 'YD}Mtr')

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        '''Run a forward (pseudo -> real) calculation'''
        return self.RealPosition(yd  = pseudo_pos.vertical + 0.5 * self.mirror_length * tan(pseudo_pos.pitch / 1000),
                                 yuo = pseudo_pos.vertical - 0.5 * self.mirror_length * tan(pseudo_pos.pitch / 1000) + 0.5 * self.mirror_width * tan(pseudo_pos.roll/1000),
                                 yui = pseudo_pos.vertical - 0.5 * self.mirror_length * tan(pseudo_pos.pitch / 1000) - 0.5 * self.mirror_width * tan(pseudo_pos.roll/1000)
                                 )

    @real_position_argument
    def inverse(self, real_pos):
        '''Run an inverse (real -> pseudo) calculation'''
        return self.PseudoPosition(vertical = (real_pos.yd + (real_pos.yuo + real_pos.yui) / 2 ) / 2,
                                   pitch    = 1000*arctan2( real_pos.yd - (real_pos.yuo + real_pos.yui)/2, self.mirror_length),
                                   roll     = 1000*arctan2( real_pos.yuo - real_pos.yui,                   self.mirror_width ))


gonio_table = GonioTable('XF:06BM-ES{SixC-Ax:Tbl_', name='gonio_table', mirror_length=1117.6,  mirror_width=711.12)
