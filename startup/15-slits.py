from ophyd import (EpicsMotor, PseudoPositioner, PseudoSingle, Component as Cpt, EpicsSignal, EpicsSignalRO)
from ophyd.pseudopos import (pseudo_position_argument,
                             real_position_argument)


class Slits(PseudoPositioner):
    def __init__(self, *args, **kwargs):
        #self.width = mirror_length
        #self.senter  = mirror_width
        super().__init__(*args, **kwargs)

    def where(self):
        print("%s:" % self.name.upper())
        print("\tvertical   size   = %7.3f mm\t\tTop      = %7.3f" % (self.vsize.readback.value,   self.top.user_readback.value))
        print("\tvertical   center = %7.3f mm\t\tBottom   = %7.3f" % (self.vcenter.readback.value, self.bottom.user_readback.value))
        print("\thorizontal size   = %7.3f mm\t\tOutboard = %7.3f" % (self.hsize.readback.value,   self.outboard.user_readback.value))
        print("\thorizontal center = %7.3f mm\t\tInboard  = %7.3f" % (self.hcenter.readback.value, self.inboard.user_readback.value))
    def wh(self):
        self.where()
        
    # The pseudo positioner axes:
    vsize   = Cpt(PseudoSingle, limits=(-10, 20))
    vcenter = Cpt(PseudoSingle, limits=(-10, 10))
    hsize   = Cpt(PseudoSingle, limits=(-1, 20))
    hcenter = Cpt(PseudoSingle, limits=(-10, 10))

    # The real (or physical) positioners:
    top      = Cpt(EpicsMotor, 'T}Mtr')
    bottom   = Cpt(EpicsMotor, 'B}Mtr')
    inboard  = Cpt(EpicsMotor, 'I}Mtr')
    outboard = Cpt(EpicsMotor, 'O}Mtr')

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        '''Run a forward (pseudo -> real) calculation'''
        return self.RealPosition(top      = pseudo_pos.vcenter + pseudo_pos.vsize/2,
                                 bottom   = pseudo_pos.vcenter - pseudo_pos.vsize/2,
                                 outboard = pseudo_pos.hcenter + pseudo_pos.hsize/2,
                                 inboard  = pseudo_pos.hcenter - pseudo_pos.hsize/2
            )
    
    @real_position_argument
    def inverse(self, real_pos):
        '''Run an inverse (real -> pseudo) calculation'''
        return self.PseudoPosition(hsize   =  real_pos.outboard - real_pos.inboard,
                                   hcenter = (real_pos.outboard + real_pos.inboard)/2,
                                   vsize   =  real_pos.top      - real_pos.bottom,
                                   vcenter = (real_pos.top      + real_pos.bottom )/2,
                                   
        )
        


slits3 = Slits('XF:06BM-BI{Slt:02-Ax:',  name='slits3')
slits2 = Slits('XF:06BM-OP{Slt:01-Ax:',  name='slits2')
