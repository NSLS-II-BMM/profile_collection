
import bluesky as bs
import bluesky.plans as bp
import bluesky.plan_stubs as bps
from bluesky.callbacks import LiveGrid
import numpy
import os

from bluesky.preprocessors import subs_decorator
## see 65-derivedplot.py for DerivedPlot class
## see 10-motors.py and 20-dcm.py for motor definitions

run_report(__file__)


def areascan(detector,
             slow, startslow, stopslow, nslow,
             fast, startfast, stopfast, nfast,
             pluck=True, force=False, dwell=0.1, md={}):
    '''
    Generic areascan plan.  This is a RELATIVE scan, relative to the
    current positions of the selected motors.

    For example:
       RE(areascan('it', 'x', -1, 1, 21, 'y', -0.5, 0.5, 11))

       detector: detector to display -- if, it, ir, or i0
       slow:     slow axis motor or nickname
       sl1:      starting value for slow axis of a relative scan
       sl2:      ending value for slow axis of a relative scan
       nsl:      number of steps in slow axis
       fast:     fast axis motor or nickname
       fa1:      starting value for fast axis of a relative scan
       fa2:      ending value for fast axis of a relative scan
       nfa:      number of steps in fast axis
       pluck:    optional flag for whether to offer to pluck & move motor
       force:    optional flag for forcing a scan even if not clear to start
       dwell:    dwell time at each point (0.1 sec default)
       md:       composable dictionary of metadata

    slow and fast are either the BlueSky name for a motor (e.g. xafs_linx)
    or a nickname for an XAFS sample motor (e.g. 'x' for xafs_linx).

    This does not write an ASCII data file, but it does make a log entry.

    Use the as2dat() function to extract the areascan from the
    database and write it to a file.
    '''

    def main_plan(detector,
                  slow, startslow, stopslow, nslow,
                  fast, startfast, stopfast, nfast,
                  pluck, force, dwell, md):
        (ok, text) = BMM_clear_to_start()
        if force is False and ok is False:
            print(error_msg(text))
            BMMuser.final_log_entry = False
            yield from null()
            return

        RE.msg_hook = None

        ## sanity checks on slow axis
        if type(slow) is str: slow = slow.lower()
        if slow not in motor_nicknames.keys() and 'EpicsMotor' not in str(type(slow)) and 'PseudoSingle' not in str(type(slow)):
            print(error_msg('\n*** %s is not an areascan motor (%s)\n' %
                            (slow, str.join(', ', motor_nicknames.keys()))))
            BMMuser.final_log_entry = False
            yield from null()
            return
        if slow in motor_nicknames.keys():
            slow = motor_nicknames[slow]

        ## sanity checks on fast axis
        if type(fast) is str: fast = fast.lower()
        if fast not in motor_nicknames.keys() and 'EpicsMotor' not in str(type(fast)) and 'PseudoSingle' not in str(type(fast)):
            print(error_msg('\n*** %s is not an areascan motor (%s)\n' %
                            (fast, str.join(', ', motor_nicknames.keys()))))
            BMMuser.final_log_entry = False
            yield from null()
            return
        if fast in motor_nicknames.keys():
            fast = motor_nicknames[fast]

        detector = detector.capitalize()
        yield from abs_set(_locked_dwell_time, dwell)
        dets = [quadem1,]
        if detector == 'If':
            dets.append(vor)
            detector = 'ROI1'

        
        if 'PseudoSingle' in str(type(slow)):
            valueslow = slow.readback.value
        else:
            valueslow = slow.user_readback.value
            line1 = 'slow motor: %s, %.3f, %.3f, %d -- starting at %.3f\n' % \
                    (slow.name, startslow, stopslow, nslow, valueslow)

        if 'PseudoSingle' in str(type(fast)):
            valuefast = fast.readback.value
        else:
            valuefast = fast.user_readback.value
        line2 = 'fast motor: %s, %.3f, %.3f, %d -- starting at %.3f\n' % \
                (fast.name, startfast, stopfast, nfast, valuefast)

        npoints = nfast * nslow
        estimate = int(npoints*(dwell+0.4))
    
        # extent = (
        #     valuefast + startfast,
        #     valueslow + startslow,
        #     valuefast + stopfast,
        #     valueslow + stopslow,
        # )
        # extent = (
        #     0,
        #     nfast-1,
        #     0,
        #     nslow-1
        # )
        # print(extent)
        # return(yield from null())
    

        # areaplot = LiveScatter(fast.name, slow.name, detector,
        #                        xlim=(startfast, stopfast), ylim=(startslow, stopslow))
    
        areaplot = LiveGrid((nslow, nfast), detector, #aspect='equal', #aspect=float(nslow/nfast), extent=extent,
                            xlabel='fast motor: %s' % fast.name,
                            ylabel='slow motor: %s' % slow.name)
        BMMuser.ax     = areaplot.ax
        BMMuser.fig    = areaplot.ax.figure
        BMMuser.motor  = fast
        BMMuser.motor2 = slow
        BMMuser.fig.canvas.mpl_connect('close_event', handle_close)

        thismd = dict()
        thismd['XDI'] = dict()
        thismd['XDI']['Facility'] = dict()
        thismd['XDI']['Facility']['GUP'] = BMMuser.gup
        thismd['XDI']['Facility']['SAF'] = BMMuser.saf
        thismd['slow_motor'] = slow.name
        thismd['fast_motor'] = fast.name


        ## engage suspenders right before starting scan sequence
        if force is False: BMM_suspenders()
    
        @subs_decorator(areaplot)
        def make_areascan(dets,
                          slow, startslow, stopslow, nslow,
                          fast, startfast, stopfast, nfast,
                          snake=False):
            BMMuser.final_log_entry = False
            yield from grid_scan(dets,
                                 slow, startslow, stopslow, nslow,
                                 fast, startfast, stopfast, nfast,
                                 snake)
            BMMuser.final_log_entry = True

        with open(dotfile, "w") as f:
            f.write(str(datetime.datetime.timestamp(datetime.datetime.now())) + '\n')
            f.write('%d\n' % estimate)
        BMM_log_info('begin areascan observing: %s\n%s%s' % (detector, line1, line2))
        yield from make_areascan(dets,
                                 slow, valueslow+startslow, valueslow+stopslow, nslow,
                                 fast, valuefast+startfast, valuefast+stopfast, nfast,
                                 False)

        if pluck is True:
            action = input('\n' + bold_msg('Pluck motor position from the plot? [Y/n then Enter] '))
            if action.lower() == 'n' or action.lower() == 'q':
                return(yield from null())
            print('Single click the left mouse button on the plot to pluck a point...')
            cid = BMMuser.fig.canvas.mpl_connect('button_press_event', interpret_click) # see 65-derivedplot.py and
            while BMMuser.x is None:                            #  https://matplotlib.org/users/event_handling.html
                yield from sleep(0.5)

            print('Converting plot coordinates to real coordinates...')
            begin = valuefast + startfast
            stepsize = (stopfast - startfast) / (nfast - 1)
            pointfast = begin + stepsize * BMMuser.x
            #print(BMMuser.x, pointfast)
        
            begin = valueslow + startslow
            stepsize = (stopslow - startslow) / (nslow - 1)
            pointslow = begin + stepsize * BMMuser.y
            #print(BMMuser.y, pointslow)

            print('That translates to x=%.3f, y=%.3f' % (pointfast, pointslow))
            yield from mv(fast, pointfast, slow, pointslow)
        
    def cleanup_plan():
        print('Cleaning up after an area scan')
        RE.clear_suspenders()
        if os.path.isfile(dotfile): os.remove(dotfile)
        if BMMuser.final_log_entry is True:
            BMM_log_info('areascan finished\n\tuid = %s, scan_id = %d' % (db[-1].start['uid'], db[-1].start['scan_id']))
        yield from abs_set(_locked_dwell_time, 0.5)
        RE.msg_hook = BMM_msg_hook

        print('Disabling plot for re-plucking.')
        cid = BMMuser.fig.canvas.mpl_disconnect(cid)
        BMMuser.x      = None
        BMMuser.y      = None
        BMMuser.motor  = None
        BMMuser.motor2 = None
        BMMuser.fig    = None
        BMMuser.ax     = None

        
    dotfile = '/home/xf06bm/Data/.area.scan.running'
    BMMuser.final_log_entry = True
    RE.msg_hook = None
    ## encapsulation!
    yield from bluesky.preprocessors.finalize_wrapper(main_plan(detector,
                                                                slow, startslow, stopslow, nslow,
                                                                fast, startfast, stopfast, nfast,
                                                                pluck, force, dwell, md),
                                                      cleanup_plan())
    RE.msg_hook = BMM_msg_hook

        
def as2dat(datafile, key):
    '''
    Export an areascan database entry to a simple column data file.

      as2dat('/path/to/myfile.dat', 2948)

    or

      as2dat('/path/to/myfile.dat', '42447313-46a5-42ef-bf8a-46fedc2c2bd1')

    The arguments are a data file name and the database key.
    '''

    if os.path.isfile(datafile):
        print(error_msg('%s already exists!  Bailing out....' % datafile))
        return
    dataframe = db[key]
    if 'slow_motor' not in dataframe['start']:
        print(error_msg('That database entry does not seem to be a an areascan (missing slow_motor)'))
        return
    if 'fast_motor' not in dataframe['start']:
        print(error_msg('That database entry does not seem to be a an areascan (missing fast_motor)'))
        return

    devices = dataframe.devices() # note: this is a _set_ (this is helpful: https://snakify.org/en/lessons/sets/)

    if 'vor' in devices:
        column_list = [dataframe['start']['slow_motor'], dataframe['start']['fast_motor'],
                       'I0', 'It', 'Ir',
                       'DTC1', 'DTC2', 'DTC3', 'DTC4',
                       'ROI1', 'ICR1', 'OCR1',
                       'ROI2', 'ICR2', 'OCR2',
                       'ROI3', 'ICR3', 'OCR3',
                       'ROI4', 'ICR4', 'OCR4']
        template = "  %.3f  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f\n"
    else:
        column_list = [dataframe['start']['slow_motor'], dataframe['start']['fast_motor'], 'I0', 'It', 'Ir']
        template = "  %.3f  %.3f  %.6f  %.6f  %.6f\n"

    table = dataframe.table()
    this = table.loc[:,column_list]

    handle = open(datafile, 'w')
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
    slowval = None
    for i in range(0,len(this)):
        if i>0 and this.iloc[i,0] != slowval:
            handle.write('\n')
        handle.write(template % tuple(this.iloc[i]))
        slowval = this.iloc[i,0]
    handle.flush()
    handle.close()
    print(bold_msg('wrote areascan to %s' % datafile))
