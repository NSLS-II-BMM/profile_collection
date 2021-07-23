from BMM.functions import run_report
run_report(__file__, text='Monochromator definitions')


dcm = False
from BMM.dcm import DCM
from BMM.user_ns.motors import dcm_x

dcm = DCM('XF:06BMA-OP{Mono:DCM1-Ax:', name='dcm', crystal='111')
if dcm_x.user_readback.get() > 10:
    dcm.set_crystal('311')
else:
    dcm.set_crystal('111')
