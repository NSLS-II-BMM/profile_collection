import bluesky as bs
import bluesky.plans as bp
import bluesky.plan_stubs as bps

run_report(__file__)

import json
import time

LOCATION = '/home/xf06bm/git/BMM-beamline-configuration/'
MODEDATA = None
def read_mode_data():
     return json.load(open(os.path.join(LOCATION, 'Modes.json')))
if os.path.isfile(os.path.join(LOCATION, 'Modes.json')):
     MODEDATA = read_mode_data()


def change_mode(mode=None, prompt=True, edge=None, reference=None, bender=True):
     '''Move the photon delivery system to a new mode. 
     A: focused at XAS end station, energy > 8000
     B: focused at XAS end station, energy < 6000
     C: focused at XAS end station, 6000 < energy < 8000
     D: unfocused, energy > 8000
     E: unfocused, 6000 < energy < 8000
     F: unfocused, energy < 8000
     XRD: focused at XRD end station, energy > 8000
     '''
     if mode is None:
          print('No mode specified')
          return(yield from null())

     mode = mode.upper()
     if mode not in ('A', 'B', 'C', 'D', 'E', 'F', 'XRD'):
          print('%s is not a mode' % mode)
          return(yield from null())
     current_mode = get_mode()

     if mode == 'B':
          action = input("You are entering Mode B -- focused beam below 6 keV is not properly configured at BMM. Continue? [y/N then Enter] ")
          if action.lower() != 'y':
               return(yield from null())


     
     if mode == 'A':
          description = 'focused, >8 keV'
     elif mode == 'B':
          description = 'focused, <6 keV'
     elif mode == 'C':
          description = 'focused, 6 to 8 keV'
     elif mode == 'D':
          description = 'unfocused, >8 keV'
     elif mode == 'E':
          description = 'unfocused, 6 to 8 keV'
     elif mode == 'F':
          description = 'unfocused, <6 keV'
     elif mode == 'XRD':
          description = 'focused at goniometer, >8 keV'
     print('Moving to mode %s (%s)' % (mode, description))
     if prompt:
          action = input("Begin moving motors? [Y/n then Enter] ")
          if action.lower() == 'q' or action.lower() == 'n':
               yield from null()
               return
          
          
     RE.msg_hook = None
     BMM_log_info('Changing photon delivery system to mode %s' % mode)
     yield from abs_set(dm3_bct.kill_cmd, 1, wait=True) # need to explicitly kill this before
                                                        # starting a move, it is one of the
                                                        # motors that reports MOVN=1 even when
                                                        # still

     base = [dm3_bct,         float(MODEDATA['dm3_bct'][mode]) - 0.86,
                        
             xafs_table.yu,   float(MODEDATA['xafs_yu'][mode]),
             xafs_table.ydo,  float(MODEDATA['xafs_ydo'][mode]),
             xafs_table.ydi,  float(MODEDATA['xafs_ydi'][mode]),

             m3.yu,           float(MODEDATA['m3_yu'][mode]),
             m3.ydo,          float(MODEDATA['m3_ydo'][mode]),
             m3.ydi,          float(MODEDATA['m3_ydi'][mode]),
             m3.xu,           float(MODEDATA['m3_xu'][mode]),
             m3.xd,           float(MODEDATA['m3_xd'][mode]), ]
     if reference is not None:
          base.extend([xafs_ref, foils.position(reference)])
     if edge is not None:
          base.extend([dcm.energy, edge])


     if mode in ('D', 'E', 'F') and current_mode in ('D', 'E', 'F'):
          yield from mv(*base)
     else:
          if bender is True:
               yield from abs_set(m2_bender.kill_cmd, 1, wait=True)
               if mode == 'XRD':
                    if abs(m2_bender.user_readback.value - BMMuser.bender_xrd) > BMMuser.bender_margin: # give some wiggle room for having
                         base.extend([m2_bender, BMMuser.bender_xrd])                                   # recently adjusted the bend 
               elif mode in ('A', 'B', 'C'):
                    if abs(m2_bender.user_readback.value - BMMuser.bender_xas) > BMMuser.bender_margin:
                         base.extend([m2_bender, BMMuser.bender_xas])
          yield from mv(*base,
                        m2.yu,  float(MODEDATA['m2_yu'][mode]),
                        m2.ydo, float(MODEDATA['m2_ydo'][mode]),
                        m2.ydi, float(MODEDATA['m2_ydi'][mode]))

     yield from bps.sleep(2.0)
     yield from abs_set(m2_bender.kill_cmd, 1, wait=True)
     yield from kill_mirror_jacks()
     
     BMMuser.pds_mode = mode
     RE.msg_hook = BMM_msg_hook
     BMM_log_info(motor_status())


def mode():
     print('Motor positions:')
     for m in (dm3_bct, xafs_yu, xafs_ydo, xafs_ydi, m2_yu, m2_ydo,
               m2_ydi, m2_bender, m3_yu, m3_ydo, m3_ydi, m3_xu, m3_xd,
               dm3_slits_t, dm3_slits_b, dm3_slits_i, dm3_slits_o):
          print('\t%-12s:\t%.3f' % (m.name, m.user_readback.value))
          
     if m2.vertical.readback.value < 0: # this is a focused mode
          if m2.pitch.readback.value > 3:
               print('This appears to be mode XRD')
          else:
               if m3.vertical.readback.value > -2:
                    print('This appears to be mode A')
               elif m3.vertical.readback.value > -7:
                    print('This appears to be mode B')
               else:
                    print('This appears to be mode C')
     else:
          if m3.pitch.readback.value < 3:
               print('This appears to be mode F')
          elif m3.lateral.readback.value > 0:
               print('This appears to be mode D')
          else:
               print('This appears to be mode E')

def get_mode():
     if m2.vertical.readback.value < 0: # this is a focused mode
          if m2.pitch.readback.value > 3:
               return 'XRD'
          else:
               if m3.vertical.readback.value > -2:
                    return 'A'
               elif m3.vertical.readback.value > -7:
                    return 'B'
               else:
                    return 'C'
     else:
          if m3.pitch.readback.value < 3:
               return 'F'
          elif m3.lateral.readback.value > 0:
               return 'D'
          else:
               return 'E'

def describe_mode():
     if m2.vertical.readback.value < 0: # this is a focused mode
          if m2.pitch.readback.value > 3:
               return 'focused at goniometer, >8 keV'
          else:
               if m3.vertical.readback.value > -2:
                    return 'focused, >8 keV'
               elif m3.vertical.readback.value > -7:
                    return 'focused, <6 keV'
               else:
                    return 'focused, 6 to 8 keV'
     else:
          if m3.pitch.readback.value < 3:
               return 'unfocused, <6 keV'
          elif m3.lateral.readback.value > 0:
               return 'unfocused, >8 keV'
          else:
               return 'unfocused, 6 to 8 keV'
#    yield from null()

if BMMuser.pds_mode is None:
    BMMuser.pds_mode = get_mode()


def change_xtals(xtal=None):
     '''Move between the Si(111) and Si(311) monochromators, also moving
     2nd crystal pitch and roll to approximate positions.  Then do a
     rocking curve scan.
     '''
     if xtal is None:
          print('No crystal set specified')
          return(yield from null())

     (ok, text) = BMM_clear_to_start()
     if ok == 0:
          print(error_msg(text))
          yield from null()
          return

     if '111' in xtal:
          xtal = 'Si(111)'
     if '311' in xtal:
          xtal = 'Si(311)'

     if xtal not in ('Si(111)', 'Si(311)'):
          print('%s is not a crytsal set' % xtal)
          return(yield from null())

     print('Moving to %s crystals' % xtal)
     action = input('Begin moving motors? [Y/n then Enter] ')
     if action.lower() == 'q' or action.lower() == 'n':
          yield from null()
          return

     current_energy = dcm.energy.readback.value
     start = time.time()

     RE.msg_hook = None
     BMM_log_info('Moving to the %s crystals' % xtal)
     yield from abs_set(dcm_pitch.kill_cmd, 1, wait=True)
     yield from abs_set(dcm_roll.kill_cmd, 1, wait=True)
     if xtal is 'Si(111)':
          yield from mv(dcm_pitch, 3.8698,
                        dcm_roll, -6.26,
                        dcm_x,     0.3    )
          #dcm._crystal = '111'
          dcm.set_crystal('111')  # set d-spacing and bragg offset
     elif xtal is 'Si(311)':
          yield from mv(dcm_pitch, 2.28,
                        dcm_roll, -23.86,
                        dcm_x,     67.3    )
          #dcm._crystal = '311'
          dcm.set_crystal('311')  # set d-spacing and bragg offset
          
     yield from bps.sleep(2.0)
     yield from abs_set(dcm_roll.kill_cmd, 1, wait=True)

     print('Returning to %.1f eV' % current_energy)
     yield from mv(dcm.energy, current_energy)

     print('Performing a rocking curve scan')
     yield from abs_set(dcm_pitch.kill_cmd, 1, wait=True)
     yield from mv(dcm_pitch, approximate_pitch(current_energy))
     yield from bps.sleep(1)
     yield from abs_set(dcm_pitch.kill_cmd, 1, wait=True)
     yield from rocking_curve()
     yield from bps.sleep(2.0)
     yield from abs_set(dcm_pitch.kill_cmd, 1, wait=True)
     RE.msg_hook = BMM_msg_hook
     BMM_log_info(motor_status())
     close_last_plot()
     end = time.time()
     print('\n\nTime elapsed: %.1f min' % ((end-start)/60))
