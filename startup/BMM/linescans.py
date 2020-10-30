import bluesky as bs

from bluesky.plans import rel_scan
from bluesky.plan_stubs import abs_set, sleep, mv, null
from bluesky import __version__ as bluesky_version
import numpy, os, datetime
from lmfit.models import SkewedGaussianModel
from databroker.core import SingleRunCache

from bluesky.preprocessors import subs_decorator, finalize_wrapper
## see 65-derivedplot.py for DerivedPlot class
## see 10-motors.py and 20-dcm.py for motor definitions


from bluesky_queueserver.manager.profile_tools import set_user_ns

# from IPython import get_ipython
# user_ns = get_ipython().user_ns

from BMM.resting_state import resting_state_plan
from BMM.suspenders    import BMM_clear_to_start
from BMM.logging       import BMM_log_info, BMM_msg_hook
from BMM.functions     import countdown
from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.derivedplot   import DerivedPlot, interpret_click

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
def move_after_scan(thismotor, user_ns):
    '''
    Call this to pluck a point from a plot and move the plotted motor to that x-value.
    '''
    BMMuser = user_ns['BMMuser']
    if BMMuser.motor is None:
        print(error_msg('\nThere\'s not a current plot on screen.\n'))
        return(yield from null())
    if thismotor is not BMMuser.motor:
        print(error_msg('\nThe motor you are asking to move is not the motor in the current plot.\n'))
        return(yield from null())
    print('Single click the left mouse button on the plot to pluck a point...')
    cid = BMMuser.fig.canvas.mpl_connect('button_press_event', interpret_click) # see derivedplot.py and
    while BMMuser.x is None:                            #  https://matplotlib.org/users/event_handling.html
        yield from sleep(0.5)
    if BMMuser.motor2 is None:
        yield from mv(thismotor, BMMuser.x)
    else:
        print('%.3f  %.3f' % (BMMuser.x, BMMuser.y))
        #yield from mv(BMMuser.motor, BMMuser.x, BMMuser.motor2, BMMuser.y)
    cid = BMMuser.fig.canvas.mpl_disconnect(cid)
    BMMuser.x = BMMuser.y = None

@set_user_ns
def pluck(user_ns):
    '''
    Call this to pluck a point from the most recent plot and move the motor to that point.
    '''
    BMMuser = user_ns['BMMuser']    
    yield from move_after_scan(BMMuser.motor)

from scipy.ndimage import center_of_mass
def com(signal):
    '''Return the center of mass of a 1D array. This is used to find the
    center of rocking curve and slit height scans.'''
    return int(center_of_mass(signal)[0])
import pandas
def peak(signal):
    '''Return the index of the maximum of a 1D array. This is used to find the
    center of rocking curve and slit height scans.'''
    return pandas.Series.idxmax(signal)

@set_user_ns
def slit_height(start=-1.5, stop=1.5, nsteps=31, move=False, force=False, slp=1.0, choice='peak', user_ns=None):
    '''Perform a relative scan of the DM3 BCT motor around the current
    position to find the optimal position for slits3. Optionally, the
    motor will moved to the center of mass of the peak at the end of
    the scan.

    Parameters
    ----------
    start : float
        starting position relative to current [-3.0]
    end : float 
        ending position relative to current [3.0]
    nsteps : int
        number of steps [61]
    move : bool
        True=move to position of max signal, False=pluck and move [False]
    slp : float
        length of sleep before trying to move dm3_bct [3.0]
    choice : str 
        'peak' or 'com' (center of mass) ['peak']
    '''

    def main_plan(start, stop, nsteps, move, slp, force):
        (ok, text) = BMM_clear_to_start()
        if force is False and ok is False:
            print(error_msg(text))
            yield from null()
            return

        RE.msg_hook = None
        BMMuser.motor = user_ns['dm3_bct']
        func = lambda doc: (doc['data'][motor.name], doc['data']['I0'])
        plot = DerivedPlot(func, xlabel=motor.name, ylabel='I0', title='I0 signal vs. slit height')
        line1 = '%s, %s, %.3f, %.3f, %d -- starting at %.3f\n' % \
                (motor.name, 'i0', start, stop, nsteps, motor.user_readback.get())
        rkvs.set('BMM:scan:type',      'line')
        rkvs.set('BMM:scan:starttime', str(datetime.datetime.timestamp(datetime.datetime.now())))
        rkvs.set('BMM:scan:estimated', 0)

        @subs_decorator(plot)
        #@subs_decorator(src.callback)
        def scan_slit(slp):

            #if slit_height < 0.5:
            #    yield from mv(slits3.vsize, 0.5)
            
            yield from abs_set(quadem1.averaging_time, 0.1, wait=True)
            yield from abs_set(motor.velocity, 0.4, wait=True)
            yield from abs_set(motor.kill_cmd, 1, wait=True)

            uid = yield from rel_scan([quadem1], motor, start, stop, nsteps)

            RE.msg_hook = BMM_msg_hook
            BMM_log_info('slit height scan: %s\tuid = %s, scan_id = %d' %
                         (line1, uid, user_ns['db'][-1].start['scan_id']))
            if move:
                t  = db[-1].table()
                signal = t['I0']
                if get_mode() in ('A', 'B', 'C'):
                    position = com(signal)
                else:
                    position = peak(signal)
                top = t[motor.name][position]
                
                yield from sleep(slp)
                yield from abs_set(motor.kill_cmd, 1, wait=True)
                yield from mv(motor, top)

            else:
                action = input('\n' + bold_msg('Pluck motor position from the plot? [Y/n then Enter] '))
                if action.lower() == 'n' or action.lower() == 'q':
                    return(yield from null())
                yield from sleep(slp)
                yield from abs_set(motor.kill_cmd, 1, wait=True)
                yield from move_after_scan(motor)
            yield from abs_set(quadem1.averaging_time, 0.5, wait=True)
        yield from scan_slit(slp)

    def cleanup_plan(slp):
        yield from mv(slits3.vsize, slit_height)
        yield from abs_set(user_ns['_locked_dwell_time'], 0.5, wait=True)
        yield from sleep(slp)
        yield from abs_set(motor.kill_cmd, 1, wait=True)
        yield from resting_state_plan()

    RE, BMMuser, db, slits3, quadem1 = user_ns['RE'], user_ns['BMMuser'], user_ns['db'], user_ns['slits3'], user_ns['quadem1']
    rkvs = user_ns['rkvs']
    #######################################################################
    # this is a tool for verifying a macro.  this replaces this slit      #
    # height scan with a sleep, allowing the user to easily map out motor #
    # motions in a macro                                                  #
    if BMMuser.macro_dryrun:
        print(info_msg('\nBMMuser.macro_dryrun is True.  Sleeping for %.1f seconds rather than running a slit height scan.\n' %
                       BMMuser.macro_sleep))
        countdown(BMMuser.macro_sleep)
        return(yield from null())
    #######################################################################
    motor = user_ns['dm3_bct']
    slit_height = slits3.vsize.readback.get()
    RE.msg_hook = None
    yield from finalize_wrapper(main_plan(start, stop, nsteps, move, slp, force), cleanup_plan(slp))
    RE.msg_hook = BMM_msg_hook


@set_user_ns
def rocking_curve(start=-0.10, stop=0.10, nsteps=101, detector='I0', choice='peak', user_ns=None):
    '''Perform a relative scan of the DCM 2nd crystal pitch around the current
    position to find the peak of the crystal rocking curve.  Begin by opening
    the hutch slits to 3 mm. At the end, move to the position of maximum 
    intensity on I0, then return to the hutch slits to their original height.

    Parameters
    ----------
    start : (float)
        starting position relative to current [-0.1]
    end : (float)
        ending position relative to current [0.1]
    nsteps : (int)
        number of steps [101]
    detector : (string)
        'I0' or 'Bicron' ['I0']
    choice : (string)
        'peak', fit' or 'com' (center of mass) ['peak']

    If choice is fit, the fit is performed using the
    SkewedGaussianModel from lmfit, which works pretty well for this
    measurement at BMM.  The line shape is a bit skewed due to the
    convolution with the slightly misaligned entrance slits.

    '''
    def main_plan(start, stop, nsteps, detector):
        (ok, text) = BMM_clear_to_start()
        if ok is False:
            print(error_msg(text))
            yield from null()
            return

        RE.msg_hook = None
        BMMuser.motor = motor
    
        if detector.lower() == 'bicron':
            func = lambda doc: (doc['data'][motor.name], doc['data']['Bicron'])
            dets = [bicron,]
            sgnl = 'Bicron'
            titl = 'Bicron signal vs. DCM 2nd crystal pitch'
        else:
            func = lambda doc: (doc['data'][motor.name], doc['data']['I0'])
            dets = [quadem1,]
            sgnl = 'I0'
            titl = 'I0 signal vs. DCM 2nd crystal pitch'

        plot = DerivedPlot(func, xlabel=motor.name, ylabel=sgnl, title=titl)

        rkvs.set('BMM:scan:type',      'line')
        rkvs.set('BMM:scan:starttime', str(datetime.datetime.timestamp(datetime.datetime.now())))
        rkvs.set('BMM:scan:estimated', 0)

        @subs_decorator(plot)
        #@subs_decorator(src.callback)
        def scan_dcmpitch(sgnl):
            line1 = '%s, %s, %.3f, %.3f, %d -- starting at %.3f\n' % \
                    (motor.name, sgnl, start, stop, nsteps, motor.user_readback.get())

            yield from abs_set(user_ns['_locked_dwell_time'], 0.1, wait=True)
            yield from dcm.kill_plan()

            yield from mv(slits3.vsize, 3)
            if sgnl == 'Bicron':
                yield from mv(slitsg.vsize, 5)
                
            uid = yield from rel_scan(dets, motor, start, stop, nsteps)
            #yield from rel_adaptive_scan(dets, 'I0', motor,
            #                             start=start,
            #                             stop=stop,
            #                             min_step=0.002,
            #                             max_step=0.03,
            #                             target_delta=.15,
            #                             backstep=True)
            t  = db[-1].table()
            signal = t[sgnl]
            if choice.lower() == 'com':
                position = com(signal)
                top      = t[motor.name][position]
            elif choice.lower() == 'fit':
                pitch    = t['dcm_pitch']
                mod      = SkewedGaussianModel()
                pars     = mod.guess(signal, x=pitch)
                out      = mod.fit(signal, pars, x=pitch)
                print(whisper(out.fit_report(min_correl=0)))
                out.plot()
                top      = out.params['center'].value
            else:
                position = peak(signal)
                top      = t[motor.name][position]

            yield from sleep(3.0)
            yield from abs_set(motor.kill_cmd, 1, wait=True)
            RE.msg_hook = BMM_msg_hook

            BMM_log_info('rocking curve scan: %s\tuid = %s, scan_id = %d' %
                         (line1, uid, user_ns['db'][-1].start['scan_id']))
            yield from mv(motor, top)
            if sgnl == 'Bicron':
                yield from mv(slitsg.vsize, gonio_slit_height)
        yield from scan_dcmpitch(sgnl)

    def cleanup_plan():
        yield from mv(user_ns['slits3'].vsize, slit_height)
        yield from abs_set(user_ns['_locked_dwell_time'], 0.5, wait=True)
        yield from sleep(1.0)
        yield from abs_set(motor.kill_cmd, 1, wait=True)
        yield from sleep(1.0)
        yield from user_ns['dcm'].kill_plan()
        yield from resting_state_plan()

    
    RE, BMMuser, db, rkvs = user_ns['RE'], user_ns['BMMuser'], user_ns['db'], user_ns['rkvs']
    dcm, slits3, slitsg, quadem1 = user_ns['dcm'], user_ns['slits3'], user_ns['slitsg'], user_ns['quadem1']
    ######################################################################
    # this is a tool for verifying a macro.  this replaces this rocking  #
    # curve scan with a sleep, allowing the user to easily map out motor #
    # motions in a macro                                                 #
    if BMMuser.macro_dryrun:
        print(info_msg('\nBMMuser.macro_dryrun is True.  Sleeping for %.1f seconds rather than running a rocking curve scan.\n' %
                       BMMuser.macro_sleep))
        countdown(BMMuser.macro_sleep)
        return(yield from null())
    ######################################################################
    motor = user_ns['dcm_pitch']
    slit_height = user_ns['slits3'].vsize.readback.get()
    try:
        gonio_slit_height = slitsg.vsize.readback.get()
    except:
        gonio_slit_height = 1
    RE.msg_hook = None
    yield from finalize_wrapper(main_plan(start, stop, nsteps, detector), cleanup_plan())
    RE.msg_hook = BMM_msg_hook

@set_user_ns
def get_user_nicknames(user_ns):
    ##                     linear stages        tilt stage           rotation stages
    motor_nicknames = {'x'    : user_ns['xafs_x'],     'roll' : user_ns['xafs_roll'],  'rh' : user_ns['xafs_roth'],
                       'y'    : user_ns['xafs_y'],     'pitch': user_ns['xafs_pitch'], 'wh' : user_ns['xafs_wheel'],
                       's'    : user_ns['xafs_lins'],  'p'    : user_ns['xafs_pitch'], 'rs' : user_ns['xafs_rots'],
                       'xs'   : user_ns['xafs_linxs'], 'r'    : user_ns['xafs_roll'],
                   }
    return motor_nicknames

motor_nicknames = get_user_nicknames()

## before 29 August 2018, the order of arguments for linescan() was
##   linescan(axis, detector, ...)
## now it is
##   linescan(detector, axis, ...)
## for consistency with areascan().  This does a simple check to see if the old
## argument order is being used and swaps them if need be
def ls_backwards_compatibility(detin, axin):
    if type(axin) is str and axin.capitalize() in ('It', 'If', 'I0', 'Iy', 'Ir', 'Both', 'Ia', 'Ib', 'Dualio', 'Xs'):
        return(axin, detin)
    else:
        return(detin, axin)


#mytable = None
####################################
# generic linescan vs. It/If/Ir/I0 #
####################################
@set_user_ns
def linescan(detector, axis, start, stop, nsteps, pluck=True, force=False, inttime=0.1, md={}, user_ns=None): # integration time?
    '''
    Generic linescan plan.  This is a RELATIVE scan, relative to the
    current position of the selected motor.

    Examples
    --------

    >>> RE(linescan('it', 'x', -1, 1, 21))

    Parameters
    ----------
    detector : str
        detector to display -- if, it, ir, or i0
    axis : str or EpicsMotor
        motor or nickname
    start : float
        starting value for a relative scan
    stop : float
         ending value for a relative scan
    nsteps : int
        number of steps in scan
    pluck : bool, optional
        flag for whether to offer to pluck & move motor
    force : bool, optional
        flag for forcing a scan even if not clear to start
    inttime : float, optional
        integration time in seconds (default: 0.1)

    The motor is either the BlueSky name for a motor (e.g. xafs_linx)
    or a nickname for an XAFS sample motor (e.g. 'x' for xafs_linx).

    This does not write an ASCII data file, but it does make a log entry.

    Use the ls2dat() function to extract the linescan from the
    database and write it to a file.
    '''

    def main_plan(detector, axis, start, stop, nsteps, pluck, force):
        (ok, text) = BMM_clear_to_start()
        if force is False and ok is False:
            print(error_msg(text))
            yield from null()
            return

        detector, axis = ls_backwards_compatibility(detector, axis)
        # print('detector is: ' + str(detector))
        # print('axis is: ' + str(axis))
        # return(yield from null())

        RE.msg_hook = None
        ## sanitize input and set thismotor to an actual motor
        if type(axis) is str: axis = axis.lower()
        detector = detector.capitalize()

        ## sanity checks on axis
        if axis not in motor_nicknames.keys() and 'EpicsMotor' not in str(type(axis)) \
           and 'PseudoSingle' not in str(type(axis)) and 'WheelMotor' not in str(type(axis)):
            print(error_msg('\n*** %s is not a linescan motor (%s)\n' %
                          (axis, str.join(', ', motor_nicknames.keys()))))
            yield from null()
            return

        if 'EpicsMotor' in str(type(axis)):
            thismotor = axis
        elif 'PseudoSingle' in str(type(axis)):
            thismotor = axis
        elif 'WheelMotor' in str(type(axis)):
            thismotor = axis
        else:                       # presume it's an xafs_XXXX motor
            thismotor = motor_nicknames[axis]
        BMMuser.motor = thismotor

        ## sanity checks on detector
        if detector not in ('It', 'If', 'I0', 'Iy', 'Ir', 'Both', 'Bicron', 'Ia', 'Ib', 'Dualio', 'Xs', 'Xs1'):
            print(error_msg('\n*** %s is not a linescan measurement (%s)\n' %
                            (detector, 'it, if, i0, iy, ir, both, bicron, dualio, xs, xs1')))
            yield from null()
            return

        yield from abs_set(user_ns['_locked_dwell_time'], inttime, wait=True)
        if detector == 'Xs':
            yield from mv(xs.settings.acquire_time, inttime)
            yield from mv(xs.total_points, nsteps)
        dets  = [user_ns['quadem1'],]
        if user_ns['with_dualem']:
            dualio = user_ns['dualio']
        denominator = ''
        detname = ''
        
        ## func is an anonymous function, built on the fly, for feeding to DerivedPlot
        if detector == 'It':
            denominator = ' / I0'
            detname = 'transmission'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['It']/doc['data']['I0'])
        elif detector == 'Ia' and dualio is not None:
            dets.append(dualio)
            detname = 'Ia'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['Ia'])
        elif detector == 'Ib' and dualio is not None:
            dets.append(dualio)
            detname = 'Ib'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['Ib'])
        elif detector == 'Ir':
            denominator = ' / It'
            detname = 'reference'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['Ir']/doc['data']['It'])
        elif detector == 'I0':
            detname = 'I0'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['I0'])
        elif detector == 'Bicron':
            dets.append(user_ns['vor'])
            detname = 'Bicron'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['Bicron'])
        elif detector == 'Iy':
            denominator = ' / I0'
            detname = 'electron yield'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['Iy']/doc['data']['I0'])
        elif detector == 'If':
            dets.append(user_ns['vor'])
            denominator = ' / I0'
            detname = 'fluorescence'
            func = lambda doc: (doc['data'][thismotor.name],
                                (doc['data'][BMMuser.dtc1] +
                                 doc['data'][BMMuser.dtc2] +
                                 doc['data'][BMMuser.dtc3] +
                                 doc['data'][BMMuser.dtc4]   ) / doc['data']['I0'])
        elif detector == 'Xs':
            dets.append(user_ns['xs'])
            denominator = ' / I0'
            detname = 'fluorescence'
            func = lambda doc: (doc['data'][thismotor.name],
                                (doc['data'][BMMuser.xs1] +
                                 doc['data'][BMMuser.xs2] +
                                 doc['data'][BMMuser.xs3] +
                                 doc['data'][BMMuser.xs4] ) / doc['data']['I0'])
            yield from mv(xs.total_points, nsteps) # Xspress3 demands that this be set up front

        elif detector == 'Xs1':
            dets.append(user_ns['xs'])
            denominator = ' / I0'
            detname = 'fluorescence'
            func = lambda doc: (doc['data'][thismotor.name],
                                doc['data'][BMMuser.xs8] / doc['data']['I0'])
            yield from mv(xs1.total_points, nsteps) # Xspress3 demands that this be set up front

        elif detector == 'Dualio':
            dets.append(dualio)
            funcia = lambda doc: (doc['data'][thismotor.name], doc['data']['Ia'])
            funcib = lambda doc: (doc['data'][thismotor.name], doc['data']['Ib'])

        ## need a "Both" for trans + xs !!!!!!!!!!
        elif detector == 'Both':
            dets.append(user_ns['vor'])
            functr = lambda doc: (doc['data'][thismotor.name], doc['data']['It']/doc['data']['I0'])
            funcfl = lambda doc: (doc['data'][thismotor.name],
                                  (doc['data'][BMMuser.dtc1] +
                                   doc['data'][BMMuser.dtc2] +
                                   doc['data'][BMMuser.dtc3] +
                                   doc['data'][BMMuser.dtc4]   ) / doc['data']['I0'])
        ## and this is the appropriate way to plot this linescan

        #abs_set(_locked_dwell_time, 0.5)
        if detector == 'Both':
            plot = [DerivedPlot(funcfl, xlabel=thismotor.name, ylabel='If/I0', title='fluorescence vs. %s' % thismotor.name),
                    DerivedPlot(functr, xlabel=thismotor.name, ylabel='It/I0', title='transmission vs. %s' % thismotor.name)]
        elif detector == 'Dualio':
            plot = [DerivedPlot(funcia, xlabel=thismotor.name, ylabel='Ia/I0', title='Ia vs. %s' % thismotor.name),
                    DerivedPlot(funcib, xlabel=thismotor.name, ylabel='Ib/I0', title='Ib vs. %s' % thismotor.name)]
        else:
            plot = DerivedPlot(func,
                               xlabel=thismotor.name,
                               ylabel=detector+denominator,
                               title='%s vs. %s' % (detname, thismotor.name))
        if 'PseudoSingle' in str(type(axis)):
            value = thismotor.readback.get()
        else:
            value = thismotor.user_readback.get()
        line1 = '%s, %s, %.3f, %.3f, %d -- starting at %.3f\n' % \
                (thismotor.name, detector, start, stop, nsteps, value)
        ##BMM_suspenders()            # engage suspenders

        thismd = dict()
        thismd['XDI'] = dict()
        thismd['XDI']['Facility'] = dict()
        thismd['XDI']['Facility']['GUP'] = BMMuser.gup
        thismd['XDI']['Facility']['SAF'] = BMMuser.saf

        rkvs.set('BMM:scan:type',      'line')
        rkvs.set('BMM:scan:starttime', str(datetime.datetime.timestamp(datetime.datetime.now())))
        rkvs.set('BMM:scan:estimated', 0)

        @subs_decorator(plot)
        #@subs_decorator(src.callback)
        def scan_xafs_motor(dets, motor, start, stop, nsteps):
            uid = yield from rel_scan(dets, motor, start, stop, nsteps, md={**thismd, **md})
            return uid
            
        uid = yield from scan_xafs_motor(dets, thismotor, start, stop, nsteps)
        #global mytable
        #run = src.retrieve()
        #mytable = run.primary.read().to_dataframe()
        BMM_log_info('linescan: %s\tuid = %s, scan_id = %d' %
                     (line1, uid, user_ns['db'][-1].start['scan_id']))
        if pluck is True:
            action = input('\n' + bold_msg('Pluck motor position from the plot? [Y/n then Enter] '))
            if action.lower() == 'n' or action.lower() == 'q':
                return(yield from null())
            yield from move_after_scan(thismotor)

    
    def cleanup_plan():
        ##RE.clear_suspenders()       # disable suspenders
        yield from resting_state_plan()


    RE, BMMuser, rkvs = user_ns['RE'], user_ns['BMMuser'], user_ns['rkvs']
    try:
        xs = user_ns['xs']
    except:
        pass
    ######################################################################
    # this is a tool for verifying a macro.  this replaces an xafs scan  #
    # with a sleep, allowing the user to easily map out motor motions in #
    # a macro                                                            #
    if BMMuser.macro_dryrun:
        print(info_msg('\nBMMuser.macro_dryrun is True.  Sleeping for %.1f seconds rather than running a line scan.\n' %
                       BMMuser.macro_sleep))
        countdown(BMMuser.macro_sleep)
        return(yield from null())
    ######################################################################
    RE.msg_hook = None
    yield from finalize_wrapper(main_plan(detector, axis, start, stop, nsteps, pluck, force), cleanup_plan())
    RE.msg_hook = BMM_msg_hook



#############################################################
# extract a linescan from the database, write an ascii file #
#############################################################
@set_user_ns
def ls2dat(datafile, key, user_ns):
    '''
    Export a linescan database entry to a simple column data file.

      ls2dat('/path/to/myfile.dat', '0783ac3a-658b-44b0-bba5-ed4e0c4e7216')

    or

      ls2dat('/path/to/myfile.dat', 1533)

    The arguments are a data file name and the database key.
    '''
    BMMuser, db = user_ns['BMMuser'], user_ns['db']
    if os.path.isfile(datafile):
        print(error_msg('%s already exists!  Bailing out....' % datafile))
        return
    handle = open(datafile, 'w')
    dataframe = db[key]
    devices = dataframe.devices() # note: this is a _set_ (this is helpful: https://snakify.org/en/lessons/sets/)
    if 'vor' in devices:
        abscissa = dataframe['start']['motors'][0]
        column_list = [abscissa, 'I0', 'It', 'Ir',
                       BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc3, BMMuser.dtc4,
                       BMMuser.roi1, 'ICR1', 'OCR1',
                       BMMuser.roi2, 'ICR2', 'OCR2',
                       BMMuser.roi3, 'ICR3', 'OCR3',
                       BMMuser.roi4, 'ICR4', 'OCR4']
        template = "  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f\n"
    elif 'DualI0' in devices:
        abscissa = dataframe['start']['motors'][0]
        column_list = [abscissa, 'Ia', 'Ib',]
        template = "  %.3f  %.6f  %.6f\n"
    else:
        abscissa = dataframe['start']['motors'][0]
        template = "  %.3f  %.6f  %.6f  %.6f\n"
        column_list = [abscissa, 'I0', 'It', 'Ir']

    #print(column_list)
    table = dataframe.table()
    this = table.loc[:,column_list]

    handle.write('# XDI/1.0 BlueSky/%s\n'    % bluesky_version)
    handle.write('# Scan.uid: %s\n'          % dataframe['start']['uid'])
    handle.write('# Scan.transient_id: %d\n' % dataframe['start']['scan_id'])
    try:
        handle.write('# Facility.GUP: %s\n'  % dataframe['start']['XDI']['Facility']['GUP'])
    except:
        pass
    try:
        handle.write('# Facility.SAF: %s\n'  % dataframe['start']['XDI']['Facility']['SAF'])
    except:
        pass
    handle.write('# ==========================================================\n')
    handle.write('# ' + '  '.join(column_list) + '\n')
    for i in range(0,len(this)):
        handle.write(template % tuple(this.iloc[i]))
    handle.flush()
    handle.close()
    print(bold_msg('wrote linescan to %s' % datafile))


## these should use src rather than db
    
def center_sample_y():
    yield from linescan('it', xafs_liny, -1.5, 1.5, 61, pluck=False)
    table = db[-1].table()
    diff = -1 * table['It'].diff()
    inflection = table['xafs_liny'][diff.idxmax()]
    yield from mv(xafs_liny, inflection)
    print(bold_msg('Optimal position in y at %.3f' % inflection))

def center_sample_roll():
    yield from linescan('it', xafs_roll, -3, 3, 61, pluck=False)
    table = db[-1].table()
    peak = table['xafs_roll'][table['It'].idxmax()]
    yield from mv(xafs_roll, peak)
    print(bold_msg('Optimal position in roll at %.3f' % peak))

def align_flat_sample(angle=0):
    yield from center_sample_y()
    yield from center_sample_roll()
    yield from center_sample_y()
    yield from center_sample_roll()
    yield from mvr(xafs_roll, angle)
