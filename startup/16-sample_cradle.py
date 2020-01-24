from ophyd import (EpicsMotor, PseudoPositioner, PseudoSingle, Component as Cpt, EpicsSignal, EpicsSignalRO)
from ophyd.pseudopos import (pseudo_position_argument, real_position_argument)
import bluesky.plan_stubs as bps

run_report(__file__)

class Cradle(PseudoPositioner):
    def __init__(self, *args, **kwargs):
        #self.width = mirror_length
        #self.senter  = mirror_width
        self.nominal = [7.0, 1.0, 0.0, 0.0] # hposition, vposition, htilt, vtilt
        super().__init__(*args, **kwargs)
    def where(self):
        #print("%s:" % self.name.upper())
        text  = "      Y  = %7.3f mm       yout (xafs_lins) = %7.3f mm\n" % (self.y.readback.value,  self.yout.user_readback.value)
        text += "      Dy = %7.3f mm       yin  (xafs_y)    = %7.3f mm\n" % (self.dy.readback.value, self.yin.user_readback.value)
        #text += "      X  = %7.3f mm       xout (xafs_lins)  = %7.3f mm\n" % (self.x.readback.value,  self.xout.user_readback.value)
        #text += "      Dx = %7.3f mm       xin  (xafs_x)     = %7.3f mm"   % (self.dx.readback.value, self.xin.user_readback.value)
        return text
    def wh(self):
        boxedtext(self.name, self.where(), 'cyan', width=80)

    # The pseudo positioner axes:
    lim = xafs_y.limits         # this is not quite right....
    y  = Cpt(PseudoSingle, limits=lim)
    dy = Cpt(PseudoSingle, limits=(-0.25, 0.25))

    #lim = xafs_x.limits
    #x  = Cpt(PseudoSingle, limits=lim)
    #dx = Cpt(PseudoSingle, limits=(-0.25, 0.25))

    # The real (or physical) positioners:
    yout = Cpt(EpicsMotor, 'LinS}Mtr')
    yin  = Cpt(EpicsMotor, 'LinY}Mtr')
    #xout = Cpt(EpicsMotor, 'Mtr8}Mtr')
    #xin  = Cpt(EpicsMotor, 'LinX}Mtr')

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        '''Run a forward (pseudo -> real) calculation'''
        return self.RealPosition(yout = pseudo_pos.y + pseudo_pos.dy,
                                 yin  = pseudo_pos.y - pseudo_pos.dy,
                                 #xout = pseudo_pos.x + pseudo_pos.dx,
                                 #xin  = pseudo_pos.x - pseudo_pos.dx
                             )

    @real_position_argument
    def inverse(self, real_pos):
        '''Run an inverse (real -> pseudo) calculation'''
        return self.PseudoPosition(y  = (real_pos.yout + real_pos.yin)/2,
                                   dy = (real_pos.yout - real_pos.yin)/2,
                                   #x  = (real_pos.xout + real_pos.xin)/2,
                                   #dx = (real_pos.xout - real_pos.xin)/2 
                               )


xafs_lins.user_offset.put(27.477)
#xafs_linxs.user_offset.put(234.625)
cradle = Cradle('XF:06BMA-BI{XAFS-Ax:',  name='cradle')

def set_cradle_offset(motor=xafs_lins):
    motor.user_offset.put(motor.user_offset.value - (motor.user_readback.value - xafs_liny.user_readback.value))

def exercise_cradle(n=5):
    yield from mvr(cradle.y,    n)
    yield from mvr(cradle.y, -1*n)
    


def crplan(slp=2):
    while vor.names.name29.value.lower() != 'ready':
        print('sleeping for %s seconds' % slp)
        yield from bps.sleep(slp)
    yield from exercise_cradle()
