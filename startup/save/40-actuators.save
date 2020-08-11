
from BMM.actuators import BMPS_Shutter, IDPS_Shutter, EPS_Shutter, Spinner

run_report(__file__)

try:
    bmps = BMPS_Shutter('SR:C06-EPS{PLC:1}', name='BMPS')
except:
    pass

try:
    idps = IDPS_Shutter('SR:C06-EPS{PLC:1}', name = 'IDPS')
except:
    pass


sha = EPS_Shutter('XF:06BM-PPS{Sh:FE}', name = 'Front-End Shutter')
sha.shutter_type = 'FE'
sha.openval  = 0
sha.closeval = 1
shb = EPS_Shutter('XF:06BM-PPS{Sh:A}', name = 'Photon Shutter')
shb.shutter_type = 'PH'
shb.openval  = 0
shb.closeval = 1

fs1 = EPS_Shutter('XF:06BMA-OP{FS:1}', name = 'FS1')
fs1.shutter_type = 'FS'
fs1.openval  = 1
fs1.closeval = 0



fan = Spinner('XF:06BM-EPS{Fan}', name = 'spinner')
