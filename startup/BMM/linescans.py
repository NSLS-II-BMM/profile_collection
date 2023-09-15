try:
    from bluesky_queueserver import is_re_worker_active
except ImportError:
    # TODO: delete this when 'bluesky_queueserver' is distributed as part of collection environment
    def is_re_worker_active():
        return False

import bluesky

from bluesky.plans import rel_scan
from bluesky.plan_stubs import sleep, mv, null
from bluesky import __version__ as bluesky_version
import numpy, os, datetime
from lmfit.models import SkewedGaussianModel, RectangleModel
#from databroker.core import SingleRunCache
import matplotlib
import matplotlib.pyplot as plt
from PIL import Image

from bluesky.preprocessors import subs_decorator, finalize_wrapper
## see 65-derivedplot.py for DerivedPlot class
## see 10-motors.py and 20-dcm.py for motor definitions

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

from BMM.derivedplot   import close_all_plots, close_last_plot
from BMM.resting_state import resting_state_plan
from BMM.suspenders    import BMM_clear_to_start, BMM_clear_suspenders
from BMM.kafka         import kafka_message
from BMM.logging       import BMM_log_info, BMM_msg_hook
from BMM.functions     import countdown, clean_img, PROMPT, now
from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.derivedplot   import DerivedPlot, interpret_click
#from BMM.purpose       import purpose
from BMM.workspace     import rkvs

from BMM.user_ns.bmm         import BMMuser
from BMM.user_ns.dcm         import *
from BMM.user_ns.detectors   import quadem1, ic0, ic1, vor, xs, xs1
from BMM.user_ns.dwelltime   import _locked_dwell_time, with_xspress3, with_quadem, with_struck, use_4element, use_1element
from BMM.user_ns.dwelltime   import with_ic0, with_ic1, with_ic2
from BMM.user_ns.instruments import m2, m3, slits3, xafs_wheel
from BMM.user_ns.motors      import *

def get_mode():
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

def unset_mouse_click():
    rkvs.set('BMM:mouse_event:value', '')
    rkvs.set('BMM:mouse_event:motor', '')

        
def pluck(suggested_motor=None):
    '''Negotiate an interaction with the Kafka consumer to pluck a
    position from a plot, stash that position and its motor in Redis,
    then grab that position from Redis.  Assuming the motor name can
    be correlated to an actual motor, offer to move the motor to that
    position.

    This is a bit cumbersome.  Some notes on that:

    (1) Using Kafka to communicate from the consumer back to the bsui
    process would be sensible.  But that would require putting the
    consumer on a thread, which Bruce doesn't really understand.

    (2) The additional check to verify the movement before moving
    might get annoying, however it is easy to attach a callback to
    every plot that the Kafka consumer makes.  Thus, any plot that
    still exists on screen can be plucked from.  The additional
    handshake with the user is required to make sure that the plucked
    value makes sense -- it is possible to pluck from a very stale
    plot!

    (3) There is a hard-coded 20 second time out on clicking on a
    plot.  There has to be a timeout to avoid blocking forever.

    '''

    unset_mouse_click()
    user_ns['BMMuser'].mouse_click = None
    print('\nSingle click the left mouse button on the plot to pluck a point (you have 20 seconds)...')
    count = 0
    while rkvs.get('BMM:mouse_event:value').decode('utf-8') == '':
        yield from sleep(0.25)
        count = count + 1
        if count > 80:
            print('Timing out...')
            return(yield from null())
    
    yield from sleep(0.25)
    position = float(rkvs.get('BMM:mouse_event:value').decode('utf-8'))
    motor_name = rkvs.get('BMM:mouse_event:motor').decode('utf-8')
    motor = None
    
    if suggested_motor is not None and suggested_motor.name != motor_name:
        print(warning_msg(f'You seem to have clicked on the wrong plot.'))
        print(warning_msg(f'You just scanned {suggested_motor.name} but clicked on a window showing {motor.name}.'))
        unset_mouse_click()
        return(yield from null())
        
    for m in user_ns['sd'].baseline:
        if m.name == motor_name:
            motor = m
            break

    if motor == None:
        print(warning_msg(f'{motor_name} does not seem to be the name of an actual motor ...  hmmm....'))
        unset_mouse_click()
        return(yield from null())
        
    action = input(f'\nMove {motor_name} to {position:.3f}? ' + PROMPT)
    if action != '':
        if action[0].lower() == 'n' or action[0].lower() == 'q':
            print('Skipping...')
            unset_mouse_click()
            return(yield from null())
    #print(motor.name, motor_name, position)
    yield from mv(motor, position)
    user_ns['BMMuser'].mouse_click = position
    unset_mouse_click()
    print(whisper('\nRE(pluck()) to grab a different point from the plot.\n'))
    

        
# def move_after_scan(thismotor):
#     '''
#     Call this to pluck a point from a plot and move the plotted motor to that x-value.
#     '''
#     if BMMuser.motor is None:
#         print(error_msg('\nThere\'s not a current plot on screen.\n'))
#         return(yield from null())
#     if thismotor is not BMMuser.motor:
#         print(error_msg('\nThe motor you are asking to move is not the motor in the current plot.\n'))
#         return(yield from null())
#     print('Single click the left mouse button on the plot to pluck a point...')
#     cid = BMMuser.fig.canvas.mpl_connect('button_press_event', interpret_click) # see derivedplot.py and
#     while BMMuser.x is None:                            #  https://matplotlib.org/users/event_handling.html
#         yield from sleep(0.5)
#     if BMMuser.motor2 is None:
#         yield from mv(thismotor, BMMuser.x)
#     else:
#         print('%.3f  %.3f' % (BMMuser.x, BMMuser.y))
#         #yield from mv(BMMuser.motor, BMMuser.x, BMMuser.motor2, BMMuser.y)
#     cid = BMMuser.fig.canvas.mpl_disconnect(cid)
#     BMMuser.x = BMMuser.y = None

# def pluck():
#     '''
#     Call this to pluck a point from the most recent plot and move the motor to that point.
#     '''
#     yield from move_after_scan(BMMuser.motor)

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

def slit_height(start=-1.5, stop=1.5, nsteps=31, move=False, force=False, slp=1.0, choice='peak'):
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

        user_ns['RE'].msg_hook = None
        BMMuser.motor = dm3_bct
        func = lambda doc: (doc['data'][motor.name], doc['data']['I0'])
        plot = DerivedPlot(func, xlabel=motor.name, ylabel='I0', title='I0 signal vs. slit height')
        line1 = '%s, %s, %.3f, %.3f, %d -- starting at %.3f\n' % \
                (motor.name, 'i0', start, stop, nsteps, motor.user_readback.get())
        rkvs.set('BMM:scan:type',      'line')
        rkvs.set('BMM:scan:starttime', str(datetime.datetime.timestamp(datetime.datetime.now())))
        rkvs.set('BMM:scan:estimated', 0)

        def conditional_subs_decorator(function):
            if user_ns['BMMuser'].enable_live_plots is True:
                return subs_decorator(plot)(function)
            else:
                return function
        
        @conditional_subs_decorator
        def scan_slit(slp):

            #if slit_height < 0.5:
            #    yield from mv(slits3.vsize, 0.5)
            
            yield from mv(quadem1.averaging_time, 0.1)
            yield from mv(motor.velocity, 0.4)
            yield from mv(motor.kill_cmd, 1)

            kafka_message({'linescan': 'start',
                           'motor' : motor.name,
                           'detector' : 'I0',})
            uid = yield from rel_scan([quadem1, ic0], motor, start, stop, nsteps, md={'plan_name' : f'rel_scan linescan {motor.name} I0'})
            kafka_message({'linescan': 'stop',})
            
            user_ns['RE'].msg_hook = BMM_msg_hook
            BMM_log_info('slit height scan: %s\tuid = %s, scan_id = %d' %
                         (line1, uid, user_ns['db'][-1].start['scan_id']))
            if move:
                t  = user_ns['db'][-1].table()
                signal = t['I0']
                #if get_mode() in ('A', 'B', 'C'):
                #    position = com(signal)
                #else:
                position = peak(signal)
                top = t[motor.name][position]
                
                yield from sleep(slp)
                yield from mv(motor.kill_cmd, 1)
                yield from sleep(slp)
                yield from mv(motor, top)

            else:
                action = input('\n' + bold_msg('Pluck motor position from the plot? ' + PROMPT))
                if action != '':
                    if action[0].lower() == 'n' or action[0].lower() == 'q':
                        return(yield from null())
                yield from sleep(slp)
                yield from mv(motor.kill_cmd, 1)
                #yield from mv(motor.inpos, 1)
                yield from sleep(slp)
                yield from pluck(suggested_motor=motor)
                #yield from move_after_scan(motor)
            yield from mv(quadem1.averaging_time, 0.5)
        yield from scan_slit(slp)

    def cleanup_plan(slp):
        #yield from mv(slits3.vsize, slit_height)
        yield from mv(_locked_dwell_time, 0.5)
        yield from sleep(slp)
        yield from mv(motor.kill_cmd, 1)
        yield from resting_state_plan()

    #RE, BMMuser, db, slits3, quadem1 = user_ns['RE'], user_ns['BMMuser'], user_ns['db'], user_ns['slits3'], user_ns['quadem1']
    #rkvs = user_ns['rkvs']
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
    motor = dm3_bct
    slit_height = slits3.vsize.readback.get()
    user_ns['RE'].msg_hook = None
    yield from finalize_wrapper(main_plan(start, stop, nsteps, move, slp, force), cleanup_plan(slp))
    user_ns['RE'].msg_hook = BMM_msg_hook


def rocking_curve(start=-0.10, stop=0.10, nsteps=101, detector='I0', choice='peak'):
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

        user_ns['RE'].msg_hook = None
        BMMuser.motor = motor
    
        if detector.lower() == 'bicron':
            func = lambda doc: (doc['data'][motor.name], doc['data']['Bicron'])
            dets = [bicron,]
            sgnl = 'Bicron'
            titl = 'Bicron signal vs. DCM 2nd crystal pitch'
        else:
            func = lambda doc: (doc['data'][motor.name], doc['data']['I0'])
            dets = [quadem1, ic0,]
            sgnl = 'I0'
            titl = 'I0 signal vs. DCM 2nd crystal pitch'

        plot = DerivedPlot(func, xlabel=motor.name, ylabel=sgnl, title=titl)

        rkvs.set('BMM:scan:type',      'line')
        rkvs.set('BMM:scan:starttime', str(datetime.datetime.timestamp(datetime.datetime.now())))
        rkvs.set('BMM:scan:estimated', 0)

        def conditional_subs_decorator(function):
            if user_ns['BMMuser'].enable_live_plots is True:
                return subs_decorator(plot)(function)
            else:
                return function

        @conditional_subs_decorator
        def scan_dcmpitch(sgnl):
            line1 = '%s, %s, %.3f, %.3f, %d -- starting at %.3f\n' % \
                    (motor.name, sgnl, start, stop, nsteps, motor.user_readback.get())

            yield from mv(_locked_dwell_time, 0.1)
            yield from dcm.kill_plan()

            yield from mv(slits3.top, 1.5, slits3.bottom, -1.5)
            #if sgnl == 'Bicron':
            #    yield from mv(slitsg.vsize, 5)
                
            kafka_message({'linescan': 'start',
                           'motor' : motor.name,
                           'detector' : 'I0',})
            uid = yield from rel_scan(dets, motor, start, stop, nsteps, md={'plan_name' : f'rel_scan linescan {motor.name} I0'})
            kafka_message({'linescan': 'stop',})

            t  = user_ns['db'][-1].table()
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

            yield from mv(motor.kill_cmd, 1)
            yield from sleep(1.0)
            user_ns['RE'].msg_hook = BMM_msg_hook

            BMM_log_info('rocking curve scan: %s\tuid = %s, scan_id = %d' %
                         (line1, uid, user_ns['db'][-1].start['scan_id']))
            yield from mv(motor, top)
            #if sgnl == 'Bicron':
            #    yield from mv(slitsg.vsize, gonio_slit_height)
        yield from scan_dcmpitch(sgnl)

    def cleanup_plan():
        yield from mv(slits3.top, slit_height/2, slits3.bottom, -1*slit_height/2)
        #yield from mv(slits3.vsize, slit_height)
        yield from mv(_locked_dwell_time, 0.5)
        yield from sleep(1.0)
        yield from mv(motor.kill_cmd, 1)
        yield from sleep(1.0)
        yield from dcm.kill_plan()
        yield from resting_state_plan()

    
    #RE, BMMuser, db, rkvs = user_ns['RE'], user_ns['BMMuser'], user_ns['db'], user_ns['rkvs']
    #dcm, slits3, slitsg, quadem1 = user_ns['dcm'], user_ns['slits3'], user_ns['slitsg'], user_ns['quadem1']
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
    motor = dcm_pitch
    slit_height = slits3.vsize.readback.get()
    # try:
    #     gonio_slit_height = slitsg.vsize.readback.get()
    # except:
    #     gonio_slit_height = 1
    user_ns['RE'].msg_hook = None
    yield from finalize_wrapper(main_plan(start, stop, nsteps, detector), cleanup_plan())
    user_ns['RE'].msg_hook = BMM_msg_hook


def find_slot(shape='slot'):
    ## NEVER prompt when using queue server
    if is_re_worker_active() is True:
        BMMuser.prompt = False
    if BMMuser.prompt:
        action = input("\nIs the beam currently on a slot in the outer ring? " + PROMPT)
        if action != '':
            if action[0].lower() == 'n' or action[0].lower() == 'q':
                return(yield from null())
    
    kafka_message({'align_wheel' : 'start'})
    if shape == 'circle':
        yield from rectangle_scan(motor=xafs_y, start=-10,  stop=10,  nsteps=31, detector='It', chore='find_slot')
    else:
        yield from rectangle_scan(motor=xafs_y, start=-3,  stop=3,  nsteps=31, detector='It', chore='find_slot')
                              #md={'BMM_kafka': {'hint': f'rectanglescan It xafs_y notnegated'}})
    close_all_plots()
    yield from rectangle_scan(motor=xafs_x, start=-10, stop=10, nsteps=31, detector='It', chore='find_slot')
                              #md={'BMM_kafka': {'hint': f'rectanglescan It xafs_x notnegated'}})
    user_ns['xafs_wheel'].in_place()
    kafka_message({'align_wheel' : 'stop'})
    print(bold_msg(f'Found slot at (X,Y) = ({xafs_x.position}, {xafs_y.position})'))
    close_all_plots()

def find_reference():
    yield from rectangle_scan(motor=xafs_refy, start=-4,   stop=4,   nsteps=31, detector='Ir')
                              #md={'BMM_kafka': {'hint': f'rectanglescan Ir xafs_refy notnegated'}})
    yield from rectangle_scan(motor=xafs_refx, start=-10,  stop=10,  nsteps=31, detector='Ir')
                              #md={'BMM_kafka': {'hint': f'rectanglescan Ir xafs_refx notnegated'}})
    print(bold_msg(f'Found reference slot at (X,Y) = ({xafs_refx.position}, {xafs_refy.position})'))

    
def rectangle_scan(motor=None, start=-20, stop=20, nsteps=41, detector='It',
                   negate=False, filename=None, move=True, force=False, chore='', md={}):

    def main_plan(motor, start, stop, nsteps, detector, negate, filename, move, force, chore, md):
        if force is False:
            (ok, text) = BMM_clear_to_start()
            if ok is False:
                print(error_msg(text))
                yield from null()
                return

        user_ns['RE'].msg_hook = None
        BMMuser.motor = motor

        dets = [user_ns['quadem1'], user_ns['ic0'], ]

        sgnl = 'fluorescence (Xspress3)'

        if detector.lower() == 'if':
            dets.append(user_ns['xs'])
            denominator = ' / I0'
            sgnl = 'fluorescence (Xspress3)'
            func = lambda doc: (doc['data'][motor.name],
                                (doc['data'][BMMuser.xs1] +
                                 doc['data'][BMMuser.xs2] +
                                 doc['data'][BMMuser.xs3] +
                                 doc['data'][BMMuser.xs4] ) / doc['data']['I0'])
            yield from mv(xs.total_points, nsteps)
        elif detector.lower() == 'it':
            sgnl = 'transmission'
            func = lambda doc: (doc['data'][motor.name], doc['data']['It']/ doc['data']['I0'])
        elif detector.lower() == 'ir':
            sgnl = 'reference'
            func = lambda doc: (doc['data'][motor.name], doc['data']['Ir']/ doc['data']['It'])

        titl = f'{sgnl} vs. {motor.name}'
        plot = DerivedPlot(func, xlabel=motor.name, ylabel=sgnl, title=titl)

        rkvs.set('BMM:scan:type',      'line')
        rkvs.set('BMM:scan:starttime', str(datetime.datetime.timestamp(datetime.datetime.now())))
        rkvs.set('BMM:scan:estimated', 0)
        
        def conditional_subs_decorator(function):
            if user_ns['BMMuser'].enable_live_plots is True:
                return subs_decorator(plot)(function)
            else:
                return function
            
        @conditional_subs_decorator
        def doscan(filename):
            line1 = '%s, %s, %.3f, %.3f, %d -- starting at %.3f\n' % \
                    (motor.name, sgnl, start, stop, nsteps, motor.user_readback.get())
            
            if negate == True:
                hint = f'rectanglescan {detector.capitalize()} {motor.name} negated'
            else:
                hint = f'rectanglescan {detector.capitalize()} {motor.name} notnegated'
            if 'BMM_kafka' not in md:
                md['BMM_kafka'] = dict()
            if 'hint' not in md['BMM_kafka']:
                md['BMM_kafka']['hint'] = hint

                
            kafka_message({'linescan': 'start',
                           'motor' : motor.name,
                           'detector' : detector.capitalize(),})
            uid = yield from rel_scan(dets, motor, start, stop, nsteps, md={**md, 'plan_name' : f'rel_scan linescan {motor.name} I0'})
            kafka_message({'linescan': 'stop',})
            
            t  = user_ns['db'][-1].table()
            if detector.lower() == 'if':
                signal   = numpy.array((t[BMMuser.xs1]+t[BMMuser.xs2]+t[BMMuser.xs3]+t[BMMuser.xs4])/t['I0'])
            elif detector.lower() == 'it':
                signal   = numpy.array(t['It']/t['I0'])
            elif detector.lower() == 'ir':
                signal   = numpy.array(t['Ir']/t['It'])

            signal = signal - signal[0]
            if negate is True:
                signal = -1 * signal
            pos      = numpy.array(t[motor.name])
            mod      = RectangleModel(form='erf')
            pars     = mod.guess(signal, x=pos)
            out      = mod.fit(signal, pars, x=pos)
            print(whisper(out.fit_report(min_correl=0)))
            if chore == 'find_slot':
                kafka_message({'align_wheel' : 'find_slot',
                               'motor'       : motor.name,
                               'detector'    : detector.lower(),
                               'xaxis'       : list(pos),
                               'data'        : list(signal),
                               'best_fit'    : list(out.best_fit),
                               'center'      : out.params['midpoint'].value,
                               'amplitude'   : out.params['amplitude'].value,
                               'uid'         : uid})

            # thisagg = matplotlib.get_backend()
            # matplotlib.use('Agg') # produce a plot without screen display
            # out.plot(xlabel=motor.name, ylabel=detector)
            # if filename is None:
            #     filename = os.path.join(user_ns['BMMuser'].folder, 'snapshots', 'toss.png')
            # plt.savefig(filename)
            # matplotlib.use(thisagg) # return to screen display
            # clean_img()
            # BMMuser.display_img = Image.open(os.path.join(user_ns['BMMuser'].folder, 'snapshots', 'toss.png'))
            # BMMuser.display_img.show()

            if move is True:
                yield from mv(motor, out.params['midpoint'].value)
            print(bold_msg(f'Found center at {motor.name} = {motor.position}'))
            for k in ('center1', 'center2', 'sigma1', 'sigma2', 'amplitude', 'midpoint'):
                rkvs.set(f'BMM:lmfit:{k}', out.params[k].value)

        yield from doscan(filename)
        
    def cleanup_plan():
        yield from resting_state_plan()
    
    user_ns['RE'].msg_hook = None
    yield from finalize_wrapper(main_plan(motor, start, stop, nsteps, detector, negate, filename, move, force, chore, md),
                                cleanup_plan())
    user_ns['RE'].msg_hook = BMM_msg_hook


def peak_scan(motor=None, start=-20, stop=20, nsteps=41, detector='It', find='max', how='peak', filename=None):

    def main_plan(motor, start, stop, nsteps, detector, find, how, filename):
        (ok, text) = BMM_clear_to_start()
        if ok is False:
            print(error_msg(text))
            yield from null()
            return

        user_ns['RE'].msg_hook = None
        BMMuser.motor = motor

        dets = [user_ns['quadem1'], user_ns['ic0'],]

        sgnl = 'fluorescence (Xspress3)'

        if detector.lower() == 'if':
            dets.append(user_ns['xs'])
            denominator = ' / I0'
            sgnl = 'fluorescence (Xspress3)'
            func = lambda doc: (doc['data'][motor.name],
                                (doc['data'][BMMuser.xs1] +
                                 doc['data'][BMMuser.xs2] +
                                 doc['data'][BMMuser.xs3] +
                                 doc['data'][BMMuser.xs4] ) / doc['data']['I0'])
            yield from mv(xs.total_points, nsteps)
        elif detector.lower() == 'it':
            sgnl = 'transmission'
            func = lambda doc: (doc['data'][motor.name], doc['data']['It']/ doc['data']['I0'])
        elif detector.lower() == 'ir':
            sgnl = 'reference'
            func = lambda doc: (doc['data'][motor.name], doc['data']['Ir']/ doc['data']['It'])

        titl = f'{sgnl} vs. {motor.name}'
        plot = DerivedPlot(func, xlabel=motor.name, ylabel=sgnl, title=titl)

        rkvs.set('BMM:scan:type',      'line')
        rkvs.set('BMM:scan:starttime', str(datetime.datetime.timestamp(datetime.datetime.now())))
        rkvs.set('BMM:scan:estimated', 0)

        def conditional_subs_decorator(function):
            if user_ns['BMMuser'].enable_live_plots is True:
                return subs_decorator(plot)(function)
            else:
                return function
        
        @conditional_subs_decorator
        def doscan(filename):
            line1 = '%s, %s, %.3f, %.3f, %d -- starting at %.3f\n' % \
                    (motor.name, sgnl, start, stop, nsteps, motor.user_readback.get())

            kafka_message({'linescan': 'start',
                           'motor' : motor.name,
                           'detector' : detector. capitalize(),})
            uid = yield from rel_scan(dets, motor, start, stop, nsteps, md={'plan_name' : f'rel_scan linescan {motor.name} I0'})
            kafka_message({'linescan': 'stop',})

            t  = user_ns['db'][-1].table()
            if detector.lower() == 'if':
                signal   = numpy.array((t[BMMuser.xs1]+t[BMMuser.xs2]+t[BMMuser.xs3]+t[BMMuser.xs4])/t['I0'])
            elif detector.lower() == 'it':
                signal   = numpy.array(t['It']/t['I0'])
            elif detector.lower() == 'ir':
                signal   = numpy.array(t['Ir']/t['It'])

            signal = signal - signal[0]
            if find == 'min':
                signal = -1 * signal
            pos      = numpy.array(t[motor.name])

            if choice.lower() == 'com':
                position = com(signal)
                top      = t[motor.name][position]
            elif choice.lower() == 'fit':
                pitch    = t[motor_name]
                mod      = SkewedGaussianModel()
                pars     = mod.guess(signal, x=pitch)
                out      = mod.fit(signal, pars, x=pitch)
                print(whisper(out.fit_report(min_correl=0)))
                out.plot()
                top      = out.params['center'].value
            else:
                position = peak(signal)
                top      = t[motor.name][position]
            
            thisagg = matplotlib.get_backend()
            matplotlib.use('Agg') # produce a plot without screen display
            out.plot()
            if filename is None:
                filename = os.path.join(user_ns['BMMuser'].folder, 'snapshots', 'toss.png')
            plt.savefig(filename)
            matplotlib.use(thisagg) # return to screen display
            clean_img()
            BMMuser.display_img = Image.open(os.path.join(user_ns['BMMuser'].folder, 'snapshots', 'toss.png'))
            BMMuser.display_img.show()
            
            yield from mv(motor, top)
            print(bold_msg(f'Found peak at {motor.name} = {motor.position}'))
            for k in ('center1', 'center2', 'sigma1', 'sigma2', 'amplitude', 'midpoint'):
                rkvs.set(f'BMM:lmfit:{k}', out.params[k].value)

        yield from doscan(filename)
        
    def cleanup_plan():
        yield from resting_state_plan()
    
    user_ns['RE'].msg_hook = None
    yield from finalize_wrapper(main_plan(motor, start, stop, nsteps, detector, find, filename), cleanup_plan())
    user_ns['RE'].msg_hook = BMM_msg_hook


    

##                     linear stages        tilt stage           rotation stages
motor_nicknames = {'x'    : xafs_x,     'roll' : xafs_roll,
                   'y'    : xafs_y,     'pitch': xafs_pitch, 'wh' : xafs_wheel,
                   's'    : xafs_lins,  'p'    : xafs_pitch, 'rs' : xafs_rots,
                   'xs'   : xafs_linxs, 'r'    : xafs_roll,
               }

## before 29 August 2018, the order of arguments for linescan() was
##   linescan(axis, detector, ...)
## now it is
##   linescan(detector, axis, ...)
## for consistency with areascan().  This does a simple check to see if the old
## argument order is being used and swaps them if need be
def ls_backwards_compatibility(detin, axin):
    if type(axin) is str and axin.capitalize() in ('It', 'If', 'I0', 'Iy', 'Ir', 'Both', 'I0a', 'I0b', 'Ic0', 'Ic1', 'Xs', 'Xs1'):
        return(axin, detin)
    else:
        return(detin, axin)


#mytable = None
####################################
# generic linescan vs. It/If/Ir/I0 #
####################################
def linescan(detector, axis, start, stop, nsteps, dopluck=True, force=False, inttime=0.1, md={}): # integration time?
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
    dopluck : bool, optional
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

    def main_plan(detector, axis, start, stop, nsteps, dopluck, force, md):
        if force is False:
            (ok, text) = BMM_clear_to_start()
            if ok is False:
                print(error_msg(text))
                yield from null()
                return

        detector, axis = ls_backwards_compatibility(detector, axis)
        # print('detector is: ' + str(detector))
        # print('axis is: ' + str(axis))
        # return(yield from null())

        user_ns['RE'].msg_hook = None
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

        current = thismotor.position
        if current+start < thismotor.limits[0]:
            print(error_msg(f'These scan parameters will take {thismotor.name} outside it\'s lower limit of {thismotor.limits[0]}'))
            print(whisper(f'(starting position = {thismotor.position})'))
            return(yield from null())
        if current+stop > thismotor.limits[1]:
            print(error_msg(f'These scan parameters will take {thismotor.name} outside it\'s upper limit of {thismotor.limits[1]}'))
            print(whisper(f'(starting position = {thismotor.position})'))
            return(yield from null())

        BMMuser.motor = thismotor

        # sanity checks on detector
        if detector not in ('It', 'If', 'I0', 'Iy', 'Ir', 'Both', 'Bicron', 'Ic0', 'Ic1', 'Xs', 'Xs1'):
            print(error_msg('\n*** %s is not a linescan measurement (%s)\n' %
                            (detector, 'it, if, i0, iy, ir, both, bicron, Ic0, Ic1, xs, xs1')))
            yield from null()
            return

        yield from mv(_locked_dwell_time, inttime)
        if detector == 'Xs':
            yield from mv(xs.cam.acquire_time, inttime)
            yield from mv(xs.total_points, nsteps)
        dets  = [quadem1, ic0, ]
        denominator = ''
        detname = ''

        # If should be xs when using Xspress3
        if with_xspress3 and detector == 'If':
            detector = 'Xs'
        
        # func is an anonymous function, built on the fly, for feeding to DerivedPlot
        if detector == 'It':
            denominator = ' / I0'
            detname = 'transmission'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['It']/doc['data']['I0'])
        elif detector == 'I0a' and ic0 is not None:
            dets.append(ic0)
            denominator = ' / I0'
            detname = 'I0a'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['I0a']/doc['data']['I0'])
        elif detector == 'I0b' and ic0 is not None:
            dets.append(ic0)
            denominator = ' / I0'
            detname = 'I0b'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['I0b']/doc['data']['I0'])
        elif detector == 'Ir':
            #denominator = ' / It'
            detname = 'reference'
            #func = lambda doc: (doc['data'][thismotor.name], doc['data']['Ir']/doc['data']['It'])
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['Ir'])
        elif detector == 'I0':
            detname = 'I0'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['I0'])
        elif detector == 'Bicron':
            dets.append(vor)
            detname = 'Bicron'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['Bicron'])
        elif detector == 'Iy':
            denominator = ' / I0'
            detname = 'electron yield'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['Iy']/doc['data']['I0'])
        elif detector == 'If':
            dets.append(vor)
            denominator = ' / I0'
            detname = 'fluorescence'
            func = lambda doc: (doc['data'][thismotor.name],
                                (doc['data'][BMMuser.dtc1] +
                                 doc['data'][BMMuser.dtc2] +
                                 doc['data'][BMMuser.dtc3] +
                                 doc['data'][BMMuser.dtc4]   ) / doc['data']['I0'])
        elif detector == 'Xs':
            dets.append(xs)
            denominator = ' / I0'
            detname = 'fluorescence'
            func = lambda doc: (doc['data'][thismotor.name],
                                (doc['data'][BMMuser.xs1] +
                                 doc['data'][BMMuser.xs2] +
                                 doc['data'][BMMuser.xs3] +
                                 doc['data'][BMMuser.xs4] ) / doc['data']['I0'])
            yield from mv(xs.total_points, nsteps) # Xspress3 demands that this be set up front

        elif detector == 'Xs1':
            dets.append(xs1)
            denominator = ' / I0'
            detname = 'fluorescence'
            func = lambda doc: (doc['data'][thismotor.name],
                                doc['data'][BMMuser.xs8] / doc['data']['I0'])
            yield from mv(xs1.total_points, nsteps) # Xspress3 demands that this be set up front

        elif detector == 'Ic0':
            funcia = lambda doc: (doc['data'][thismotor.name], doc['data']['I0a'])
            funcib = lambda doc: (doc['data'][thismotor.name], doc['data']['I0b'])

        elif detector == 'Ic1':
            dets.append(ic1)
            funcia = lambda doc: (doc['data'][thismotor.name], doc['data']['Ita'])
            funcib = lambda doc: (doc['data'][thismotor.name], doc['data']['Itb'])

        ## need a "Both" for trans + xs !!!!!!!!!!
        elif detector == 'Both':
            dets.append(vor)
            functr = lambda doc: (doc['data'][thismotor.name], doc['data']['It']/doc['data']['I0'])
            funcfl = lambda doc: (doc['data'][thismotor.name],
                                  (doc['data'][BMMuser.dtc1] +
                                   doc['data'][BMMuser.dtc2] +
                                   doc['data'][BMMuser.dtc3] +
                                   doc['data'][BMMuser.dtc4]   ) / doc['data']['I0'])
        ## and this is the appropriate way to plot this linescan

        #mv(_locked_dwell_time, 0.5)
        if detector == 'Both':
            plot = [DerivedPlot(funcfl, xlabel=thismotor.name, ylabel='If/I0', title='fluorescence vs. %s' % thismotor.name),
                    DerivedPlot(functr, xlabel=thismotor.name, ylabel='It/I0', title='transmission vs. %s' % thismotor.name)]
        elif detector == 'Ic0':
            plot = [DerivedPlot(funcia, xlabel=thismotor.name, ylabel='I0a', title='I0a vs. %s' % thismotor.name),
                    DerivedPlot(funcib, xlabel=thismotor.name, ylabel='I0b', title='I0b vs. %s' % thismotor.name)]
        elif detector == 'Ic1':
            plot = [DerivedPlot(funcia, xlabel=thismotor.name, ylabel='Ita', title='Ita vs. %s' % thismotor.name),
                    DerivedPlot(funcib, xlabel=thismotor.name, ylabel='Itb', title='Itb vs. %s' % thismotor.name)]
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
        #if 'purpose' not in md:
        #    md['purpose'] = 'alignment'

        if 'BMM_kafka' not in md:
            md['BMM_kafka'] = dict()
        if 'hint' not in md['BMM_kafka'] or thismotor.name not in md['BMM_kafka']['hint']:
            md['BMM_kafka']['hint'] = f'linescan {detector} {thismotor.name}'
        kafka_message({'linescan': 'start',
                       'motor' : thismotor.name,
                       'detector' : detector,})
            
        rkvs.set('BMM:scan:type',      'line')
        rkvs.set('BMM:scan:starttime', str(datetime.datetime.timestamp(datetime.datetime.now())))
        rkvs.set('BMM:scan:estimated', 0)

        ## This helped Bruce understand how to make a decorator conditional:
        ## https://stackoverflow.com/a/49204061
        def conditional_subs_decorator(function):
            if user_ns['BMMuser'].enable_live_plots is True:
                return subs_decorator(plot)(function)
            else:
                return function
        
        @conditional_subs_decorator
        def scan_xafs_motor(dets, motor, start, stop, nsteps):
            uid = yield from rel_scan(dets, motor, start, stop, nsteps, md={**thismd, **md, 'plan_name' : f'rel_scan linescan {motor.name} {detector}'})
            return uid

        uid = yield from scan_xafs_motor(dets, thismotor, start, stop, nsteps)
        kafka_message({'linescan': 'stop',})
        
        BMM_log_info('linescan: %s\tuid = %s, scan_id = %d' %
                     (line1, uid, user_ns['db'][-1].start['scan_id']))
        if dopluck is True:
            action = input('\n' + bold_msg('Pluck motor position from the plot? ' + PROMPT))
            if action != '':
                if action[0].lower() == 'n' or action[0].lower() == 'q':
                    return(yield from null())
            yield from pluck(suggested_motor=thismotor)
            #yield from move_after_scan(thismotor)
            ## right here... put UID and plucked value in a store of some sort
            if user_ns["BMMuser"].mouse_click is not None:
                with open('/home/xf06bm/Data/bucket/linescan_evaluation.txt', 'a') as f:
                    f.write(f'''{now()}
     mode = {thismotor.name}/{detector}
     uid = {uid}
     position = {user_ns["BMMuser"].mouse_click}

''')

    
    def cleanup_plan():
        yield from resting_state_plan()


    #RE, BMMuser, rkvs = user_ns['RE'], user_ns['BMMuser'], user_ns['rkvs']
    #try:
    #    xs = user_ns['xs']
    #except:
    #    pass
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
    user_ns['RE'].msg_hook = None
    yield from finalize_wrapper(main_plan(detector, axis, start, stop, nsteps, dopluck, force, md), cleanup_plan())
    user_ns['RE'].msg_hook = BMM_msg_hook



#############################################################
# extract a linescan from the database, write an ascii file #
#############################################################
def ls2dat(datafile, key):
    '''
    Export a linescan database entry to a simple column data file.

      ls2dat('/path/to/myfile.dat', '0783ac3a-658b-44b0-bba5-ed4e0c4e7216')

    or

      ls2dat('/path/to/myfile.dat', 1533)

    The arguments are a data file name and the database key.
    '''
    #BMMuser, db = user_ns['BMMuser'], user_ns['db']
    if os.path.isfile(datafile):
        print(error_msg('%s already exists!  Bailing out....' % datafile))
        return
    handle = open(datafile, 'w')
    dataframe = user_ns['db'][key]
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
    elif 'Ic0' in devices:
        abscissa = dataframe['start']['motors'][0]
        column_list = [abscissa, 'I0a', 'I0b',]
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


# def center_sample_y():
#     yield from linescan('it', xafs_liny, -1.5, 1.5, 61, pluck=False)
#     table = user_ns['db'][-1].table()
#     diff = -1 * table['It'].diff()
#     inflection = table['xafs_liny'][diff.idxmax()]
#     yield from mv(xafs_liny, inflection)
#     print(bold_msg('Optimal position in y at %.3f' % inflection))

# def center_sample_roll():
#     yield from linescan('it', xafs_roll, -3, 3, 61, pluck=False)
#     table = user_ns['db'][-1].table()
#     peak = table['xafs_roll'][table['It'].idxmax()]
#     yield from mv(xafs_roll, peak)
#     print(bold_msg('Optimal position in roll at %.3f' % peak))

# def align_flat_sample(angle=0):
#     yield from center_sample_y()
#     yield from center_sample_roll()
#     yield from center_sample_y()
#     yield from center_sample_roll()
#     yield from mvr(xafs_roll, angle)
