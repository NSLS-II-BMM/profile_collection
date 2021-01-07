from ophyd import (EpicsMotor, PseudoPositioner, PseudoSingle, Component as Cpt, EpicsSignal, EpicsSignalRO)
from ophyd.pseudopos import (pseudo_position_argument,
                             real_position_argument)

from bluesky.plan_stubs import abs_set, sleep, mv, mvr, null

from numpy import pi, sin, cos, arcsin

from BMM.motors         import FMBOEpicsMotor, VacuumEpicsMotor
from BMM.functions      import HBARC, boxedtext, approximate_pitch
from BMM.functions      import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.dcm_parameters import dcm_parameters
BMM_dcm = dcm_parameters()

from IPython import get_ipython
user_ns = get_ipython().user_ns


# PV for clearing encoder signal loss
# XF:06BMA-OP{Mono:DCM1-Ax:Bragg}Mtr_ENC_LSS_CLR_CMD.PROC

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
            (' Energy', self.energy.readback.get(),
             'reflection', self._crystal)
        text += "%s: %s = %8.5f   %s  = %7.4f   %s = %8.4f\n" %\
            (' current',
             'Bragg', self.bragg.user_readback.get(),
             '2nd Xtal Perp',  self.perp.user_readback.get(),
             'Para',  self.para.user_readback.get())
        text += "                                      %s = %7.4f   %s = %8.4f" %\
            ('Pitch', user_ns['dcm_pitch'].user_readback.get(),
             'Roll',  user_ns['dcm_roll'].user_readback.get())
        #text += "                             %s = %7.4f   %s = %8.4f" %\
        #    ('2nd Xtal pitch', self.pitch.user_readback.get(),
        #     '2nd Xtal roll',  self.roll.user_readback.get())
        return text
    def wh(self):
        boxedtext('DCM', self.where(), 'cyan', width=74)

    def restore(self):
        self.mode = 'fixed'
        if dcm_x.user_readback.get() < 10:
            self._crystal = '111'
        elif dcm_x.user_readback.get() > 10:
            self._crystal = '311'

    # The pseudo positioner axes:
    energy = Cpt(PseudoSingle, limits=(2900, 25000))


    # The real (or physical) positioners:
    bragg  = Cpt(FMBOEpicsMotor, 'Bragg}Mtr')
    para   = Cpt(VacuumEpicsMotor, 'Par2}Mtr')
    perp   = Cpt(VacuumEpicsMotor, 'Per2}Mtr')
    #pitch  = Cpt(VacuumEpicsMotor, 'P2}Mtr')
    #roll   = Cpt(VacuumEpicsMotor, 'R2}Mtr')

    def recover(self):
        '''Home and re-position all DCM motors after a power interruption.
        '''
        dcm_bragg, dcm_para, dcm_perp = user_ns['dcm_bragg'], user_ns['dcm_para'], user_ns['dcm_perp']
        dcm_pitch, dcm_roll, dcm_x = user_ns['dcm_pitch'], user_ns['dcm_roll'], user_ns['dcm_x']
        BMMuser, dcm = user_ns['BMMuser'], user_ns['dcm']
        dcm_bragg.acceleration.put(BMMuser.acc_fast)
        dcm_para.velocity.put(0.2)
        dcm_para.hvel_sp.put(0.2)
        dcm_perp.velocity.put(0.2)
        dcm_perp.hvel_sp.put(0.2)
        dcm_x.velocity.put(0.6)
        ## initiate homing for Bragg, pitch, roll, para, perp, and x
        yield from abs_set(dcm_bragg.home_signal, 1)
        yield from abs_set(dcm_pitch.home_signal, 1)
        yield from abs_set(dcm_roll.home_signal,  1)
        yield from abs_set(dcm_para.home_signal,  1)
        yield from abs_set(dcm_perp.home_signal,  1)
        yield from abs_set(dcm_x.home_signal,     1)
        yield from sleep(1.0)
        ## wait for them to be homed
        print('Begin homing DCM motors:\n')
        hvalues = (dcm_bragg.hocpl.get(), dcm_pitch.hocpl.get(), dcm_roll.hocpl.get(), dcm_para.hocpl.get(),
                   dcm_perp.hocpl.get(), dcm_x.hocpl.get())
        while any(v == 0 for v in hvalues):
            hvalues = (dcm_bragg.hocpl.get(), dcm_pitch.hocpl.get(), dcm_roll.hocpl.get(), dcm_para.hocpl.get(),
                       dcm_perp.hocpl.get(), dcm_x.hocpl.get())
            strings = ['Bragg', 'pitch', 'roll', 'para', 'perp', 'x']
            for i,v in enumerate(hvalues):
                strings[i] = go_msg(strings[i]) if hvalues[i] == 1 else error_msg(strings[i])
            print('  '.join(strings), end='\r')
            yield from sleep(1.0)
                

        ## move x into the correct position for Si(111)
        print('\n')
        yield from mv(dcm_x, 1)
        yield from mv(dcm_x, 0.3)
        ## move pitch and roll to the Si(111) positions
        this_energy = dcm.energy.readback.get()
        yield from dcm.kill_plan()
        yield from mv(dcm_pitch, approximate_pitch(this_energy), dcm_roll, -6.26)
        yield from mv(dcm.energy, this_energy)
        print('DCM is at %.1f eV.  There should be signal in I0.' % dcm.energy.readback.get())
        yield from sleep(2.0)
        yield from dcm.kill_plan()

    def enable(self):
        yield from mv(user_ns['dcm_para'].enable_cmd,  1)
        yield from mv(user_ns['dcm_para'].enable_cmd,  1)
        yield from mv(user_ns['dcm_para'].enable_cmd,  1)
        yield from mv(user_ns['dcm_para'].enable_cmd, 1)
        yield from mv(user_ns['dcm_para'].enable_cmd, 1)
        
    def ena(self):
        user_ns['dcm_para'].enable()
        user_ns['dcm_perp'].enable()
        user_ns['dcm_pitch'].enable()
        user_ns['dcm_roll'].enable()

    def kill(self):
        user_ns['dcm_para'].kill_cmd.put(1)
        user_ns['dcm_perp'].kill_cmd.put(1)
        user_ns['dcm_pitch'].kill_cmd.put(1)
        user_ns['dcm_roll'].kill_cmd.put(1)

    def kill_plan(self):
        yield from mv(user_ns['dcm_para'].kill_cmd,  1)
        yield from mv(user_ns['dcm_perp'].kill_cmd,  1)
        yield from mv(user_ns['dcm_pitch'].kill_cmd, 1)
        yield from mv(user_ns['dcm_roll'].kill_cmd,  1)


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
        angle = 180 * arcsin(wavelength / self._twod) / pi
        return angle

    def wavelength(self,val):
        """convert between mono angle and photon wavelength"""
        return self._twod * sin(val*pi/180)

    def motor_positions(self, energy):
        wavelength = 2*pi*HBARC / energy
        angle = arcsin(wavelength / self._twod)
        bragg = 180 * arcsin(wavelength/self._twod) / pi
        para  = self.offset / (2*sin(angle))
        perp  = self.offset / (2*cos(angle))
        print(f'for {energy} ev: bragg={bragg:.4f}  para={para:.4f}  perp={perp:.4f}')
    

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        '''Run a forward (pseudo -> real) calculation'''
        wavelength = 2*pi*HBARC / pseudo_pos.energy
        angle = arcsin(wavelength / self._twod)
        if self._pseudo_channel_cut:
            return self.RealPosition(bragg = 180 * arcsin(wavelength/self._twod) / pi,
                                     para  = self.para.user_readback.get(),
                                     perp  = self.perp.user_readback.get())
        else:
            return self.RealPosition(bragg = 180 * arcsin(wavelength/self._twod) / pi,
                                     para  = self.offset / (2*sin(angle)),
                                     perp  = self.offset / (2*cos(angle))
                                    )

    @real_position_argument
    def inverse(self, real_pos):
        '''Run an inverse (real -> pseudo) calculation'''
        return self.PseudoPosition(energy = 2*pi*HBARC/(self._twod*sin(real_pos.bragg*pi/180)))

