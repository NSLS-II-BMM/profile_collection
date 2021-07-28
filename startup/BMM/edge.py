
import time, json, os

from bluesky.plan_stubs import null, abs_set, sleep, mv, mvr

from BMM.logging       import BMM_log_info, BMM_msg_hook, report
from BMM.periodictable import edge_energy, Z_number, element_symbol
from BMM.functions     import boxedtext, countdown, approximate_pitch
from BMM.suspenders    import BMM_clear_to_start
from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.wheel         import show_reference_wheel
from BMM.modes         import change_mode, get_mode, pds_motors_ready, MODEDATA
from BMM.linescans     import rocking_curve, slit_height
from BMM.derivedplot   import close_all_plots, close_last_plot, interpret_click
from BMM.workspace     import rkvs

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

#from __main__ import RE
from BMM.user_ns.bmm         import BMMuser, rois
from BMM.user_ns.dcm         import dcm
from BMM.user_ns.detectors   import xs, with_xspress3
from BMM.user_ns.instruments import kill_mirror_jacks, m3_ydi, m3_ydo, m3_yu, m3_xd, m3_xu
from BMM.user_ns.motors      import *

def show_edges():
    if with_xspress3 is True:
        text = show_reference_wheel() + '\n' + xs.show_rois()
    else:
        text = show_reference_wheel() + '\n' + rois.show()
    boxedtext('Foils and ROIs configuration', text[:-1], 'brown', width=85)


def all_connected(with_m2=False):
    motors = [dm3_bct, xafs_yu, xafs_ydo, xafs_ydi,
              m3_yu, m3_ydo, m3_ydi, m3_xu, m3_xd,]
    if with_m2 is True:
        motors.extend([m2_yu, m2_ydo, m2_ydi])
    ok = True
    for m in motors:
        if m.connected is False:
            print(disconnected_msg(f'{m.name} is not connected'))
            for walk in m.walk_signals(include_lazy=False):
                if walk.item.connected is False:
                    print(disconnected_msg(f'      {walk.item.name} is a disconnected PV'))
            print(whisper(f'try: {m.name} = {m.__class__}("{m.prefix}", name={m.name})'))
            ok = False
    return ok
    
def arrived_in_mode(mode=None):
    motors = [dm3_bct, xafs_yu, xafs_ydo, xafs_ydi,
              m2_yu, m2_ydo, m2_ydi, #m2_xu, m2_xd,
              m3_yu, m3_ydo, m3_ydi, m3_xu, m3_xd,]
    ok = True
    for m in motors:
        target = float(MODEDATA[m][mode])
        achieved = m.position
        diff = abs(target - achieved)
        if diff > 0.5:
            print(f'{m} is out of position, target={target}, current position={achieved}')
            ok = False
    return ok

    
def change_edge(el, focus=False, edge='K', energy=None, slits=True, target=300., xrd=False, bender=True):
    '''Change edge energy by:
    1. Moving the DCM above the edge energy
    2. Moving the photon delivery system to the correct mode
    3. Running a rocking curve scan
    4. Running a slits_height scan

    Parameters
    ----------
    el : str
        one- or two-letter symbol
    focus : bool, optional
        T=focused or F=unfocused beam [False, unfocused]
    edge : str, optional
        edge symbol ['K']
    energy : float, optional
        e0 value [None, determined from el/edge]
    slits : bool, optional
        perform slit_height() scan [False]
    target : float, optional
        energy where rocking curve is measured [300]
    xrd : boolean, optional
        force photon delivery system to XRD [False]

    Examples
    --------
    Normal use, unfocused beam:
       
    >>> RE(change_edge('Fe'))

    Normal use, focused beam:
       
    >>> RE(change_edge('Fe', focus=True))

    L2 or L1 edge:
       
    >>> RE(change_edge('Re', edge='L2'))

    Measure rocking curve at edge energy:
      
    >>> RE(change_edge('Fe', target=0))

    XRD, new energy:
       
    >>> RE(change_edge('Fe', xrd=True, energy=8600))
        
    note that you must specify an element, but it doesn't matter which
    one the energy will be moved to the specified energy xrd=True
    implies focus=True and target=0

    '''
    # try:
    #     xs = user_ns['xs']
    # except:
    #     pass
    #BMMuser.prompt = True
    el = el.capitalize()
    
    ######################################################################
    # this is a tool for verifying a macro.  this replaces an xafsmod scan  #
    # with a sleep, allowing the user to easily map out motor motions in #
    # a macro                                                            #
    if BMMuser.macro_dryrun:
        print(info_msg('\nBMMuser.macro_dryrun is True.  Sleeping for %.1f seconds rather than changing to the %s edge.\n' %
                       (BMMuser.macro_sleep, el)))
        countdown(BMMuser.macro_sleep)
        return(yield from null())
    ######################################################################

    if pds_motors_ready() is False:
        print(error_msg('\nOne or more motors are showing amplifier faults.\nToggle the correct kill switch, then re-enable the faulted motor.'))
        return(yield from null())    
    
    (ok, text) = BMM_clear_to_start()
    if ok is False:
        print(error_msg('\n'+text) + bold_msg('Quitting change_edge() macro....\n'))
        return(yield from null())
    
    if energy is None:
        energy = edge_energy(el,edge)
        
    if energy is None:
        print(error_msg('\nEither %s or %s is not a valid symbol\n' % (el, edge)))
        return(yield from null())
    if energy > 23500:
        edge = 'L3'
        energy = edge_energy(el,'L3')

    if energy < 4000:
        print(warning_msg('The %s edge energy is below 4950 eV' % el))
        print(warning_msg('You have to change energy by hand.'))
        return(yield from null())

    if energy > 23500:
        print(warning_msg('The %s edge energy is outside the range of this beamline!' % el))
        return(yield from null())

    BMMuser.edge        = edge
    BMMuser.element     = el
    BMMuser.edge_energy = energy
    rkvs.set('BMM:pds:edge',        edge)
    rkvs.set('BMM:pds:element',     el)
    rkvs.set('BMM:pds:edge_energy', energy)

    
    if energy > 8000:
        mode = 'A' if focus else 'D'
    elif energy < 6000:
        #mode = 'B' if focus else 'F'   ## mode B currently is inaccessible :(
        mode = 'C' if focus else 'F'
    else:
        mode = 'C' if focus else 'E'
    if xrd:
        mode   = 'XRD'
        focus  = True
        target = 0.0
    current_mode = get_mode()
    if mode in ('D', 'E', 'F') and current_mode in ('D', 'E', 'F'):
        with_m2 = False
    elif mode in ('A', 'B', 'C') and current_mode in ('A', 'B', 'C'): # no need to move M2
        with_m2 = False
    else:
        with_m2 = True
    if all_connected(with_m2) is False:
        print(warning_msg('Ophyd connection failure' % el))
        return(yield from null())


    ################################
    # confirm configuration change #
    ################################
    print(bold_msg('\nEnergy change:'))
    print('   %s: %s %s' % (list_msg('edge'),                    el.capitalize(), edge.capitalize()))
    print('   %s: %.1f'  % (list_msg('edge energy'),             energy))
    print('   %s: %.1f'  % (list_msg('target energy'),           energy+target))
    print('   %s: %s'    % (list_msg('focus'),                   str(focus)))
    print('   %s: %s'    % (list_msg('photon delivery mode'),    mode))
    print('   %s: %s'    % (list_msg('optimizing slits height'), str(slits)))
    if BMMuser.prompt:
        action = input("\nBegin energy change? [Y/n then Enter] ")
        if action.lower() == 'q' or action.lower() == 'n':
            return(yield from null())
        if mode == 'C' and energy < 6000:
            print(warning_msg('\nMoving to mode C for focused beam and an edge energy below 6 keV.'))
            action = input("You will not get optimal harmonic rejection.  Continue anyway?  [Y/n then Enter] ")
            if action.lower() == 'q' or action.lower() == 'n':
                return(yield from null())
        
    start = time.time()
    if mode == 'XRD':
        report('Configuring beamline for XRD', level='bold', slack=True)
    else:
        report(f'Configuring beamline for {el.capitalize()} {edge.capitalize()} edge', level='bold', slack=True)
    yield from dcm.kill_plan()

    ################################################
    # change to the correct photon delivery mode   #
    #      + move mono to correct energy           #
    #      + move reference holder to correct slot #
    ################################################
    # if not calibrating and mode != current_mode:
    #     print('Moving to photon delivery mode %s...' % mode)
    yield from mv(dcm_bragg.acceleration, BMMuser.acc_slow)
    yield from change_mode(mode=mode, prompt=False, edge=energy+target, reference=el, bender=bender)
    yield from mv(dcm_bragg.acceleration, BMMuser.acc_fast)
    if arrived_in_mode(mode=mode) is False:
        print(error_msg(f'\nFailed to arrive in Mode {mode}'))
        print('Fixing this is often as simple as re-running the change_mode() command.')
        print('Or try dm3_bct.kill() the re-run the change_mode() command.')
        print('If that doesn\'t work, call for help')
        return(yield from null())
        
    yield from kill_mirror_jacks()
    yield from sleep(1)
    if BMMuser.motor_fault is not None:
        print(error_msg('\nSome motors are reporting amplifier faults: %s' % BMMuser.motor_fault))
        print('Clear the faults and try running the same change_edge() command again.')
        print('Troubleshooting: ' + url_msg('https://nsls-ii-bmm.github.io/BeamlineManual/trouble.html#amplifier-fault'))
        BMMuser.motor_fault = None
        return(yield from null())
    BMMuser.motor_fault = None
    
        
    ############################
    # run a rocking curve scan #
    ############################
    print('Optimizing rocking curve...')
    yield from abs_set(dcm_pitch.kill_cmd, 1, wait=True)
    yield from mv(dcm_pitch, approximate_pitch(energy+target))
    yield from sleep(1)
    yield from abs_set(dcm_pitch.kill_cmd, 1, wait=True)
    yield from rocking_curve()
    close_last_plot()
    
    ##########################
    # run a slit height scan #
    ##########################
    if slits:
        print('Optimizing slits height...')
        yield from slit_height(move=True)
        close_last_plot()
        ## redo rocking curve?

    ##################################
    # set reference and roi channels #
    ##################################
    if not xrd:
        ## reference channel
        print('Moving reference foil...')
        yield from rois.select_plan(el)
        ## Xspress3
        if with_xspress3:
            BMMuser.verify_roi(xs, el, edge)
        ## feedback
        show_edges()
    
    if mode == 'XRD':
        report('Finished configuring for XRD', level='bold', slack=True)
    else:
        report(f'Finished configuring for {el.capitalize()} {edge.capitalize()} edge', level='bold', slack=True)
    if slits is False:
        print('  * You may need to verify the slit position:  RE(slit_height())')
    #xBMMuser.to_json(os.path.join(BMMuser.folder, '.BMMuser'))
    yield from dcm.kill_plan()
    end = time.time()
    print('\n\nThat took %.1f min' % ((end-start)/60))
    return()

    
