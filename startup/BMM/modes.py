import json, time, os

from bluesky.plan_stubs import null, abs_set, sleep, mv, mvr

from BMM.derivedplot   import close_all_plots, close_last_plot, interpret_click
from BMM.functions     import approximate_pitch, countdown
from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.linescans     import rocking_curve
from BMM.logging       import BMM_log_info, BMM_msg_hook
from BMM.motor_status  import motor_status
from BMM.suspenders    import BMM_clear_to_start

try:
    from bluesky_queueserver.manager.profile_tools import set_user_ns
except ModuleNotFoundError:
    from ._set_user_ns import set_user_ns

# from IPython import get_ipython
# user_ns = get_ipython().user_ns


MODEDATA = None

@set_user_ns
def read_mode_data(user_ns):
     return json.load(open(os.path.join(user_ns["BMM_CONFIGURATION_LOCATION"], 'Modes.json')))

@set_user_ns
def is_modes_json_exists(user_ns):
    return os.path.isfile(os.path.join(user_ns["BMM_CONFIGURATION_LOCATION"], 'Modes.json'))

if is_modes_json_exists():
     MODEDATA = read_mode_data()


@set_user_ns
def pds_motors_ready(user_ns):
    m3, m2, m2_bender, dm3_bct = user_ns['m3'], user_ns['m2'], user_ns['m2_bender'], user_ns['dm3_bct']
    dcm_pitch, dcm_roll, dcm_perp, dcm_roll, dcm_bragg = user_ns["dcm_pitch"], user_ns["dcm_roll"], user_ns["dcm_perp"], user_ns["dcm_roll"], user_ns["dcm_bragg"]
    mcs8_motors = [m3.xu, m3.xd, m3.yu, m3.ydo, m3.ydi, m2.xu, m2.xd, m2.yu, m2.ydo, m2.ydi, m2_bender, dcm_pitch, dcm_roll, dcm_perp, dcm_roll, dcm_bragg, dm3_bct]

    count = 0
    for m in mcs8_motors:
        if m.amfe.get() or m.amfae.get():
            print(error_msg("%-12s : %s / %s" % (m.name, m.amfe.enum_strs[m.amfe.get()], m.amfae.enum_strs[m.amfae.get()])))
            count += 1
        else:
            pass
    if count > 0:
        return(False)
    else:
        return(True)

     
@set_user_ns
def change_mode(mode=None, prompt=True, edge=None, reference=None, bender=True, *, user_ns):
    '''Move the photon delivery system to a new mode. 
    A: focused at XAS end station, energy > 8000
    B: focused at XAS end station, energy < 6000
    C: focused at XAS end station, 6000 < energy < 8000
    D: unfocused, energy > 8000
    E: unfocused, 6000 < energy < 8000
    F: unfocused, energy < 8000
    XRD: focused at XRD end station, energy > 8000
    '''
    BMMuser, RE, dcm, dm3_bct, slits3 = user_ns['BMMuser'], user_ns['RE'], user_ns['dcm'], user_ns['dm3_bct'], user_ns['slits3']
    xafs_table, m3, m2, m2_bender, xafs_ref = user_ns['xafs_table'], user_ns['m3'], user_ns['m2'], user_ns['m2_bender'], user_ns['xafs_ref']
    if mode is None:
        print('No mode specified')
        return(yield from null())

    mode = mode.upper()
    if mode not in ('A', 'B', 'C', 'D', 'E', 'F', 'XRD'):
        print('%s is not a mode' % mode)
        return(yield from null())
    current_mode = get_mode()

    if pds_motors_ready() is False:
        print(error_msg('\nOne or more motors are showing amplifier faults.\nToggle the correct kill switch, then re-enable the faulted motor.'))
        return(yield from null())
    
    ######################################################################
    # this is a tool for verifying a macro.  this replaces an xafs scan  #
    # with a sleep, allowing the user to easily map out motor motions in #
    # a macro                                                            #
    if BMMuser.macro_dryrun:
        print(info_msg('\nBMMuser.macro_dryrun is True.  Sleeping for %.1f seconds rather than changing to mode %s.\n' %
                       (BMMuser.macro_sleep, mode)))
        countdown(BMMuser.macro_sleep)
        return(yield from null())
    ######################################################################

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
            return(yield from null())
          
          
    RE.msg_hook = None
    BMM_log_info('Changing photon delivery system to mode %s' % mode)
    yield from dcm.kill_plan()
    yield from abs_set(dm3_bct.kill_cmd, 1, wait=True) # need to explicitly kill this before
                                                       # starting a move, it is one of the
                                                       # motors that reports MOVN=1 even when
                                                       # still
                                                       
    base = [dm3_bct,         float(MODEDATA['dm3_bct'][mode]),
                        
            xafs_table.yu,   float(MODEDATA['xafs_yu'][mode]),
            xafs_table.ydo,  float(MODEDATA['xafs_ydo'][mode]),
            xafs_table.ydi,  float(MODEDATA['xafs_ydi'][mode]),

            m3.yu,           float(MODEDATA['m3_yu'][mode]),
            m3.ydo,          float(MODEDATA['m3_ydo'][mode]),
            m3.ydi,          float(MODEDATA['m3_ydi'][mode]),
            m3.xu,           float(MODEDATA['m3_xu'][mode]),
            m3.xd,           float(MODEDATA['m3_xd'][mode]), ]
    if reference is not None:
         #base.extend([xafs_linxs, foils.position(reference.capitalize())])
         base.extend([xafs_ref, xafs_ref.position_of_slot(reference.capitalize())])
    if edge is not None:
         #dcm_bragg.clear_encoder_loss()
         base.extend([dcm.energy, edge])
    if mode in ('D', 'E', 'F'):
         base.extend([slits3.hcenter, 2])
    else:
         base.extend([slits3.hcenter, 0])
          

    ###################################################################
    # check for amplifier faults on the motors, return without moving #
    # anything if any are found                                       #
    ###################################################################
    motors_ready = True
    problem_motors = list()
    for m in base[::2]:
        try:        # skip non-FMBO motors, which do not have the amfe or amfae attributes
            if m.amfe.get() == 1 or m.amfae.get() == 1:
                motors_ready = False
                problem_motors.append(m.name)
        except:
            continue
    if motors_ready is False:
        BMMuser.motor_fault = ', '.join(problem_motors)
        return (yield from null())

    ##########################
    # do the motor movements #
    ##########################
    yield from abs_set(dm3_bct.kill_cmd, 1, wait=True)
    if mode in ('D', 'E', 'F') and current_mode in ('D', 'E', 'F'):
        yield from mv(*base)
    elif mode in ('A', 'B', 'C') and current_mode in ('A', 'B', 'C'): # no need to move M2
        yield from mv(*base)
    else:
        if bender is True:
            yield from abs_set(m2_bender.kill_cmd, 1, wait=True)
            if mode == 'XRD':
                if abs(m2_bender.user_readback.get() - BMMuser.bender_xrd) > BMMuser.bender_margin: # give some wiggle room for having
                    base.extend([m2_bender, BMMuser.bender_xrd])                                   # recently adjusted the bend 
            elif mode in ('A', 'B', 'C'):
                if abs(m2_bender.user_readback.get() - BMMuser.bender_xas) > BMMuser.bender_margin:
                    base.extend([m2_bender, BMMuser.bender_xas])

        base.extend([m2.yu,  float(MODEDATA['m2_yu'][mode])])
        base.extend([m2.ydo, float(MODEDATA['m2_ydo'][mode])])
        base.extend([m2.ydi, float(MODEDATA['m2_ydi'][mode])])
        yield from mv(*base)

    yield from sleep(2.0)
    yield from abs_set(m2_bender.kill_cmd, 1, wait=True)
    yield from abs_set(dm3_bct.kill_cmd, 1, wait=True)
    yield from m2.kill_jacks()
    yield from m3.kill_jacks()
     
    BMMuser.pds_mode = mode
    RE.msg_hook = BMM_msg_hook
    BMM_log_info(motor_status())


@set_user_ns
def mode(user_ns):
    print('Motor positions:')
    for m in ('dm3_bct', 'xafs_yu', 'xafs_ydo', 'xafs_ydi', 'm2_yu', 'm2_ydo',
              'm2_ydi', 'm2_bender', 'm3_yu', 'm3_ydo', 'm3_ydi', 'm3_xu', 'm3_xd',
              'dm3_slits_t', 'dm3_slits_b', 'dm3_slits_i', 'dm3_slits_o'):
        mot = user_ns[m]
        print('\t%-12s:\t%.3f' % (mot.name, mot.user_readback.get()))
        
    m2, m3 = user_ns['m2'], user_ns['m3']
    if m2.vertical.readback.get() < 0: # this is a focused mode
        if m2.pitch.readback.get() > 3:
            print('This appears to be mode XRD')
        else:
            if m3.vertical.readback.get() > -2:
                print('This appears to be mode A')
            elif m3.vertical.readback.get() > -7:
                print('This appears to be mode B')
            else:
                print('This appears to be mode C')
    else:
        if m3.pitch.readback.get() < 3:
            print('This appears to be mode F')
        elif m3.lateral.readback.get() > 0:
            print('This appears to be mode D')
        else:
            print('This appears to be mode E')

@set_user_ns
def get_mode(user_ns):
    m2, m3 = user_ns['m2'], user_ns['m3']
    if m2.vertical.readback.get() < 0: # this is a focused mode
        if m2.pitch.readback.get() > 3:
            return 'XRD'
        else:
            if m3.vertical.readback.get() > -2:
                return 'A'
            elif m3.vertical.readback.get() > -7:
                return 'B'
            else:
                return 'C'
    else:
        if m3.pitch.readback.get() < 3:
            return 'F'
        elif m3.lateral.readback.get() > 0:
            return 'D'
        else:
            return 'E'

@set_user_ns
def describe_mode(user_ns):
    m2, m3 = user_ns['m2'], user_ns['m3']
    if m2.vertical.readback.get() < 0: # this is a focused mode
        if m2.pitch.readback.get() > 3:
            return 'focused at goniometer, >8 keV'
        else:
            if m3.vertical.readback.get() > -2:
                return 'focused, >8 keV'
            elif m3.vertical.readback.get() > -7:
                return 'focused, <6 keV'
            else:
                return 'focused, 6 to 8 keV'
    else:
        if m3.pitch.readback.get() < 3:
            return 'unfocused, <6 keV'
        elif m3.lateral.readback.get() > 0:
            return 'unfocused, >8 keV'
        else:
            return 'unfocused, 6 to 8 keV'


@set_user_ns
def change_xtals(xtal=None, *, user_ns):
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

     BMMuser, RE, dcm, dm3_bct = user_ns['BMMuser'], user_ns['RE'], user_ns['dcm'], user_ns['dm3_bct']
     dcm_pitch, dcm_roll, dcm_x = user_ns['dcm_pitch'], user_ns['dcm_roll'], user_ns['dcm_x']
     
     if '111' in xtal:
          xtal = 'Si(111)'
     if '311' in xtal:
          xtal = 'Si(311)'

     if xtal not in ('Si(111)', 'Si(311)'):
          print('%s is not a crytsal set' % xtal)
          return(yield from null())

     ######################################################################
     # this is a tool for verifying a macro.  this replaces an xafs scan  #
     # with a sleep, allowing the user to easily map out motor motions in #
     # a macro                                                            #
     if BMMuser.macro_dryrun:
          print(info_msg('\nBMMuser.macro_dryrun is True.  Sleeping for %.1f seconds rather than changing to the %s crystal.\n' %
                         (BMMuser.macro_sleep, xtal)))
          countdown(BMMuser.macro_sleep)
          return(yield from null())
     ######################################################################

     print('Moving to %s crystals' % xtal)
     action = input('Begin moving motors? [Y/n then Enter] ')
     if action.lower() == 'q' or action.lower() == 'n':
          yield from null()
          return

     current_energy = dcm.energy.readback.get()
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
          
     yield from sleep(2.0)
     yield from abs_set(dcm_roll.kill_cmd, 1, wait=True)

     print('Returning to %.1f eV' % current_energy)
     yield from mv(dcm.energy, current_energy)

     print('Performing a rocking curve scan')
     yield from abs_set(dcm_pitch.kill_cmd, 1, wait=True)
     yield from mv(dcm_pitch, approximate_pitch(current_energy))
     yield from sleep(1)
     yield from abs_set(dcm_pitch.kill_cmd, 1, wait=True)
     yield from rocking_curve()
     yield from sleep(2.0)
     yield from abs_set(dcm_pitch.kill_cmd, 1, wait=True)
     RE.msg_hook = BMM_msg_hook
     BMM_log_info(motor_status())
     close_last_plot()
     end = time.time()
     print('\n\nTime elapsed: %.1f min' % ((end-start)/60))
        
