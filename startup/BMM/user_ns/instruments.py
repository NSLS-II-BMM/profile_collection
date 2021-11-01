from BMM.functions import run_report

run_report(__file__, text='instrument definitions')

## http://patorjk.com/software/taag/#p=display&f=Doom&t=MIRRORS

#################################################
# ___  ____________________ ___________  _____  #
# |  \/  |_   _| ___ \ ___ \  _  | ___ \/  ___| #
# | .  . | | | | |_/ / |_/ / | | | |_/ /\ `--.  #
# | |\/| | | | |    /|    /| | | |    /  `--. \ #
# | |  | |_| |_| |\ \| |\ \\ \_/ / |\ \ /\__/ / #
# \_|  |_/\___/\_| \_\_| \_|\___/\_| \_|\____/  #
#################################################


run_report('\tmirrors')
from BMM.motors import XAFSEpicsMotor, Mirrors, XAFSTable, GonioTable
from BMM.user_ns.motors import mcs8_motors

## harmonic rejection mirror
m3_yu     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M3-Ax:YU}Mtr',   name='m3_yu')
m3_ydo    = XAFSEpicsMotor('XF:06BMA-OP{Mir:M3-Ax:YDO}Mtr',  name='m3_ydo')
m3_ydi    = XAFSEpicsMotor('XF:06BMA-OP{Mir:M3-Ax:YDI}Mtr',  name='m3_ydi')
m3_xu     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M3-Ax:XU}Mtr',   name='m3_xu')
m3_xd     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M3-Ax:XD}Mtr',   name='m3_xd')
mcs8_motors.extend([m3_yu, m3_ydo, m3_ydi, m3_xu, m3_xd])



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
m2.yaw._limits      = (-1, 2)

m3 = Mirrors('XF:06BMA-OP{Mir:M3-Ax:', name='m3', mirror_length=667,  mirror_width=240)
m3.vertical._limits = (-11, 1)
m3.lateral._limits  = (-16, 16)
m3.pitch._limits    = (-6, 6)
m3.roll._limits     = (-2, 2)
m3.yaw._limits      = (-1, 1)


def kill_mirror_jacks():
    yield from m2.kill_jacks()
    yield from m3.kill_jacks()


xt = xafs_table = XAFSTable('XF:06BMA-BI{XAFS-Ax:Tbl_', name='xafs_table', mirror_length=1160,  mirror_width=558)

gonio_table = GonioTable('XF:06BM-ES{SixC-Ax:Tbl_', name='gonio_table', mirror_length=1117.6,  mirror_width=711.12)

run_report('\tmirror trigonometry')
from BMM.mirror_trigonometry import move_m2, move_m3


###################################
#  _____ _     _____ _____ _____  #
# /  ___| |   |_   _|_   _/  ___| #
# \ `--.| |     | |   | | \ `--.  #
#  `--. \ |     | |   | |  `--. \ #
# /\__/ / |_____| |_  | | /\__/ / #
# \____/\_____/\___/  \_/ \____/  #
###################################
                               

run_report('\tslits')
from BMM.slits import Slits, GonioSlits #, recover_slits2, recover_slits3

sl = slits3 = Slits('XF:06BM-BI{Slt:02-Ax:',  name='slits3')
slits3.nominal = [7.0, 1.0, 0.0, 0.0]
slits2 = Slits('XF:06BMA-OP{Slt:01-Ax:',  name='slits2')
slits2.nominal = [18.0, 1.1, 0.0, 0.6]
slits2.top.user_offset.put(-0.038)
slits2.bottom.user_offset.put(0.264)

        
slitsg = GonioSlits('XF:06BM-ES{SixC-Ax:Slt1_',  name='slitsg')



#####################################
#  _    _ _   _  _____ _____ _      #
# | |  | | | | ||  ___|  ___| |     #
# | |  | | |_| || |__ | |__ | |     #
# | |/\| |  _  ||  __||  __|| |     #
# \  /\  / | | || |___| |___| |____ #
#  \/  \/\_| |_/\____/\____/\_____/ #
#####################################
                                 
                                 
run_report('\tsample wheels')
from BMM.wheel import WheelMotor, WheelMacroBuilder, reference, show_reference_wheel

xafs_wheel = xafs_rotb  = WheelMotor('XF:06BMA-BI{XAFS-Ax:RotB}Mtr',  name='xafs_wheel')
xafs_wheel.slotone = -30        # the angular position of slot #1
#xafs_wheel.user_offset.put(-0.7821145500000031)
slot = xafs_wheel.set_slot

xafs_ref = WheelMotor('XF:06BMA-BI{XAFS-Ax:Ref}Mtr',  name='xafs_ref')
xafs_ref.slotone = 0        # the angular position of slot #1

#                    1     2     3     4     5     6     7     8     9     10    11    12
xafs_ref.content = [None, 'Ti', 'V',  'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge',
                    'As', 'Se', 'Br', 'Zr', 'Nb', 'Mo', 'Pt', 'Au', 'Pb', 'Bi', 'Ce', None]
#                    13    14    15    16    17    18    19    20    21    22    23    24

#                    1     2     3     4     5     6     7     8     9     10    11    12
#xafs_ref.content = [None, 'La', 'Ce', 'Pr', 'Nd', 'Sm', 'Tb', 'Ho', 'Er', 'Yb', 'Lu', 'Tm',
#                    'Eu', 'Gd', None, None, 'Au', 'Cu', 'Mo', None, 'Zr', None, 'Fe', 'Ti']
#                    13    14    15    16    17    18    19    20    21    22    23    24

        
## reference foil wheel will be something like this:
# xafs_wheel.content = ['Ti', 'V',  'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As',
#                       'Se', 'Br', 'Sr', 'Y',  'Nb', 'Mo', 'Hf', 'W',  'Re'  'Pt', 'Au', 'Pb']
#
# others: Zr, Rb, Ta, Hg, Ru, Bi, Cs, Ba, La, Ce to Lu (14)
#
# too low (H-Sc): 21
# noble gases: 4
# Rh to I: 9
# radioactive (Tc, Po, At, Fr - U): 9 (Tc, U, and Th could be part of the experiment)
#
# available = 47, unavailable = 45
#
# then,
#   try:
#      sl = xafs_wheel.content.index[elem] + 1
#      yield from reference_slot(sl)
#   except:
#      # don't move reference wheel

from BMM.workspace import rkvs
def ref2redis():
    for i in range(0, rkvs.llen('BMM:reference:list')):
        rkvs.rpop('BMM:reference:list')
    for el in xafs_ref.content:
        rkvs.rpush('BMM:reference:list', el)


def setup_wheel():
    yield from mv(xafs_x, -119.7, xafs_y, 112.1, xafs_wheel, 0)
    

wmb = WheelMacroBuilder()
#xlsx = wmb.spreadsheet




######################################################################################
# ______ _____ _____ _____ _____ _____ ___________  ___  ________ _   _ _   _ _____  #
# |  _  \  ___|_   _|  ___/  __ \_   _|  _  | ___ \ |  \/  |  _  | | | | \ | |_   _| #
# | | | | |__   | | | |__ | /  \/ | | | | | | |_/ / | .  . | | | | | | |  \| | | |   #
# | | | |  __|  | | |  __|| |     | | | | | |    /  | |\/| | | | | | | | . ` | | |   #
# | |/ /| |___  | | | |___| \__/\ | | \ \_/ / |\ \  | |  | \ \_/ / |_| | |\  | | |   #
# |___/ \____/  \_/ \____/ \____/ \_/  \___/\_| \_| \_|  |_/\___/ \___/\_| \_/ \_/   #
######################################################################################
                                                                                  
run_report('\tdetector mount')
from BMM.detector_mount import find_detector_position #, DetectorMount
#detx = DetectorMount()




###########################################################
#   ___  _____ _____ _   _  ___ _____ ___________  _____  #
#  / _ \/  __ \_   _| | | |/ _ \_   _|  _  | ___ \/  ___| #
# / /_\ \ /  \/ | | | | | / /_\ \| | | | | | |_/ /\ `--.  #
# |  _  | |     | | | | | |  _  || | | | | |    /  `--. \ #
# | | | | \__/\ | | | |_| | | | || | \ \_/ / |\ \ /\__/ / #
# \_| |_/\____/ \_/  \___/\_| |_/\_/  \___/\_| \_|\____/  #
###########################################################

run_report('\tactuators')
from BMM.actuators import BMPS_Shutter, IDPS_Shutter, EPS_Shutter

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

# Plan names to open and close the shutters from RE Worker (need distinct name)
shb_open_plan = shb.open_plan
shb_close_plan = shb.close_plan




fs1 = EPS_Shutter('XF:06BMA-OP{FS:1}', name = 'FS1')
fs1.shutter_type = 'FS'
fs1.openval  = 1
fs1.closeval = 0


# single spinner is no longer in user
#fan = Spinner('XF:06BM-EPS{Fan}', name = 'spinner')




###############################################
# ______ _____ _    _____ ___________  _____  #
# |  ___|_   _| |  |_   _|  ___| ___ \/  ___| #
# | |_    | | | |    | | | |__ | |_/ /\ `--.  #
# |  _|   | | | |    | | |  __||    /  `--. \ #
# | |    _| |_| |____| | | |___| |\ \ /\__/ / #
# \_|    \___/\_____/\_/ \____/\_| \_|\____/  #
###############################################


run_report('\tfilters')
from BMM.attenuators import attenuator, filter_state, set_filters
from BMM.user_ns.motors import dm1_filters1, dm1_filters2
filter1 = attenuator()
filter1.motor = dm1_filters1
filter2 = attenuator()
filter2.motor = dm1_filters2



###############################################################################
# ____________ _____ _   _ _____      _____ _   _______  _______________  ___ #
# |  ___| ___ \  _  | \ | |_   _|    |  ___| \ | |  _  \ | ___ \ ___ \  \/  | #
# | |_  | |_/ / | | |  \| | | |______| |__ |  \| | | | | | |_/ / |_/ / .  . | #
# |  _| |    /| | | | . ` | | |______|  __|| . ` | | | | | ___ \  __/| |\/| | #
# | |   | |\ \\ \_/ / |\  | | |      | |___| |\  | |/ /  | |_/ / |   | |  | | #
# \_|   \_| \_|\___/\_| \_/ \_/      \____/\_| \_/___/   \____/\_|   \_|  |_/ #
###############################################################################

                                                                           
run_report('\tfront-end beam position monitor')
from BMM.frontend import FEBPM

try:
    bpm_upstream   = FEBPM('SR:C06-BI{BPM:4}Pos:', name='bpm_upstream')
    bpm_downstream = FEBPM('SR:C06-BI{BPM:5}Pos:', name='bpm_downstream')
except:
    pass

def read_bpms():
    return(bpm_upstream.x.get(), bpm_upstream.y.get(), bpm_downstream.x.get(), bpm_downstream.y.get())





#############################################
#  _     _____ _   _  _   __  ___  ___  ___ #
# | |   |_   _| \ | || | / / / _ \ |  \/  | #
# | |     | | |  \| || |/ / / /_\ \| .  . | #
# | |     | | | . ` ||    \ |  _  || |\/| | #
# | |_____| |_| |\  || |\  \| | | || |  | | #
# \_____/\___/\_| \_/\_| \_/\_| |_/\_|  |_/ #
#############################################


run_report('\tLinkam controller')
from BMM.linkam import Linkam, LinkamMacroBuilder
linkam = Linkam('XF:06BM-ES:{LINKAM}:', name='linkam', egu='°C', settle_time=10, limits=(-169.0,500.0))

lmb = LinkamMacroBuilder()



###############################################################
# ___  ________ _____ ___________   _____ ______ ___________  #
# |  \/  |  _  |_   _|  _  | ___ \ |  __ \| ___ \_   _|  _  \ #
# | .  . | | | | | | | | | | |_/ / | |  \/| |_/ / | | | | | | #
# | |\/| | | | | | | | | | |    /  | | __ |    /  | | | | | | #
# | |  | \ \_/ / | | \ \_/ / |\ \  | |_\ \| |\ \ _| |_| |/ /  #
# \_|  |_/\___/  \_/  \___/\_| \_|  \____/\_| \_|\___/|___/   #
###############################################################

from BMM.grid import GridMacroBuilder
gmb = GridMacroBuilder()



####################################################################################
#  _   _______ _      _       _____  _    _ _____ _____ _____  _   _  _____ _____  #
# | | / /_   _| |    | |     /  ___|| |  | |_   _|_   _/  __ \| | | ||  ___/  ___| #
# | |/ /  | | | |    | |     \ `--. | |  | | | |   | | | /  \/| |_| || |__ \ `--.  #
# |    \  | | | |    | |      `--. \| |/\| | | |   | | | |    |  _  ||  __| `--. \ #
# | |\  \_| |_| |____| |____ /\__/ /\  /\  /_| |_  | | | \__/\| | | || |___/\__/ / #
# \_| \_/\___/\_____/\_____/ \____/  \/  \/ \___/  \_/  \____/\_| |_/\____/\____/  #
####################################################################################
                                                                                

run_report('\tamplifier kill switches')
from BMM.killswitch import KillSwitch
ks = KillSwitch('XF:06BMB-CT{DIODE-Local:4}', name='amplifier kill switches')

