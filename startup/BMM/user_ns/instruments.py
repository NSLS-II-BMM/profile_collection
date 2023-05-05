import time, json
from BMM.functions import run_report, examine_fmbo_motor_group
from BMM.workspace import rkvs

run_report(__file__, text='instrument definitions')

TAB = '\t\t\t'

########################################################################
# Note: the use of SynAxis in this file is so that every motor-related #
# symbol gets set to `something' at startup.  This allows bsui to      #
# fully start and places the user at a fully-functional-for-BMM        #
# command line.                                                        #
#                                                                      #
# LOTS of things won't work correctly in this situation. For example,  #
# if M2 is disconnected, then anything that wants to touch M2 will not #
# work, e.g. `%w m2' or any kind of coordinated or non-coordinated     #
# motion.  But this allows one to use and develop BMM's bsui profile   #
# even with multiple motors disconnected.                              #
#                                                                      #
# The most common causes of a disconnected motor are an IOC that is    #
# not running or a controller that is powered down (or both).          #
########################################################################
from ophyd.sim import SynAxis
def wait_for_connection(thing):
    # give it a moment
    count = 0
    while thing.connected is False:
        count += 1
        time.sleep(0.5)
        if count > 10:
            break



## http://patorjk.com/software/taag/#p=display&f=Doom&t=MIRRORS

#################################################
# ___  ____________________ ___________  _____  #
# |  \/  |_   _| ___ \ ___ \  _  | ___ \/  ___| #
# | .  . | | | | |_/ / |_/ / | | | |_/ /\ `--.  #
# | |\/| | | | |    /|    /| | | |    /  `--. \ #
# | |  | |_| |_| |\ \| |\ \\ \_/ / |\ \ /\__/ / #
# \_|  |_/\___/\_| \_\_| \_|\___/\_| \_|\____/  #
#################################################


run_report('\tmirrors and tables')
from BMM.motors import XAFSEpicsMotor, Mirrors, XAFSTable, GonioTable, EndStationEpicsMotor
from BMM.user_ns.bmm import BMMuser
from BMM.user_ns.motors import mcs8_motors, xafs_motors, define_EndStationEpicsMotor


## collimating mirror
print(f'{TAB}FMBO motor group: m1')
m1 = Mirrors('XF:06BM-OP{Mir:M1-Ax:',  name='m1', mirror_length=556,  mirror_width=240)
m1.vertical._limits = (-5.0, 5.0)
m1.lateral._limits  = (-5.0, 5.0)
m1.pitch._limits    = (-5.0, 5.0)
m1.roll._limits     = (-5.0, 5.0)
m1.yaw._limits      = (-5.0, 5.0)

wait_for_connection(m1)



if m1.connected is True:
    m1_yu     = XAFSEpicsMotor('XF:06BM-OP{Mir:M1-Ax:YU}Mtr',   name='m1_yu')
    m1_ydo    = XAFSEpicsMotor('XF:06BM-OP{Mir:M1-Ax:YDO}Mtr',  name='m1_ydo')
    m1_ydi    = XAFSEpicsMotor('XF:06BM-OP{Mir:M1-Ax:YDI}Mtr',  name='m1_ydi')
    m1_xu     = XAFSEpicsMotor('XF:06BM-OP{Mir:M1-Ax:XU}Mtr',   name='m1_xu')
    m1_xd     = XAFSEpicsMotor('XF:06BM-OP{Mir:M1-Ax:XD}Mtr',   name='m1_xd')
else:
    m1_yu     = SynAxis(name='m1_yu')
    m1_ydo    = SynAxis(name='m1_ydo')
    m1_ydi    = SynAxis(name='m1_ydi')
    m1_xu     = SynAxis(name='m1_xu')
    m1_xd     = SynAxis(name='m1_xd')
    
m1list = [m1_yu, m1_ydo, m1_ydi, m1_xu, m1_xd]
mcs8_motors.extend(m1list)


## focusing mirror
print(f'{TAB}FMBO motor group: m2')
m2 = Mirrors('XF:06BMA-OP{Mir:M2-Ax:', name='m2', mirror_length=1288, mirror_width=240)
m2.vertical._limits = (-6.0, 8.0)
m2.lateral._limits  = (-2, 2)
m2.pitch._limits    = (-0.5, 5.0)
m2.roll._limits     = (-2, 2)
m2.yaw._limits      = (-1, 2)

wait_for_connection(m2)


#m2_yu, m2_ydo, m2_ydi, m2_xu, m2_xd, m2_bender = None, None, None, None, None, None
if m2.connected is True:
    m2_yu     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:YU}Mtr',   name='m2_yu')
    m2_ydo    = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:YDO}Mtr',  name='m2_ydo')
    m2_ydi    = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:YDI}Mtr',  name='m2_ydi')
    m2_xu     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:XU}Mtr',   name='m2_xu')
    m2_xd     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:XD}Mtr',   name='m2_yxd')
    m2_bender = XAFSEpicsMotor('XF:06BMA-OP{Mir:M2-Ax:Bend}Mtr', name='m2_bender')
    m2_xu.velocity.put(0.05)
    m2_xd.velocity.put(0.05)
    m2.xu.user_offset.put(-0.2679)
    m2.xd.user_offset.put(1.0199)
else:
    m2_yu     = SynAxis(name='m2_yu')
    m2_ydo    = SynAxis(name='m2_ydo')
    m2_ydi    = SynAxis(name='m2_ydi')
    m2_xu     = SynAxis(name='m2_xu')
    m2_xd     = SynAxis(name='m2_xd')
    m2_bender = SynAxis(name='m2_bender')
m2list = [m2_yu, m2_ydo, m2_ydi, m2_xu, m2_xd, m2_bender]
mcs8_motors.extend(m2list)   
examine_fmbo_motor_group(m2list)


## harmonic rejection mirror
print(f'{TAB}FMBO motor group: m3')
m3 = Mirrors('XF:06BMA-OP{Mir:M3-Ax:', name='m3', mirror_length=667,  mirror_width=240)
m3.vertical._limits = (-11, 1)
m3.lateral._limits  = (-16, 16)
m3.pitch._limits    = (-6, 6)
m3.roll._limits     = (-2, 2)
m3.yaw._limits      = (-1, 1)

wait_for_connection(m3)

#m3_yu, m3_ydo, m3_ydi, m3_xu, m3_xd = None, None, None, None, None
if m3.connected is True:
    m3_yu     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M3-Ax:YU}Mtr',   name='m3_yu')
    m3_ydo    = XAFSEpicsMotor('XF:06BMA-OP{Mir:M3-Ax:YDO}Mtr',  name='m3_ydo')
    m3_ydi    = XAFSEpicsMotor('XF:06BMA-OP{Mir:M3-Ax:YDI}Mtr',  name='m3_ydi')
    m3_xu     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M3-Ax:XU}Mtr',   name='m3_xu')
    m3_xd     = XAFSEpicsMotor('XF:06BMA-OP{Mir:M3-Ax:XD}Mtr',   name='m3_xd')
    m3_xd.velocity.put(0.15)
    m3_xu.velocity.put(0.15)
    #m3.ydo.user_offset.put(-2.1705) #-0.37    
    #m3.ydi.user_offset.put(1.5599)  #-0.24
    m3.xd.user_offset.put(4.691) # fix yaw after January 2022 M3 intervention
    m3.xu.user_offset.put(0.647)
else:
    m3_yu     = SynAxis(name='m3_yu')
    m3_ydo    = SynAxis(name='m3_ydo')
    m3_ydi    = SynAxis(name='m3_ydi')
    m3_xu     = SynAxis(name='m3_xu')
    m3_xd     = SynAxis(name='m3_xd')
mcs8_motors.extend([m3_yu, m3_ydo, m3_ydi, m3_xu, m3_xd])
examine_fmbo_motor_group([m3_yu, m3_ydo, m3_ydi, m3_xu, m3_xd])



def kill_mirror_jacks():
    if m2.connected is True:
        yield from m2.kill_jacks()
    if m3.connected is True:
        yield from m3.kill_jacks()


## XAFS table
print(f'{TAB}XAFS table motor group')
xt = xafs_table = XAFSTable('XF:06BMA-BI{XAFS-Ax:Tbl_', name='xafs_table', mirror_length=1160,  mirror_width=558)
wait_for_connection(xafs_table)

if xafs_table.connected is True:
    xafs_yu  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_YU}Mtr',  name='xafs_yu')
    xafs_ydo = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_YDO}Mtr', name='xafs_ydo')
    xafs_ydi = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_YDI}Mtr', name='xafs_ydi')
    xafs_xu  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_XU}Mtr',  name='xafs_xu')
    xafs_xd  = EndStationEpicsMotor('XF:06BMA-BI{XAFS-Ax:Tbl_XD}Mtr',  name='xafs_xd')
else:
    xafs_yu     = SynAxis(name='xafs_yu')
    xafs_ydo    = SynAxis(name='xafs_ydo')
    xafs_ydi    = SynAxis(name='xafs_ydi')
    xafs_xu     = SynAxis(name='xafs_xu')
    xafs_xd     = SynAxis(name='xafs_xd')
    
xafs_motors.extend([xafs_yu, xafs_ydo, xafs_ydi, xafs_xu, xafs_xd])

from BMM.functions           import examine_xafs_motor_group
print(f'{TAB}Examine XAFS motor groups')
examine_xafs_motor_group(xafs_motors)

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
from BMM.slits import Slits #, recover_slits2, recover_slits3

## DM3
print(f'{TAB}FMBO motor group: slits3')
sl = slits3 = Slits('XF:06BM-BI{Slt:02-Ax:',  name='slits3')
slits3.nominal = [7.0, 1.0, 0.0, 0.0]
wait_for_connection(slits3)

if slits3.connected is True:
    dm3_slits_o = XAFSEpicsMotor('XF:06BM-BI{Slt:02-Ax:O}Mtr',  name='dm3_slits_o')
    dm3_slits_i = XAFSEpicsMotor('XF:06BM-BI{Slt:02-Ax:I}Mtr',  name='dm3_slits_i')
    dm3_slits_t = XAFSEpicsMotor('XF:06BM-BI{Slt:02-Ax:T}Mtr',  name='dm3_slits_t')
    dm3_slits_b = XAFSEpicsMotor('XF:06BM-BI{Slt:02-Ax:B}Mtr',  name='dm3_slits_b')
    dm3_slits_o.hvel_sp.put(0.2)
    dm3_slits_i.hvel_sp.put(0.2)
    dm3_slits_t.hvel_sp.put(0.2)
    dm3_slits_b.hvel_sp.put(0.2)
    dm3_slits_i.user_offset.put(-6.0211)
    dm3_slits_o.user_offset.put(7.9844)
    #dm3_slits_t.user_offset.put(-2.676)
    #dm3_slits_b.user_offset.put(-2.9737)
else:
    dm3_slits_o = SynAxis(name='dm3_slits_o')
    dm3_slits_i = SynAxis(name='dm3_slits_i')
    dm3_slits_t = SynAxis(name='dm3_slits_t')
    dm3_slits_b = SynAxis(name='dm3_slits_b')
    
slits3list = [dm3_slits_o, dm3_slits_i, dm3_slits_t, dm3_slits_b]
mcs8_motors.extend(slits3list)
examine_fmbo_motor_group(slits3list)




## DM2
print(f'{TAB}FMBO motor group: slits2')

slits2 = Slits('XF:06BMA-OP{Slt:01-Ax:',  name='slits2')
slits2.nominal = [18.0, 1.1, 0.0, 0.6]
slits2.top.user_offset.put(-0.038)
slits2.bottom.user_offset.put(0.264)

wait_for_connection(slits2)

if slits2.connected is True:
    dm2_slits_o = XAFSEpicsMotor('XF:06BMA-OP{Slt:01-Ax:O}Mtr',  name='dm2_slits_o')
    dm2_slits_i = XAFSEpicsMotor('XF:06BMA-OP{Slt:01-Ax:I}Mtr',  name='dm2_slits_i')
    dm2_slits_t = XAFSEpicsMotor('XF:06BMA-OP{Slt:01-Ax:T}Mtr',  name='dm2_slits_o')
    dm2_slits_b = XAFSEpicsMotor('XF:06BMA-OP{Slt:01-Ax:B}Mtr',  name='dm2_slits_b')
    dm2_slits_o.hvel_sp.put(0.2)
    dm2_slits_i.hvel_sp.put(0.2)
    dm2_slits_t.hvel_sp.put(0.2)
    dm2_slits_b.hvel_sp.put(0.2)
else:
    dm2_slits_o = SynAxis(name='dm2_slits_o')
    dm2_slits_i = SynAxis(name='dm2_slits_i')
    dm2_slits_t = SynAxis(name='dm2_slits_t')
    dm2_slits_b = SynAxis(name='dm2_slits_b')
    
    
dm2list = [dm2_slits_o, dm2_slits_i, dm2_slits_t, dm2_slits_b]
mcs8_motors.extend(dm2list)
examine_fmbo_motor_group(dm2list)









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
from BMM.user_ns.motors import xafs_x, xafs_refx

xafs_wheel = xafs_rotb  = WheelMotor('XF:06BMA-BI{XAFS-Ax:RotB}Mtr',  name='xafs_wheel')
xafs_wheel.slotone = -30        # the angular position of slot #1
#xafs_wheel.user_offset.put(-0.7821145500000031)
slot = xafs_wheel.set_slot
xafs_wheel.x_motor = xafs_x
if rkvs.get('BMM:wheel:outer') is None:
    xafs_wheel.outer_position = 0
else:
    xafs_wheel.outer_position   = float(rkvs.get('BMM:wheel:outer'))
xafs_wheel.inner_position   = xafs_wheel.outer_position + 26.0


xafs_ref = WheelMotor('XF:06BMA-BI{XAFS-Ax:Ref}Mtr',  name='xafs_ref')
xafs_ref.slotone = 0        # the angular position of slot #1
xafs_ref.x_motor = xafs_refx
if rkvs.get('BMM:ref:outer') is None:
    xafs_ref.outer_position = -78.018
else:
    xafs_ref.outer_position   = float(rkvs.get('BMM:ref:outer'))
xafs_ref.inner_position = -48 # xafs_ref.outer_position + 26.5

#                    1     2     3     4     5     6     7     8     9     10    11    12
#xafs_ref.content = [None, 'Ti', 'V',  'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge',
#                    'As', 'Se', 'Br', 'Zr', 'Nb', 'Mo', 'Pt', 'Au', 'Pb', 'Bi', 'Ce', None]
#                    13    14    15    16    17    18    19    20    21    22    23    24

#                          ring, slot, elem, material (ring: 0=outer, 1=inner)
xafs_ref.mapping = {'empty0': [0,  1, 'empty0', 'empty'],
                    'Ti':     [0,  2, 'Ti', 'Ti foil'],
                    'V' :     [0,  3, 'V',  'V foil'],
                    'Cr':     [0,  4, 'Cr', 'Cr foil'],
                    'Mn':     [0,  5, 'Mn', 'Mn metal powder'],
                    'Fe':     [0,  6, 'Fe', 'Fe foil'],
                    'Co':     [0,  7, 'Co', 'Co foil'],
                    'Ni':     [0,  8, 'Ni', 'Ni foil'],
                    'Cu':     [0,  9, 'Cu', 'Cu foil'],
                    'Zn':     [0, 10, 'Zn', 'Zn foil'],
                    'Ga':     [0, 11, 'Ga', 'Ga2O3'],
                    'Ge':     [0, 12, 'Ge', 'GeO2'],
                    'As':     [0, 13, 'As', 'As2O3'],
                    'Se':     [0, 14, 'Se', 'Se metal powder'],
                    'Br':     [0, 15, 'Br', 'bromophenol blue'],
                    'Zr':     [0, 16, 'Zr', 'Zr foil'],
                    'Nb':     [0, 17, 'Nb', 'Nb foil'],
                    'Mo':     [0, 18, 'Mo', 'Mo foil'],
                    'Pt':     [0, 19, 'Pt', 'Pt foil'],
                    'Au':     [0, 20, 'Au', 'Au foil'],
                    'Pb':     [0, 21, 'Pb', 'Pb foil'],
                    'Bi':     [0, 22, 'Bi', 'BiO2'],
                    'Sr':     [0, 23, 'Sr', 'SrTiO3'],
                    'Y' :     [0, 24, 'Y',  'Y2O3'],
                    'Cs':     [1,  1, 'Cs', 'CsNO3'],
                    'La':     [1,  2, 'La', 'La(OH)3'],
                    'Ce':     [1,  3, 'Ce', 'CeO2'],
                    'Pr':     [1,  4, 'Pr', 'Pr6O11'],
                    'Nd':     [1,  5, 'Nd', 'Nd2O3'],
                    'Sm':     [1,  6, 'Sm', 'Sm2O3'],
                    'Eu':     [1,  7, 'Eu', 'Eu2O3'],
                    'Gd':     [1,  8, 'Gd', 'Gd2O3'],
                    'Tb':     [1,  9, 'Tb', 'Tb4O9'],
                    'Dy':     [1, 10, 'Dy', 'Dy2O3'],
                    'Ho':     [1, 11, 'Ho', 'Ho2O3'],
                    'Er':     [1, 12, 'Er', 'Er2O3'],
                    'Tm':     [1, 13, 'Tm', 'Tm2O3'],
                    'Yb':     [1, 14, 'Yb', 'Yb2O3'],
                    'Lu':     [1, 15, 'Lu', 'Lu2O3'],
                    'Rb':     [1, 16, 'Rb', 'RbCO3'],
                    'Ba':     [1, 17, 'Ba', 'None'],
                    'Hf':     [1, 18, 'Hf', 'HfO2'],
                    'Ta':     [1, 19, 'Ta', 'Ta2O5'],
                    #'Sc' :    [1, 20, 'Sc', 'Sc2O3'],
                    'W' :     [1, 20, 'W',  'WO3'],
                    'Re':     [1, 21, 'Re', 'ReO2'], 
                    'Os':     [1, 22, 'Os', 'None'],
                    'Ir':     [1, 23, 'Ir', 'None'],
                    'Ru':     [1, 24, 'Ru', 'RuO2'],
                    'Th':     [0, 22, 'Bi', 'BiO2'],  # use Bi L1 for Th L3
                    'U' :     [0, 24, 'Y',  'Y2O3'],  # use Y K for U L3
                    'Pu':     [0, 16, 'Zr', 'Zr foil'],  # use Zr K for Pu L3
}
## missing: Tl, Hg, Ca, Sc, Th, U, Pu


#                    1     2     3     4     5     6     7     8     9     10    11    12
#xafs_ref.content = [None, 'La', 'Ce', 'Pr', 'Nd', 'Sm', 'Tb', 'Ho', 'Er', 'Yb', 'Lu', 'Tm',
#                    'Eu', 'Gd', None, None, None, None, None, None, None, 'Ba', None, None]
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

def ref2redis():
    #for i in range(0, rkvs.llen('BMM:reference:list')):
    #    rkvs.rpop('BMM:reference:list')
    #for el in xafs_ref.content:
    #    rkvs.rpush('BMM:reference:list', str(el))
    rkvs.set('BMM:reference:mapping', json.dumps(xafs_ref.mapping))

ref2redis()

def setup_wheel():
    yield from mv(xafs_x, -119.7, xafs_y, 112.1, xafs_wheel, 0)
    

wmb = WheelMacroBuilder()
wmb.description = 'a standard sample wheel'
wmb.instrument  = 'sample wheel'
wmb.folder      = BMMuser.folder
wmb.cleanup     = 'yield from xafs_wheel.reset()' 



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


ln2 = EPS_Shutter('XF:06BM-PU{LN2-Main:IV}', name = 'LN2')
ln2.shutter_type = 'LN'
ln2.openval  = 1
ln2.closeval = 0



###############################################
# ______ _____ _    _____ ___________  _____  #
# |  ___|_   _| |  |_   _|  ___| ___ \/  ___| #
# | |_    | | | |    | | | |__ | |_/ /\ `--.  #
# |  _|   | | | |    | | |  __||    /  `--. \ #
# | |    _| |_| |____| | | |___| |\ \ /\__/ / #
# \_|    \___/\_____/\_/ \____/\_| \_|\____/  #
###############################################


# run_report('\tfilters')
# from BMM.attenuators import attenuator, filter_state, set_filters
# from BMM.user_ns.motors import dm1_filters1, dm1_filters2
# filter1 = attenuator()
# filter1.motor = dm1_filters1
# filter2 = attenuator()
# filter2.motor = dm1_filters2



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



####################################################################
#  _____ _   _ _______   __ ______ _____ _   _ _____ _____  _____  #
# | ___ \ | | /  ___\ \ / / |  _  \  ___| | | |_   _/  __ \|  ___| #
# | |_/ / | | \ `--. \ V /  | | | | |__ | | | | | | | /  \/| |__   #
# | ___ \ | | |`--. \ \ /   | | | |  __|| | | | | | | |    |  __|  #
# | |_/ / |_| /\__/ / | |   | |/ /| |___\ \_/ /_| |_| \__/\| |___  #
# \____/ \___/\____/  \_/   |___/ \____/ \___/ \___/ \____/\____/  #
####################################################################
                                                                
run_report('\tbusy device')
from BMM.busy import Busy
busy = Busy(name='busy')


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
linkam = Linkam('XF:06BM-ES:{LINKAM}:', name='linkam', egu='°C', settle_time=10, limits=(-169.0,560.0))

lmb = LinkamMacroBuilder()
lmb.description = 'the Linkam stage'
lmb.instrument='Linkam'
lmb.folder = BMMuser.folder



##############################################################
#  _       ___   _   __ _____ _____ _   _ ___________ _____  #
# | |     / _ \ | | / /|  ___/  ___| | | |  _  | ___ \  ___| #
# | |    / /_\ \| |/ / | |__ \ `--.| |_| | | | | |_/ / |__   #
# | |    |  _  ||    \ |  __| `--. \  _  | | | |    /|  __|  #
# | |____| | | || |\  \| |___/\__/ / | | \ \_/ / |\ \| |___  #
# \_____/\_| |_/\_| \_/\____/\____/\_| |_/\___/\_| \_\____/  #
##############################################################

run_report('\tLakeShore 331 controller')
from BMM.lakeshore import LakeShore, LakeShoreMacroBuilder
lakeshore = LakeShore('XF:06BM-BI{LS:331-1}:', name='LakeShore 331', egu='K', settle_time=10, limits=(5,400.0))
## 1 second updates on scan and ctrl
lakeshore.temp_scan_rate.put(6)
lakeshore.ctrl_scan_rate.put(6)

lsmb = LakeShoreMacroBuilder()
lsmb.description = 'the LakeShore 331 temperature controller'
lsmb.instrument='LakeShore'
lsmb.folder = BMMuser.folder





###############################################################
# ___  ________ _____ ___________   _____ ______ ___________  #
# |  \/  |  _  |_   _|  _  | ___ \ |  __ \| ___ \_   _|  _  \ #
# | .  . | | | | | | | | | | |_/ / | |  \/| |_/ / | | | | | | #
# | |\/| | | | | | | | | | |    /  | | __ |    /  | | | | | | #
# | |  | \ \_/ / | | \ \_/ / |\ \  | |_\ \| |\ \ _| |_| |/ /  #
# \_|  |_/\___/  \_/  \___/\_| \_|  \____/\_| \_|\___/|___/   #
###############################################################

run_report('\tmotor grid automation')
from BMM.grid import GridMacroBuilder
gmb = GridMacroBuilder()
gmb.description = 'a motor grid'
gmb.instrument = 'grid'
gmb.folder = BMMuser.folder


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

#######################################################
#  _   _ ___________   _   _ ___________ _____ _____  #
# | | | /  ___| ___ \ | | | |_   _|  _  \  ___|  _  | #
# | | | \ `--.| |_/ / | | | | | | | | | | |__ | | | | #
# | | | |`--. \ ___ \ | | | | | | | | | |  __|| | | | #
# | |_| /\__/ / |_/ / \ \_/ /_| |_| |/ /| |___\ \_/ / #
#  \___/\____/\____/   \___/ \___/|___/ \____/ \___/  #
#######################################################
                                                   

run_report('\tvideo recording via USB cameras')
from BMM.video import USBVideo
usbvideo1 = USBVideo('XF:06BM-ES{UVC-Cam:1}CV1:', name='usbvideo1')
usbvideo1.path = '/nsls2/data/bmm/assets/usbcam/'
usbvideo1.initialize()

# usbvideo2 = USBVideo('XF:06BM-ES{UVC-Cam:1}CV2:', name='usbvideo2')
# usbvideo2.enable.put(0)
# usbvideo2.visionfunction3.put(4)
# usbvideo2.path.put('/nsls2/data/bmm/assets/usbcam/')
# usbvideo2.framerate.put(60)
# usbvideo2.startstop.put(0)
