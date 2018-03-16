from ophyd import (EpicsMotor, PseudoPositioner, PseudoSingle, Component as Cpt, EpicsSignal, EpicsSignalRO)
from ophyd.pseudopos import (pseudo_position_argument,
                             real_position_argument)

from numpy import pi, sin, cos, arcsin

#from colorama import Fore, Back, Style

HBARC = 1973.27053324

class DCM(PseudoPositioner):
    def __init__(self, *args, crystal='111', mode='fixed', offset=30, **kwargs):
        self.crystal = crystal
        self.offset  = offset
        self.mode    = mode
        super().__init__(*args, **kwargs)

    @property
    def _pseudo_channel_cut(self):
        if self.mode is 'channelcut':
            return 1
        else:
            return 0

    @property
    def _twod(self):
        if self.crystal is '311':
            return 2*1.63761489
        else:
            return 2*3.13597211

    def _done_moving(self, *args, **kwargs):
        ## this method is originally defined as Positioner, a base class of EpicsMotor
        ## tack on instructions for killing the motor after movement
        super()._done_moving(*args, **kwargs)
        self.para.kill_cmd.put(1)
        self.perp.kill_cmd.put(1)

    def where(self):
        print("%s = %.1f   %s = Si(%s)" % \
            ('Energy', self.energy.readback.value,
             'reflection', self.crystal))
        print("%s: %s = %8.5f   %s = %7.4f   %s = %8.4f" %\
            ('current',
             'Bragg', self.bragg.user_readback.value,
             '2nd Xtal Perp',  self.perp.user_readback.value,
             '2nd Xtal Para',  self.para.user_readback.value))

        
    # The pseudo positioner axes:
    energy   = Cpt(PseudoSingle, limits=(4000, 25000))

    
    # The real (or physical) positioners:
    bragg = Cpt(BraggEpicsMotor, 'Bragg}Mtr')
    para  = Cpt(VacuumEpicsMotor, 'Par2}Mtr')
    perp  = Cpt(VacuumEpicsMotor, 'Per2}Mtr')

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        '''Run a forward (pseudo -> real) calculation'''
        wavelength = 2*pi*HBARC / pseudo_pos.energy
        angle = arcsin(wavelength / self._twod)
        if self._pseudo_channel_cut:
            return self.RealPosition(bragg = 180 * arcsin(wavelength/self._twod) / pi,
                                     para  = self.para.user_readback.value,
                                     perp  = self.perp.user_readback.value)
        else:
            return self.RealPosition(bragg = 180 * arcsin(wavelength/self._twod) / pi,
                                     para  = self.offset / (2*sin(angle)),
                                     perp  = self.offset / (2*cos(angle))
                                    )

    @real_position_argument
    def inverse(self, real_pos):
        '''Run an inverse (real -> pseudo) calculation'''
        return self.PseudoPosition(energy = 2*pi*HBARC/(self._twod*sin(real_pos.bragg*pi/180)))


dcm = DCM('XF:06BMA-OP{Mono:DCM1-Ax:', name='dcm111', crystal='111')

