from ophyd import (EpicsMotor, PseudoPositioner, PseudoSingle, Component as Cpt, EpicsSignal, EpicsSignalRO)
from ophyd.pseudopos import (pseudo_position_argument,
                             real_position_argument)

from numpy import pi, sin, cos, arcsin

run_report(__file__)

#from colorama import Fore, Back, Style

HBARC = 1973.27053324

class DCM(PseudoPositioner):
    def __init__(self, *args, crystal='111', mode='fixed', offset=30, **kwargs):
        self._crystal = crystal
        #self.set_crystal()
        self.offset  = offset
        self.mode    = mode
        self.suppress_channel_cut = False
        #self.prompt  = True
        super().__init__(*args, **kwargs)

    @property
    def _pseudo_channel_cut(self):
        if self.suppress_channel_cut:
            return False
        if 'channel' in self.mode:
            return True
        else:
            return False

    @property
    def _twod(self):
        if self._crystal is '311':
            return 2*BMM_dcm.dspacing_311
        else:
            return 2*BMM_dcm.dspacing_111

    def _done_moving(self, *args, **kwargs):
        ## this method is originally defined for Positioner, a base class of EpicsMotor
        ## tack on instructions for killing the motor after movement
        super()._done_moving(*args, **kwargs)
        self.para.kill_cmd.put(1)
        self.perp.kill_cmd.put(1)

    def where(self):
        text  = "%s = %.1f   %s = Si(%s)\n" % \
            (' Energy', self.energy.readback.value,
             'reflection', self._crystal)
        text += "%s: %s = %8.5f   %s  = %7.4f   %s = %8.4f\n" %\
            (' current',
             'Bragg', self.bragg.user_readback.value,
             '2nd Xtal Perp',  self.perp.user_readback.value,
             '2nd Xtal Para',  self.para.user_readback.value)
        #text += "                             %s = %7.4f   %s = %8.4f" %\
        #    ('2nd Xtal pitch', self.pitch.user_readback.value,
        #     '2nd Xtal roll',  self.roll.user_readback.value)
        return text
    def wh(self):
        boxedtext('DCM', self.where(), 'cyan', width=82)

    def restore(self):
        self.mode = 'fixed'
        if dcm_x.user_readback.value < 0:
            self._crystal = '111'
        elif dcm_x.user_readback.value > 0:
            self._crystal = '311'

    # The pseudo positioner axes:
    energy = Cpt(PseudoSingle, limits=(3600, 25000))


    # The real (or physical) positioners:
    bragg  = Cpt(BraggEpicsMotor, 'Bragg}Mtr')
    para   = Cpt(VacuumEpicsMotor, 'Par2}Mtr')
    perp   = Cpt(VacuumEpicsMotor, 'Per2}Mtr')
    #pitch  = Cpt(VacuumEpicsMotor, 'P2}Mtr')
    #roll   = Cpt(VacuumEpicsMotor, 'R2}Mtr')

    #pitch  = Cpt(VacuumEpicsMotor, 'P2}Mtr')

    def kill(self):
        dcm_para.kill_cmd.put(1)
        dcm_perp.kill_cmd.put(1)
        dcm_pitch.kill_cmd.put(1)
        dcm_roll.kill_cmd.put(1)

    def kill_plan(self):
        yield from abs_set(dcm_para.kill_cmd,  1)
        yield from abs_set(dcm_perp.kill_cmd,  1)
        yield from abs_set(dcm_pitch.kill_cmd, 1)
        yield from abs_set(dcm_roll.kill_cmd,  1)


    def set_crystal(self, crystal=None):
        if crystal is not None:
            self._crystal = crystal
        if self._crystal is '311':
            self.bragg.user_offset.put(BMM_dcm.offset_311)
        else:
            self.bragg.user_offset.put(BMM_dcm.offset_111)

    def e2a(self,energy):
        """convert absolute energy to monochromator angle"""
        wavelength = 2*pi*HBARC / energy
        angle = 180 * arcsin(wavelength / dcm._twod) / pi
        return angle

    def wavelength(self,val):
        """convert between mono angle and photon wavelength"""
        return self._twod * sin(val*pi/180)


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


dcm = DCM('XF:06BMA-OP{Mono:DCM1-Ax:', name='dcm', crystal='111')
if dcm_x.user_readback.value > 0: dcm.set_crystal('311')
## dcm_x is 29 for Si(311), -35 for Si(111)
