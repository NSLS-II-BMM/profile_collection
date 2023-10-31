from BMM.functions import run_report
run_report(__file__, text='Monochromator definitions')

from BMM.user_ns.instruments import wait_for_connection
from BMM.motors              import FMBOEpicsMotor, VacuumEpicsMotor, XAFSEpicsMotor, DeadbandEpicsMotor
from BMM.user_ns.motors      import mcs8_motors
from BMM.functions           import examine_fmbo_motor_group

# see comment at top of BMM/user_ns/instruments.py
from ophyd.sim import SynAxis

TAB = '\t\t\t'

dcm = False
from BMM.dcm import DCM
#from BMM.user_ns.motors import dcm_x

dcm = DCM('XF:06BMA-OP{Mono:DCM1-Ax:', name='dcm', crystal='111')
wait_for_connection(dcm)

print(f'{TAB}FMBO motor group: dcm')
if dcm.connected is True:
    if hasattr(dcm.bragg, 'tolerance'):  # relevant to Jamie's DeadbandEpicsMotor
        dcm.bragg.tolerance.put(0.0001)

    dcm_bragg = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Bragg}Mtr', name='dcm_bragg')
    dcm_pitch = VacuumEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:P2}Mtr',    name='dcm_pitch')
    dcm_roll  = VacuumEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:R2}Mtr',    name='dcm_roll')
    dcm_perp  = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Per2}Mtr',  name='dcm_perp')
    dcm_para  = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Par2}Mtr',  name='dcm_para')
    dcm_x     = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:X}Mtr',     name='dcm_x')
    dcm_y     = XAFSEpicsMotor('XF:06BMA-OP{Mono:DCM1-Ax:Y}Mtr',     name='dcm_y')

    dcm_para.hlm.put(161)        # this is 21200 on the Si(111) mono
    #                            # hard limit is at 162.48

    if hasattr(dcm_bragg, 'tolerance'):  # relevant to Jamie's DeadbandEpicsMotor
        dcm_bragg.tolerance.put(0.0001)
    dcm_bragg.encoder.kind = 'hinted'
    dcm_bragg.user_readback.kind = 'hinted'
    dcm_bragg.user_setpoint.kind = 'config'
    dcm_bragg.velocity.put(0.4)
    from BMM.user_ns.bmm import BMMuser
    dcm_bragg.acceleration.put(BMMuser.acc_fast)

    ## for some reason, this needs to be set explicitly
    dcm_x.hlm.put(68)
    dcm_x.llm.put(0)
    dcm_x.velocity.put(0.6)
    dcm_x._limits = (0, 68)

    ## dcm_para: 1.25 results in a following error
    dcm_para.velocity.put(0.6)  # sped up 06/26/23 to attempt to deal with stalling at positions > 125
    dcm_para.hvel_sp.put(0.4)
    dcm_perp.velocity.put(0.2)
    dcm_perp.hvel_sp.put(0.2)
    #dcm_para.llm.put(12.3)
    #dcm_para.hlm.put(158.5)
    dcm_perp.llm.put(1.39)
    dcm_perp.hlm.put(26.5)


    if dcm_x.user_readback.get() > 10:
        dcm.set_crystal('311')
    else:
        dcm.set_crystal('111')
    
else:
    dcm_bragg = SynAxis(name='dcm_bragg')
    dcm_pitch = SynAxis(name='dcm_pitch')
    dcm_roll  = SynAxis(name='dcm_roll')
    dcm_perp  = SynAxis(name='dcm_perp')
    dcm_para  = SynAxis(name='dcm_para')
    dcm_x     = SynAxis(name='dcm_x')
    dcm_y     = SynAxis(name='dcm_y')
    
dcmlist = [dcm_bragg, dcm_pitch, dcm_roll, dcm_perp, dcm_para, dcm_x, dcm_y]
mcs8_motors.extend(dcmlist)
examine_fmbo_motor_group(dcmlist)

