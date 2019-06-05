import bluesky as bs
import bluesky.plans as bp
import bluesky.plan_stubs as bps
from bluesky import __version__ as bluesky_version
import numpy
import os

from bluesky.preprocessors import subs_decorator
## see 65-derivedplot.py for DerivedPlot class
## see 10-motors.py and 20-dcm.py for motor definitions

run_report(__file__)

def resting_state():
    BMMuser.prompt = True
    quadem1.on()
    vor.on()
    _locked_dwell_time.set(0.5)
    RE.msg_hook = BMM_msg_hook
def resting_state_plan():
    #BMMuser.prompt = True
    #yield from quadem1.on_plan()
    #yield from vor.on_plan()
    yield from abs_set(_locked_dwell_time, 0.5)
    RE.msg_hook = BMM_msg_hook
def end_of_macro():
    BMMuser.prompt = True
    yield from quadem1.on_plan()
    yield from vor.on_plan()
    yield from abs_set(_locked_dwell_time, 0.5)
    RE.msg_hook = BMM_msg_hook


    
def move_after_scan(thismotor):
    '''
    Call this to pluck a point from a plot and move the plotted motor to that x-value.
    '''
    if BMMuser.motor is None:
        print(error_msg('\nThere\'s not a current plot on screen.\n'))
        return(yield from null())
    if thismotor is not BMMuser.motor:
        print(error_msg('\nThe motor you are asking to move is not the motor in the current plot.\n'))
        return(yield from null())
    print('Single click the left mouse button on the plot to pluck a point...')
    cid = BMMuser.fig.canvas.mpl_connect('button_press_event', interpret_click) # see 65-derivedplot.py and
    while BMMuser.x is None:                            #  https://matplotlib.org/users/event_handling.html
        yield from sleep(0.5)
    if BMMuser.motor2 is None:
        yield from mv(thismotor, BMMuser.x)
    else:
        print('%.3f  %.3f' % (BMMuser.x, BMMuser.y))
        #yield from mv(BMMuser.motor, BMMuser.x, BMMuser.motor2, BMMuser.y)
    cid = BMMuser.fig.canvas.mpl_disconnect(cid)
    BMMuser.x = BMMuser.y = None

def pluck():
    '''
    Call this to pluck a point from the most recent plot and move the motor to that point.
    '''
    yield from move_after_scan(BMMuser.motor)

from scipy.ndimage import center_of_mass
def com(signal):
    '''Return the center of mass of a 1D array. This is used to find the
    center of rocking curve and slit height scans.'''
    return int(center_of_mass(signal)[0])

def slit_height(start=-1.5, stop=1.5, nsteps=31, move=False, sleep=1.0):
    '''Perform a relative scan of the DM3 BCT motor around the current
    position to find the optimal position for slits3. Optionally, the
    motor will moved to the center of mass of the peak at the end of
    the scan.

    Input:
      start:   (float) starting position relative to current                         [-3.0]
      end:     (float) ending position relative to current                           [3.0]
      nsteps:  (int) number of steps                                                 [61]
      move:    (Boolean) True=move to position of max signal, False=pluck and move   [False]
      sleep:   (float) length of sleep before trying to move dm3_bct                 [3.0]

    '''

    def main_plan(start, stop, nsteps, move):
        (ok, text) = BMM_clear_to_start()
        if ok is False:
            print(error_msg(text))
            yield from null()
            return

        RE.msg_hook = None
        BMMuser.motor = dm3_bct
        func = lambda doc: (doc['data'][motor.name], doc['data']['I0'])
        plot = DerivedPlot(func, xlabel=motor.name, ylabel='I0', title='I0 signal vs. slit height')
        line1 = '%s, %s, %.3f, %.3f, %d -- starting at %.3f\n' % \
                (motor.name, 'i0', start, stop, nsteps, motor.user_readback.value)
        with open(dotfile, "w") as f:
            f.write("")

        @subs_decorator(plot)
        def scan_slit():

            yield from abs_set(quadem1.averaging_time, 0.1)
            yield from abs_set(motor.velocity, 0.6)
            yield from abs_set(motor.kill_cmd, 1)

            yield from rel_scan([quadem1], motor, start, stop, nsteps)

            RE.msg_hook = BMM_msg_hook
            BMM_log_info('slit height scan: %s\tuid = %s, scan_id = %d' %
                         (line1, db[-1].start['uid'], db[-1].start['scan_id']))
            if move:
                t  = db[-1].table()
                signal = t['I0']
                position = com(signal)
                top = t[motor.name][position]
                
                yield from bps.sleep(sleep)
                yield from abs_set(motor.kill_cmd, 1)
                yield from mv(motor, top)

            else:
                action = input('\n' + bold_msg('Pluck motor position from the plot? [Y/n then Enter] '))
                if action.lower() == 'n' or action.lower() == 'q':
                    return(yield from null())
                yield from bps.sleep(sleep)
                yield from abs_set(motor.kill_cmd, 1)
                yield from move_after_scan(dm3_bct)
            yield from abs_set(quadem1.averaging_time, 0.5)
        yield from scan_slit()

    def cleanup_plan():
        yield from abs_set(_locked_dwell_time, 0.5)
        yield from bps.sleep(sleep)
        yield from abs_set(motor.kill_cmd, 1)
        yield from resting_state_plan()
        if os.path.isfile(dotfile): os.remove(dotfile)

    motor = dm3_bct
    dotfile = '/home/xf06bm/Data/.line.scan.running'
    RE.msg_hook = None
    yield from bluesky.preprocessors.finalize_wrapper(main_plan(start, stop, nsteps, move), cleanup_plan())
    RE.msg_hook = BMM_msg_hook


def rocking_curve(start=-0.10, stop=0.10, nsteps=101, detector='I0'):
    '''
    Perform a relative scan of the DCM 2nd crystal pitch around the current
    position to find the peak of the crystal rocking curve.  Begin by opening
    the hutch slits to 3 mm. At the end, move to the position of maximum 
    intensity on I0, then return to the hutch slits to their original height.

    Input:
      start:    (float) starting position relative to current  [-0.1]
      end:      (float) ending position relative to current    [0.1]
      nsteps:   (int) number of steps                          [101]
      detector: (string) 'I0' or 'Bicron'                      ['I0']
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

        with open(dotfile, "w") as f:
            f.write("")

        @subs_decorator(plot)
        def scan_dcmpitch(sgnl):
            line1 = '%s, %s, %.3f, %.3f, %d -- starting at %.3f\n' % \
                    (motor.name, sgnl, start, stop, nsteps, motor.user_readback.value)

            yield from abs_set(_locked_dwell_time, 0.1)
            yield from abs_set(motor.kill_cmd, 1)

            yield from mv(slits3.vsize, 3)
            if sgnl == 'Bicron':
                yield from mv(slitsg.vsize, 5)
                
            yield from rel_scan(dets, motor, start, stop, nsteps)
            #yield from rel_adaptive_scan(dets, 'I0', motor,
            #                             start=start,
            #                             stop=stop,
            #                             min_step=0.002,
            #                             max_step=0.03,
            #                             target_delta=.15,
            #                             backstep=True)
            t  = db[-1].table()
            signal = t[sgnl]
            position = com(signal)
            top = t[motor.name][position]

            yield from bps.sleep(3.0)
            yield from abs_set(motor.kill_cmd, 1)
            RE.msg_hook = BMM_msg_hook

            BMM_log_info('rocking curve scan: %s\tuid = %s, scan_id = %d' %
                         (line1, db[-1].start['uid'], db[-1].start['scan_id']))
            yield from mv(motor, top)
            if sgnl == 'Bicron':
                yield from mv(slitsg.vsize, gonio_slit_height)
        yield from scan_dcmpitch(sgnl)

    def cleanup_plan():
        yield from mv(slits3.vsize, slit_height)
        yield from abs_set(_locked_dwell_time, 0.5)
        yield from bps.sleep(1.0)
        yield from abs_set(motor.kill_cmd, 1)
        yield from bps.sleep(1.0)
        yield from resting_state_plan()
        if os.path.isfile(dotfile): os.remove(dotfile)

    motor = dcm_pitch
    dotfile = '/home/xf06bm/Data/.line.scan.running'
    slit_height = slits3.vsize.readback.value
    gonio_slit_height = slitsg.vsize.readback.value
    RE.msg_hook = None
    yield from bluesky.preprocessors.finalize_wrapper(main_plan(start, stop, nsteps, detector), cleanup_plan())
    RE.msg_hook = BMM_msg_hook


##                     linear stages        tilt stage           rotation stages
motor_nicknames = {'x'    : xafs_x,     'roll' : xafs_roll,  'rh' : xafs_roth,
                   'y'    : xafs_y,     'pitch': xafs_pitch, 'wh' : xafs_wheel,
                   's'    : xafs_lins,  'p'    : xafs_pitch, 'rs' : xafs_rots,
                   'ref'  : xafs_ref,   'r'    : xafs_roll,
               }

## before 29 August 2018, the order of arguments for linescan() was
##   linescan(axis, detector, ...)
## now it is
##   linescan(detector, axis, ...)
## for consistency with areascan().  This does a simple check to see if the old
## argument order is being used and swaps them if need be
def ls_backwards_compatibility(detin, axin):
    if type(axin) is str and axin.capitalize() in ('It', 'If', 'I0', 'Iy', 'Ir', 'Both'):
        return(axin, detin)
    else:
        return(detin, axin)


####################################
# generic linescan vs. It/If/Ir/I0 #
####################################
def linescan(detector, axis, start, stop, nsteps, pluck=True, force=False, md={}): # integration time?
    '''
    Generic linescan plan.  This is a RELATIVE scan, relative to the
    current position of the selected motor.

    For example:
       RE(linescan('it', 'x', -1, 1, 21))

       detector: detector to display -- if, it, ir, or i0
       axis :    motor or nickname
       start:    starting value for a relative scan
       stop:     ending value for a relative scan
       nsteps:   number of steps in scan
       pluck:    flag for whether to offer to pluck & move motor
       force:    flag for forcing a scan even if not clear to start

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
        if axis not in motor_nicknames.keys() and 'EpicsMotor' not in str(type(axis)) and 'PseudoSingle' not in str(type(axis)):
            print(error_msg('\n*** %s is not a linescan motor (%s)\n' %
                          (axis, str.join(', ', motor_nicknames.keys()))))
            yield from null()
            return

        if 'EpicsMotor' in str(type(axis)):
            thismotor = axis
        elif 'PseudoSingle' in str(type(axis)):
            thismotor = axis
        else:                       # presume it's an xafs_XXXX motor
            thismotor = motor_nicknames[axis]
        BMMuser.motor = thismotor

        ## sanity checks on detector
        if detector not in ('It', 'If', 'I0', 'Iy', 'Ir', 'Both', 'Bicron'):
            print(error_msg('\n*** %s is not a linescan measurement (%s)\n' %
                            (detector, 'it, if, i0, iy, ir, both, bicron')))
            yield from null()
            return

        yield from abs_set(_locked_dwell_time, 0.1)
        dets  = [quadem1,]
        denominator = ''
        detname = ''
        
        ## func is an anonymous function, built on the fly, for feeding to DerivedPlot
        if detector == 'It':
            denominator = ' / I0'
            detname = 'transmission'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['It']/doc['data']['I0'])
        elif detector == 'Ir':
            denominator = ' / It'
            detname = 'reference'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['Ir']/doc['data']['It'])
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
        elif detector == 'Both':
            dets.append(vor)
            functr = lambda doc: (doc['data'][thismotor.name], doc['data']['It']/doc['data']['I0'])
            funcfl = lambda doc: (doc['data'][thismotor.name],
                                  (doc['data'][BMMuser.dtc1] +
                                   doc['data'][BMMuser.dtc2] +
                                   doc['data'][BMMuser.dtc3] +
                                   doc['data'][BMMuser.dtc4]   ) / doc['data']['I0'])
        ## and this is the appropriate way to plot this linescan
        if detector == 'Both':
            plot = [DerivedPlot(funcfl, xlabel=thismotor.name, ylabel='If/I0', title='fluorescence vs. %s' % thismotor.name),
                    DerivedPlot(functr, xlabel=thismotor.name, ylabel='It/I0', title='transmission vs. %s' % thismotor.name)]
        else:
            plot = DerivedPlot(func,
                               xlabel=thismotor.name,
                               ylabel=detector+denominator,
                               title='%s vs. %s' % (detname, thismotor.name))

        if 'PseudoSingle' in str(type(axis)):
            value = thismotor.readback.value
        else:
            value = thismotor.user_readback.value
        line1 = '%s, %s, %.3f, %.3f, %d -- starting at %.3f\n' % \
                (thismotor.name, detector, start, stop, nsteps, value)
        ##BMM_suspenders()            # engage suspenders

        thismd = dict()
        thismd['XDI'] = dict()
        thismd['XDI']['Facility'] = dict()
        thismd['XDI']['Facility']['GUP'] = BMMuser.gup
        thismd['XDI']['Facility']['SAF'] = BMMuser.saf

        with open(dotfile, "w") as f:
            f.write("")
                
    
        @subs_decorator(plot)
        def scan_xafs_motor(dets, motor, start, stop, nsteps):
            yield from rel_scan(dets, motor, start, stop, nsteps, md={**thismd, **md})

        yield from scan_xafs_motor(dets, thismotor, start, stop, nsteps)
        BMM_log_info('linescan: %s\tuid = %s, scan_id = %d' %
                     (line1, db[-1].start['uid'], db[-1].start['scan_id']))
        if pluck is True:
            action = input('\n' + bold_msg('Pluck motor position from the plot? [Y/n then Enter] '))
            if action.lower() == 'n' or action.lower() == 'q':
                return(yield from null())
            yield from move_after_scan(thismotor)

    
    def cleanup_plan():
        if os.path.isfile(dotfile): os.remove(dotfile)
        ##RE.clear_suspenders()       # disable suspenders
        yield from resting_state_plan()


    dotfile = '/home/xf06bm/Data/.line.scan.running'
    RE.msg_hook = None
    yield from bluesky.preprocessors.finalize_wrapper(main_plan(detector, axis, start, stop, nsteps, pluck, force), cleanup_plan())
    RE.msg_hook = BMM_msg_hook



#############################################################
# extract a linescan from the database, write an ascii file #
#############################################################
def ls2dat(datafile, key):
    '''
    Export a linescan database entry to a simple column data file.

      ls2dat('/path/to/myfile.dat', 1533)

    or

      ls2dat('/path/to/myfile.dat', '0783ac3a-658b-44b0-bba5-ed4e0c4e7216')

    The arguments are a data file name and the database key.
    '''
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
    else:
        abscissa = dataframe['start']['motors'][0]
        template = "  %.3f  %.6f  %.6f  %.6f\n"
        column_list = [abscissa, 'I0', 'It', 'Ir']

    print(column_list)
    table = dataframe.table()
    this = table.loc[:,column_list]

    handle.write('# XDI/1.0 BlueSky/%s\n' % bluesky_version)
    handle.write('# Scan.uid: %s\n' % dataframe['start']['uid'])
    handle.write('# Scan.transient_id: %d\n' % dataframe['start']['scan_id'])
    try:
        handle.write('# Facility.GUP: %d\n' % dataframe['start']['XDI']['Facility']['GUP'])
    except:
        pass
    try:
        handle.write('# Facility.SAF: %d\n' % dataframe['start']['XDI']['Facility']['SAF'])
    except:
        pass
    handle.write('# ==========================================================\n')
    handle.write('# ' + '  '.join(column_list) + '\n')
    for i in range(0,len(this)):
        handle.write(template % tuple(this.iloc[i]))
    handle.flush()
    handle.close()
    print(bold_msg('wrote linescan to %s' % datafile))


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

def align_flat_sample(angle=2):
    yield from center_sample_y()
    yield from center_sample_roll()
    yield from center_sample_y()
    yield from center_sample_roll()
    yield from mv(xafs_roll, angle)
