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

def move_after_scan(thismotor):
    '''
    Call this to pluck a point from a plot and move the plotted motor to that x-value.
    '''
    if BMM_cpl.motor is None:
        print(colored('\nThere\'s not a current plot on screen.\n', 'lightred'))
        return(yield from null())
    if thismotor is not BMM_cpl.motor:
        print(colored('\nThe motor you are asking to move is not the motor in the current plot.\n',
                      'lightred'))
        return(yield from null())
    print('Single click the left mouse button on the plot to pluck a point...')
    cid = BMM_cpl.fig.canvas.mpl_connect('button_press_event', interpret_click) # see 65-derivedplot.py and
    while BMM_cpl.x is None:                            #  https://matplotlib.org/users/event_handling.html
        yield from sleep(0.5)
    if BMM_cpl.motor2 is None:
        yield from mv(thismotor, BMM_cpl.x)
    else:
        print('%.3f  %.3f' % (BMM_cpl.x, BMM_cpl.y))
        #yield from mv(BMM_cpl.motor, BMM_cpl.x, BMM_cpl.motor2, BMM_cpl.y)
    cid = BMM_cpl.fig.canvas.mpl_disconnect(cid)
    BMM_cpl.x = BMM_cpl.y = None

def pluck():
    '''
    Call this to pluck a point from the most recent plot and move the motor to that point.
    '''
    yield from move_after_scan(BMM_cpl.motor)

from scipy.ndimage import center_of_mass
def com(signal):
    '''Return the center of mass of a 1D array. This is used to find the
    center of rocking curve and slit height scans.'''
    return int(center_of_mass(signal)[0])

def slit_height(start=-2.5, stop=2.5, nsteps=51, move=False, sleep=1.0):
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
            print(colored(text, 'lightred'))
            yield from null()
            return

        RE.msg_hook = None
        BMM_cpl.motor = dm3_bct
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
                action = input('\n' + colored('Pluck motor position from the plot? [Y/n then Enter] ', 'white'))
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
            print(colored(text, 'lightred'))
            yield from null()
            return

        RE.msg_hook = None
        BMM_cpl.motor = motor
    
        func = lambda doc: (doc['data'][motor.name], doc['data']['I0'])
        dets = [quadem1,]
        name = 'I0'
        if detector.lower() == 'bicron':
            func = lambda doc: (doc['data'][motor.name], doc['data']['Bicron'])
            dets = [bicron,]
            name = 'Bicron'
        plot = DerivedPlot(func, xlabel=motor.name, ylabel=name, title='I0 signal vs. DCM 2nd crystal pitch')

        with open(dotfile, "w") as f:
            f.write("")

        @subs_decorator(plot)
        def scan_dcmpitch():
            line1 = '%s, %s, %.3f, %.3f, %d -- starting at %.3f\n' % \
                    (motor.name, 'i0', start, stop, nsteps, motor.user_readback.value)

            yield from abs_set(_locked_dwell_time, 0.1)
            yield from abs_set(motor.kill_cmd, 1)

            yield from mv(slits3.vsize, 3)
            yield from rel_scan(dets, motor, start, stop, nsteps)

            t  = db[-1].table()
            signal = t['I0']
            position = com(signal)
            top = t[motor.name][position]

            yield from bps.sleep(3.0)
            yield from abs_set(motor.kill_cmd, 1)
            RE.msg_hook = BMM_msg_hook
            BMM_log_info('rocking curve scan: %s\tuid = %s, scan_id = %d' %
                         (line1, db[-1].start['uid'], db[-1].start['scan_id']))
            yield from mv(motor, top)
        yield from scan_dcmpitch()

    def cleanup_plan():
        yield from mv(slits3.vsize, slit_height)
        yield from abs_set(_locked_dwell_time, 0.5)
        yield from bps.sleep(1.0)
        yield from abs_set(motor.kill_cmd, 1)
        yield from bps.sleep(1.0)
        if os.path.isfile(dotfile): os.remove(dotfile)

    motor = dcm_pitch
    dotfile = '/home/xf06bm/Data/.line.scan.running'
    slit_height = slits3.vsize.readback.value
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
    if type(axin) is str and axin.capitalize() in ('It', 'If', 'I0', 'Iy', 'Ir'):
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
            print(colored(text, 'lightred'))
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
            print(colored('\n*** %s is not a linescan motor (%s)\n' %
                          (axis, str.join(', ', motor_nicknames.keys())), 'lightred'))
            yield from null()
            return

        if 'EpicsMotor' in str(type(axis)):
            thismotor = axis
        elif 'PseudoSingle' in str(type(axis)):
            thismotor = axis
        else:                       # presume it's an xafs_XXXX motor
            thismotor = motor_nicknames[axis]
        BMM_cpl.motor = thismotor

        ## sanity checks on detector
        if detector not in ('It', 'If', 'I0', 'Iy', 'Ir', 'Both'):
            print(colored('\n*** %s is not a linescan measurement (%s)\n' %
                          (detector, 'it, if, i0, iy, ir, both'), 'lightred'))
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
        elif detector == 'Iy':
            denominator = ' / I0'
            detname = 'electron yield'
            func = lambda doc: (doc['data'][thismotor.name], doc['data']['Iy']/doc['data']['I0'])
        elif detector == 'If':
            dets.append(vor)
            denominator = ' / I0'
            detname = 'fluorescence'
            func = lambda doc: (doc['data'][thismotor.name],
                                (doc['data']['DTC1'] +
                                 doc['data']['DTC2'] +
                                 doc['data']['DTC3'] +
                                 doc['data']['DTC4']   ) / doc['data']['I0'])
        elif detector == 'Both':
            dets.append(vor)
            functr = lambda doc: (doc['data'][thismotor.name], doc['data']['It']/doc['data']['I0'])
            funcfl = lambda doc: (doc['data'][thismotor.name],
                                  (doc['data']['DTC1'] +
                                   doc['data']['DTC2'] +
                                   doc['data']['DTC3'] +
                                   doc['data']['DTC4']   ) / doc['data']['I0'])
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
        thismd['XDI,Facility,GUP'] = BMM_xsp.gup
        thismd['XDI,Facility,SAF'] = BMM_xsp.saf

        with open(dotfile, "w") as f:
            f.write("")
                
    
        @subs_decorator(plot)
        def scan_xafs_motor(dets, motor, start, stop, nsteps):
            yield from rel_scan(dets, motor, start, stop, nsteps, md={**thismd, **md})

        yield from scan_xafs_motor(dets, thismotor, start, stop, nsteps)
        BMM_log_info('linescan: %s\tuid = %s, scan_id = %d' %
                     (line1, db[-1].start['uid'], db[-1].start['scan_id']))
        if pluck is True:
            action = input('\n' + colored('Pluck motor position from the plot? [Y/n then Enter] ', 'white'))
            if action.lower() == 'n' or action.lower() == 'q':
                return(yield from null())
            yield from move_after_scan(thismotor)

    
    def cleanup_plan():
        if os.path.isfile(dotfile): os.remove(dotfile)
        ##RE.clear_suspenders()       # disable suspenders
        yield from abs_set(_locked_dwell_time, 0.5)


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
        print(colored('%s already exists!  Bailing out....' % datafile, 'lightred'))
        return
    handle = open(datafile, 'w')
    dataframe = db[key]
    devices = dataframe.devices() # note: this is a _set_ (this is helpful: https://snakify.org/en/lessons/sets/)
    if 'vor' in devices:
        abscissa = (devices - {'quadem1', 'vor'}).pop()
        abscissa = 'xafs_liny'
        column_list = [abscissa, 'I0', 'It', 'Ir',
                       'DTC1', 'DTC2', 'DTC3', 'DTC4',
                       'ROI1', 'ICR1', 'OCR1',
                       'ROI2', 'ICR2', 'OCR2',
                       'ROI3', 'ICR3', 'OCR3',
                       'ROI4', 'ICR4', 'OCR4']
        template = "  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f\n"
    else:
        abscissa = (devices - {'quadem1',}).pop()
        template = "  %.3f  %.6f  %.6f  %.6f\n"
        column_list = [abscissa, 'I0', 'It', 'Ir']

    table = dataframe.table()
    this = table.loc[:,column_list]

    handle.write('# XDI/1.0 BlueSky/%s' % bluesky_version)
    handle.write('# Scan.uid: %s\n' % dataframe['start']['uid'])
    handle.write('# Scan.transient_id: %d\n' % dataframe['start']['scan_id'])
    try:
        handle.write('# Facility.GUP: %d\n' % dataframe['start']['XDI,Facility,GUP'])
    except:
        pass
    try:
        handle.write('# Facility.SAF: %d\n' % dataframe['start']['XDI,Facility,SAF'])
    except:
        pass
    handle.write('# ==========================================================\n')
    handle.write('# ' + '  '.join(column_list) + '\n')
    for i in range(0,len(this)):
        handle.write(template % tuple(this.iloc[i]))
    handle.flush()
    handle.close()
    print(colored('wrote linescan to %s' % datafile, 'white'))


def center_sample_y():
    yield from linescan('it', xafs_liny, -1.5, 1.5, 61, pluck=False)
    table = db[-1].table()
    diff = -1 * table['It'].diff()
    inflection = table['xafs_liny'][diff.idxmax()]
    yield from mv(xafs_liny, inflection)
    print(colored('Optimal position in y at %.3f' % inflection, 'white'))

def center_sample_roll():
    yield from linescan('it', xafs_roll, -3, 3, 61, pluck=False)
    table = db[-1].table()
    peak = table['xafs_roll'][table['It'].idxmax()]
    yield from mv(xafs_roll, peak)
    print(colored('Optimal position in roll at %.3f' % peak, 'white'))

def align_flat_sample(angle=2):
    yield from center_sample_y()
    yield from center_sample_roll()
    yield from center_sample_y()
    yield from center_sample_roll()
    yield from mv(xafs_roll, angle)
