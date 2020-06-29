

from BMM.wheel import WheelMotor, WheelMacroBuilder
from BMM.functions import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper

run_report(__file__, text='sample and reference wheel definitions')


    

xafs_wheel = xafs_rotb  = WheelMotor('XF:06BMA-BI{XAFS-Ax:RotB}Mtr',  name='xafs_wheel')
xafs_wheel.slotone = -30        # the angular position of slot #1
xafs_wheel.user_offset.put(-2.079)
slot = xafs_wheel.set_slot

xafs_ref = WheelMotor('XF:06BMA-BI{XAFS-Ax:Ref}Mtr',  name='xafs_ref')
xafs_ref.slotone = 0        # the angular position of slot #1

#                    1     2     3     4     5     6     7     8     9     10    11    12
xafs_ref.content = [None, 'Ti', 'V',  'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge',
                    'As', 'Se', 'Br', 'Zr', 'Nb', 'Mo', 'Pt', 'Au', 'Pb', 'Bi', 'Ce', None]

def reference(target=None):
    if target is None:
        print('Not moving reference wheel.')
        return(yield from null())
    if type(target) is int:
        if target < 1 or target > 24:
            print('An integer reference target must be between 1 and 24 (%d)' % target)
            return(yield from null())
        else:
            yield from xafs_ref.set_slot(target)
            return
    try:
        target = target.capitalize()
        slot = xafs_ref.content.index(target) + 1
        yield from xafs_ref.set_slot(slot)
    except:
        print('Element %s is not on the reference wheel.' % target)
        

def show_reference_wheel():
    wheel = xafs_ref.content.copy()
    this  = xafs_ref.current_slot() - 1
    #wheel[this] = go_msg(wheel[this])
    text = 'Foil wheel:\n'
    text += bold_msg('    1      2      3      4      5      6      7      8      9     10     11     12\n')
    text += ' '
    for i in range(12):
        if i==this:
            text += go_msg('%4.4s' % str(wheel[i])) + '   '
        else:
            text += '%4.4s' % str(wheel[i]) + '   '
    text += '\n'
    text += bold_msg('   13     14     15     16     17     18     19     20     21     22     23     24\n')
    text += ' '
    for i in range(12, 24):
        if i==this:
            text += go_msg('%4.4s' % str(wheel[i])) + '   '
        else:
            text += '%4.4s' % str(wheel[i]) + '   '
    text += '\n'
    return(text)
        
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


def setup_wheel():
    yield from mv(xafs_x, -119.7, xafs_y, 112.1, xafs_wheel, 0)
    


        
wmb = WheelMacroBuilder()
#wmb.do_first_change = True

xlsx = wmb.spreadsheet
