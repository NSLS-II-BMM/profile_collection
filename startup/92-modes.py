import bluesky as bs
import bluesky.plans as bp

import json

GITREPO = '/home/bravel/git/BMM-beamline-configuration/'
MOTORDATA = json.load(open(os.path.join(GITREPO, 'Modes.json')))

def change_mode(mode=None):
    if mode is None:
        print('No mode specified')
        return(yield from null())

    mode = mode.upper()
    if mode not in ('A', 'B', 'C', 'D', 'E', 'F'):
        print('%s is not a mode' % mode)
        return(yield from null())

    yield from mv(
        #dm3_bct,     float(MOTORDATA['dm3_bct'][mode]),

        xafs_yu,     float(MOTORDATA['xafs_yu'][mode]),
        xafs_ydo,    float(MOTORDATA['xafs_ydo'][mode]),
        xafs_ydi,    float(MOTORDATA['xafs_ydi'][mode]),

        m2_yu,       float(MOTORDATA['m2_yu'][mode]),
        m2_ydo,      float(MOTORDATA['m2_ydo'][mode]),
        m2_ydi,      float(MOTORDATA['m2_ydi'][mode]),

        m3_yu,       float(MOTORDATA['m3_yu'][mode]),
        m3_ydo,      float(MOTORDATA['m3_ydo'][mode]),
        m3_ydi,      float(MOTORDATA['m3_ydi'][mode]),
        m3_xu,       float(MOTORDATA['m3_xu'][mode]),
        m3_xd,       float(MOTORDATA['m3_xd'][mode]),

        dm3_slits_t, float(MOTORDATA['dm3_slits_t'][mode]),
        dm3_slits_b, float(MOTORDATA['dm3_slits_b'][mode]),
        dm3_slits_i, float(MOTORDATA['dm3_slits_i'][mode]),
        dm3_slits_o, float(MOTORDATA['dm3_slits_o'][mode])
    )
    
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

    if xtal is 'Si(111)':
        yield from mv(dcm_pitch, 5.5511,
                      dcm_roll, -6.2601,
                      dcm_x,    -35.4    )
    elif xtal is 'Si(311)':
        yield from mv(dcm_pitch, 4.00454,
                      dcm_roll, -6.2601,
                      dcm_x,     33.0    )

    yield from abs_set(dcm_pitch.kill_cmd, 1)
    yield from abs_set(dcm_roll.kill_cmd, 1)
    
