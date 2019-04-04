import bluesky as bs
import bluesky.plans as bp
import bluesky.plan_stubs as bps

run_report(__file__)

import json

LOCATION = '/home/xf06bm/git/BMM-beamline-configuration/'
MODEDATA = None
def read_mode_data():
     return json.load(open(os.path.join(LOCATION, 'Modes.json')))
if os.path.isfile(os.path.join(LOCATION, 'Modes.json')):
     MODEDATA = read_mode_data()

##########################################################
# --- a simple class for managing beamline configuration #
##########################################################
class BMM_configuration():
    def __init__(self):
        self.pds_mode = self._mode = None

        self.bounds = [-200, -30, 15.3, '14k']
        self.steps = [10, 0.5, '0.05k']
        self.times = [0.5, 0.5, '0.25k']
        
        self.folder = os.environ.get('HOME')+'/data/'
        self.filename = 'data.dat'
        self.experimenters = ''
        self.e0 = None
        self.element = None
        self.edge = 'K'
        self.sample = ''
        self.prep = ''
        self.comment = ''
        self.nscans = 1
        self.start = 0
        self.inttime = 1
        self.snapshots = True
        self.usbstick = True
        self.rockingcurve = False
        self.htmlpage = True
        self.bothways = False
        self.channelcut = True
        self.mode = 'transmission'

        self.npoints = 0 # see 71-timescans.py
        self.dwell = 1.0
        self.delay = 0.1


BMM_config = BMM_configuration()


def change_mode(mode=None, prompt=True):
     if mode is None:
          print('No mode specified')
          return(yield from null())

     mode = mode.upper()
     if mode not in ('A', 'B', 'C', 'D', 'E', 'F', 'XRD'):
          print('%s is not a mode' % mode)
          return(yield from null())
     current_mode = get_mode()
          
     
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
     yield from abs_set(dm3_bct.kill_cmd, 1) # need to explicitly kill this before
                                            # starting a move, it is one of the
                                            # motors that reports MOVN=1 even when
                                            # still

     #base = [
     #   ]
     if mode in ('D', 'E', 'F') and current_mode in ('D', 'E', 'F'):
          yield from mv(dm3_bct,         float(MODEDATA['dm3_bct'][mode]),

                        xafs_yu,         float(MODEDATA['xafs_yu'][mode]),
                        xafs_ydo,        float(MODEDATA['xafs_ydo'][mode]),
                        xafs_ydi,        float(MODEDATA['xafs_ydi'][mode]),

                        m3.yu,           float(MODEDATA['m3_yu'][mode]),
                        m3.ydo,          float(MODEDATA['m3_ydo'][mode]),
                        m3.ydi,          float(MODEDATA['m3_ydi'][mode]),
                        m3.xu,           float(MODEDATA['m3_xu'][mode]),
                        m3.xd,           float(MODEDATA['m3_xd'][mode]),
          
                        slits3.top,      float(MODEDATA['dm3_slits_t'][mode]),
                        slits3.bottom,   float(MODEDATA['dm3_slits_b'][mode]),
                        slits3.inboard,  float(MODEDATA['dm3_slits_i'][mode]),
                        slits3.outboard, float(MODEDATA['dm3_slits_o'][mode]))
     else:
          yield from mv(dm3_bct,         float(MODEDATA['dm3_bct'][mode]),

                        xafs_yu,         float(MODEDATA['xafs_yu'][mode]),
                        xafs_ydo,        float(MODEDATA['xafs_ydo'][mode]),
                        xafs_ydi,        float(MODEDATA['xafs_ydi'][mode]),

                        m3.yu,           float(MODEDATA['m3_yu'][mode]),
                        m3.ydo,          float(MODEDATA['m3_ydo'][mode]),
                        m3.ydi,          float(MODEDATA['m3_ydi'][mode]),
                        m3.xu,           float(MODEDATA['m3_xu'][mode]),
                        m3.xd,           float(MODEDATA['m3_xd'][mode]),
          
                        slits3.top,      float(MODEDATA['dm3_slits_t'][mode]),
                        slits3.bottom,   float(MODEDATA['dm3_slits_b'][mode]),
                        slits3.inboard,  float(MODEDATA['dm3_slits_i'][mode]),
                        slits3.outboard, float(MODEDATA['dm3_slits_o'][mode]),
          
                        m2.yu,           float(MODEDATA['m2_yu'][mode]),
                        m2.ydo,          float(MODEDATA['m2_ydo'][mode]),
                        m2.ydi,          float(MODEDATA['m2_ydi'][mode]))

     yield from bps.sleep(2.0)
     yield from abs_set(dm3_bct.kill_cmd, 1) # and after
     BMM_config.pds_mode = mode
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

if BMM_config.pds_mode is None:
    BMM_config.pds_mode = get_mode()


def change_xtals(xtal=None):
     if xtal is None:
          print('No crystal set specified')
          return(yield from null())

     (ok, text) = BMM_clear_to_start()
     if ok == 0:
          print(colored(text, 'lightred'))
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

     RE.msg_hook = None
     BMM_log_info('Moving to the %s crystals' % xtal)
     yield from abs_set(dcm_pitch.kill_cmd, 1)
     yield from abs_set(dcm_roll.kill_cmd, 1)
     if xtal is 'Si(111)':
          yield from mv(dcm_pitch, 3.8698,
                        dcm_roll, -6.26,
                        dcm_x,    -35.4    )
          #dcm._crystal = '111'
          dcm.set_crystal('111')  # set d-spacing and bragg offset
     elif xtal is 'Si(311)':
          yield from mv(dcm_pitch, 2.28,
                        dcm_roll, -23.86,
                        dcm_x,     29.0    )
          #dcm._crystal = '311'
          dcm.set_crystal('311')  # set d-spacing and bragg offset
          
     yield from bps.sleep(2.0)
     yield from abs_set(dcm_roll.kill_cmd, 1)

     print('Returning to %.1f eV' % current_energy)
     yield from mv(dcm.energy, current_energy)

     print('Performing a rocking curve scan')
     yield from rocking_curve()
     yield from bps.sleep(2.0)
     yield from abs_set(dcm_pitch.kill_cmd, 1)
     RE.msg_hook = BMM_msg_hook
     BMM_log_info(motor_status())
