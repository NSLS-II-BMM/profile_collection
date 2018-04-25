import bluesky as bs
import bluesky.plans as bp

import json

LOCATION = '/home/bravel/git/BMM-beamline-configuration/'
MODEDATA = json.load(open(os.path.join(LOCATION, 'Modes.json')))

def change_mode(mode=None):
    if mode is None:
        print('No mode specified')
        return(yield from null())

    mode = mode.upper()
    if mode not in ('A', 'B', 'C', 'D', 'E', 'F'):
        print('%s is not a mode' % mode)
        return(yield from null())

    yield from abs_set(dm3_bct.kill_cmd, 1) # need to explicitly kill this before
                                            # starting a move, it is one of the
                                            # motors that report MOVN=1 even when
                                            # still
    yield from mv(
        dm3_bct,     float(MODEDATA['dm3_bct'][mode]),

        xafs_yu,     float(MODEDATA['xafs_yu'][mode]),
        xafs_ydo,    float(MODEDATA['xafs_ydo'][mode]),
        xafs_ydi,    float(MODEDATA['xafs_ydi'][mode]),

        m2_yu,       float(MODEDATA['m2_yu'][mode]),
        m2_ydo,      float(MODEDATA['m2_ydo'][mode]),
        m2_ydi,      float(MODEDATA['m2_ydi'][mode]),

        m3_yu,       float(MODEDATA['m3_yu'][mode]),
        m3_ydo,      float(MODEDATA['m3_ydo'][mode]),
        m3_ydi,      float(MODEDATA['m3_ydi'][mode]),
        m3_xu,       float(MODEDATA['m3_xu'][mode]),
        m3_xd,       float(MODEDATA['m3_xd'][mode]),

        dm3_slits_t, float(MODEDATA['dm3_slits_t'][mode]),
        dm3_slits_b, float(MODEDATA['dm3_slits_b'][mode]),
        dm3_slits_i, float(MODEDATA['dm3_slits_i'][mode]),
        dm3_slits_o, float(MODEDATA['dm3_slits_o'][mode])
    )

def mode():
    print("Motor positions:")
    for m in (dm3_bct, xafs_yu, xafs_ydo, xafs_ydi, m2_yu, m2_ydo,
              m2_ydi, m3_yu, m3_ydo, m3_ydi, m3_xu, m3_xd,
              dm3_slits_t, dm3_slits_b, dm3_slits_i, dm3_slits_o):
        print('\t%-12s:\t%.3f' % (m.name, m.user_readback.value))
    if xafs_yu.user_readback.value > 126.5:
        print("This appears to be mode A")
    elif xafs_yu.user_readback.value > 100:
        if m3_xu.user_readback.value > 0:
            print("This appears to be mode D")
        else:
            print("This appears to be mode E")
    elif xafs_yu.user_readback.value > 90:
        print("This appears to be mode F")
    elif xafs_yu.user_readback.value > 40:
        print("This appears to be mode C")
    else:
        print("This appears to be mode B")
        
#    yield from null()
    
    
def change_xtals(xtal=None):
    if xtal is None:
        print('No crystal set specified')
        return(yield from null())

    if '111' in xtal:
        xtal = 'Si(111)'
    if '311' in xtal:
        xtal = 'Si(311)'
    
    if xtal not in ('Si(111)', 'Si(311)'):
        print('%s is not a crytsal set' % xtal)
        return(yield from null())

    yield from abs_set(dcm_pitch.kill_cmd, 1)
    yield from abs_set(dcm_roll.kill_cmd, 1)
    if xtal is 'Si(111)':
        yield from mv(dcm_pitch, 5.583,
                      dcm_roll, -6.26,
                      dcm_x,    -35.4    )
        #dcm.crystal = '111'
        dcm.set_crystal('111')  # set d-spacing and bragg offset
    elif xtal is 'Si(311)':
        yield from mv(dcm_pitch, 3.994,
                      dcm_roll, -23.86,
                      dcm_x,     33.0    )
        #dcm.crystal = '311'
        dcm.set_crystal('311')  # set d-spacing and bragg offset

    yield from sleep(0.5)
    yield from abs_set(dcm_pitch.kill_cmd, 1)
    yield from abs_set(dcm_roll.kill_cmd, 1)
    
