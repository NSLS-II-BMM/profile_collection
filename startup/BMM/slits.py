from ophyd import (EpicsMotor, PseudoPositioner, PseudoSingle, Component as Cpt, EpicsSignal, EpicsSignalRO)
from ophyd.pseudopos import (pseudo_position_argument,
                             real_position_argument)

from bluesky.plan_stubs import abs_set, sleep, mv, null

from BMM.functions import boxedtext
from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper


class Slits(PseudoPositioner):
    def __init__(self, *args, **kwargs):
        #self.width = mirror_length
        #self.senter  = mirror_width
        self.nominal = [7.0, 1.0, 0.0, 0.0] # hsize, vsize, hcenter, vcenter
        super().__init__(*args, **kwargs)

    def where(self):
        #print("%s:" % self.name.upper())
        text = "      vertical   size   = %7.3f mm            Top      = %7.3f mm\n" % \
               (self.vsize.readback.get(),   self.top.user_readback.get())
        text += "      vertical   center = %7.3f mm            Bottom   = %7.3f mm\n" % \
                (self.vcenter.readback.get(), self.bottom.user_readback.get())
        text += "      horizontal size   = %7.3f mm            Outboard = %7.3f mm\n" % \
                (self.hsize.readback.get(),   self.outboard.user_readback.get())
        text += "      horizontal center = %7.3f mm            Inboard  = %7.3f mm" % \
                (self.hcenter.readback.get(), self.inboard.user_readback.get())
        return text
    def wh(self):
        boxedtext(self.name, self.where(), 'cyan')

    #def enable(self):
    #    dm3_slits_t.enable()
    #    dm3_slits_b.enable()
    #    dm3_slits_i.enable()
    #    dm3_slits_o.enable()

    # The pseudo positioner axes:
    vsize   = Cpt(PseudoSingle, limits=(-15, 20))
    vcenter = Cpt(PseudoSingle, limits=(-15, 10))
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




class GonioSlits(PseudoPositioner):
    '''Note that the parity of the bottom and inboard slits are different
    than for all the other slits on the beamline.  For these slits,
    the positive direction is away from the center of the slits for all
    four blades.'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def where(self):
        #print("%s:" % self.name.upper())
        text = "      vertical   size   = %7.3f mm            Top      = %7.3f mm\n" % \
               (self.vsize.readback.get(),   self.top.user_readback.get())
        text += "      vertical   center = %7.3f mm            Bottom   = %7.3f mm\n" % \
                (self.vcenter.readback.get(), self.bottom.user_readback.get())
        text += "      horizontal size   = %7.3f mm            Outboard = %7.3f mm\n" % \
                (self.hsize.readback.get(),   self.outboard.user_readback.get())
        text += "      horizontal center = %7.3f mm            Inboard  = %7.3f mm" % \
                (self.hcenter.readback.get(), self.inboard.user_readback.get())
        return text
    def wh(self):
        boxedtext(self.name, self.where(), 'cyan')

    # The pseudo positioner axes:
    vsize   = Cpt(PseudoSingle, limits=(-15, 20))
    vcenter = Cpt(PseudoSingle, limits=(-15, 10))
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
        return self.RealPosition(top      = pseudo_pos.vsize/2 + pseudo_pos.vcenter,
                                 bottom   = pseudo_pos.vsize/2 - pseudo_pos.vcenter,
                                 outboard = pseudo_pos.hsize/2 + pseudo_pos.hcenter,
                                 inboard  = pseudo_pos.hsize/2 - pseudo_pos.hcenter
                             )

    @real_position_argument
    def inverse(self, real_pos):
        '''Run an inverse (real -> pseudo) calculation'''
        return self.PseudoPosition(hsize   =  real_pos.outboard + real_pos.inboard,
                                   hcenter = (real_pos.outboard - real_pos.inboard)/2,
                                   vsize   =  real_pos.top      + real_pos.bottom,
                                   vcenter = (real_pos.top      - real_pos.bottom )/2,
        ) ##                                                    ^
          ## note different +/- signs here compared to Slits __/ 

def recover_slits2():
    dm2_slits_t, dm2_slits_b, dm2_slits_i, dm2_slits_o = user_ns['dm2_slits_t'], user_ns['dm2_slits_b'], user_ns['dm2_slits_i'], user_ns['dm2_slits_o']
    yield from abs_set(dm2_slits_t.home_signal, 1)
    yield from abs_set(dm2_slits_i.home_signal, 1)
    yield from sleep(1.0)
    print('Begin homing %s motors:\n' % slits2.name)
    hvalues = (dm2_slits_t.hocpl.get(), dm2_slits_b.hocpl.get(), dm2_slits_i.hocpl.get(), dm2_slits_o.hocpl.get())
    while any(v == 0 for v in hvalues):
        hvalues = (dm2_slits_t.hocpl.get(), dm2_slits_b.hocpl.get(), dm2_slits_i.hocpl.get(), dm2_slits_o.hocpl.get())
        strings = ['top', 'bottom', 'inboard', 'outboard']
        for i,v in enumerate(hvalues):
            strings[i] = go_msg(strings[i]) if hvalues[i] == 1 else error_msg(strings[i])
        print('  '.join(strings), end='\r')
        yield from sleep(1.0)
    print('\n')
    yield from mv(slits2.hsize,   slits2.nominal[0])
    yield from mv(slits2.vsize,   slits2.nominal[1])
    yield from mv(slits2.hcenter, slits2.nominal[2])
    yield from mv(slits2.vcenter, slits2.nominal[3])

def recover_slits3():
    dm3_slits_t, dm3_slits_b, dm3_slits_i, dm3_slits_o = user_ns['dm3_slits_t'], user_ns['dm3_slits_b'], user_ns['dm3_slits_i'], user_ns['dm3_slits_o']
    yield from abs_set(dm3_slits_t.home_signal, 1)
    yield from abs_set(dm3_slits_i.home_signal, 1)
    yield from sleep(1.0)
    print('Begin homing %s motors:\n' % slits3.name)
    hvalues = (dm3_slits_t.hocpl.get(), dm3_slits_b.hocpl.get(), dm3_slits_i.hocpl.get(), dm3_slits_o.hocpl.get())
    while any(v == 0 for v in hvalues):
        hvalues = (dm3_slits_t.hocpl.get(), dm3_slits_b.hocpl.get(), dm3_slits_i.hocpl.get(), dm3_slits_o.hocpl.get())
        strings = ['top', 'bottom', 'inboard', 'outboard']
        for i,v in enumerate(hvalues):
            strings[i] = go_msg(strings[i]) if hvalues[i] == 1 else error_msg(strings[i])
        print('  '.join(strings), end='\r')
        yield from sleep(1.0)
    print('\n')
    yield from mv(slits3.hsize,   slits3.nominal[0])
    yield from mv(slits3.vsize,   slits3.nominal[1])
    yield from mv(slits3.hcenter, slits3.nominal[2])
    yield from mv(slits3.vcenter, slits3.nominal[3])

