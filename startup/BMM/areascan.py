
from bluesky.plans import grid_scan
from bluesky.callbacks import LiveGrid
from bluesky.plan_stubs import sleep, mv, mvr, null
from bluesky.preprocessors import subs_decorator, finalize_wrapper
import numpy, datetime
import os
import matplotlib.pyplot as plt
from ophyd.sim import noisy_det

from BMM.user_ns.dwelltime import with_xspress3
from BMM.resting_state     import resting_state_plan
from BMM.suspenders        import BMM_clear_to_start
from BMM.kafka             import kafka_message
from BMM.linescans         import motor_nicknames
from BMM.logging           import BMM_log_info, BMM_msg_hook, report, img_to_slack, post_to_slack
from BMM.functions         import countdown, plotting_mode, now, PROMPT
from BMM.functions         import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.derivedplot       import DerivedPlot, interpret_click, close_all_plots
from BMM.suspenders        import BMM_suspenders, BMM_clear_to_start, BMM_clear_suspenders
#from BMM.purpose       import purpose
from BMM.workspace         import rkvs

from BMM.user_ns.bmm         import BMMuser
from BMM.user_ns.dwelltime   import _locked_dwell_time
from BMM.user_ns.detectors   import quadem1, vor, xs, ic0

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)


def areascan(detector,
             slow, startslow, stopslow, nslow,
             fast, startfast, stopfast, nfast,
             pluck=True, force=False, dwell=0.1, fname=None,
             contour=False, log=True, md={}):
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
       contour:  True=plot with filled-in countours, False=plot with pcolormesh
       log:      True=plot log of signal in color scale
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
                  pluck, force, dwell, fname, contour, log,  md):

        
        if force is True:
            (ok, text) = (True, '')
        else:
            (ok, text) = BMM_clear_to_start()
            if force is False and ok is False:
                print(error_msg(text))
                BMMuser.final_log_entry = False
                yield from null()
                return

        user_ns['RE'].msg_hook = None

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
        yield from mv(_locked_dwell_time, dwell)
        dets = [quadem1,]

        if with_xspress3 and detector == 'If':
            detector = 'Xs'

        if detector == 'If':
            dets.append(vor)
            detector = 'ROI1'
        elif detector.lower() == 'xs':
            dets.append(xs)
            detector = BMMuser.xs1
            yield from mv(xs.total_points, nslow*nfast)
        elif detector in ('Random', 'Noisy', 'Noisy_det'):
            dets.append(noisy_det)
            detector = 'noisy_det'
        elif detector == 'I0a':
            dets.append(ic0)
            detector = ic0.Ia.name
        elif detector == 'I0a':
            dets.append(ic0)
            detector = ic0.Ib.name
        
        line1 = f'slow motor: {slow.name}, {startslow}, {stopslow}, {nslow} -- starting at {slow.position:.3f}\n'
        line2 = f'fast motor: {fast.name}, {startfast}, {stopfast}, {nfast} -- starting at {fast.position:.3f}\n'

        npoints = nfast * nslow
        estimate = int(npoints*(dwell+0.43))
    
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

        close_all_plots()
    
        areaplot = LiveGrid((nslow, nfast), detector, #aspect='equal', #aspect=float(nslow/nfast), extent=extent,
                            xlabel='fast motor: %s' % fast.name,
                            ylabel='slow motor: %s' % slow.name)
        #BMMuser.ax     = areaplot.ax
        #BMMuser.fig    = areaplot.ax.figure
        BMMuser.motor  = fast
        BMMuser.motor2 = slow
        #BMMuser.fig.canvas.mpl_connect('close_event', handle_close)

        thismd = dict()
        thismd['XDI'] = dict()
        thismd['XDI']['Facility'] = dict()
        thismd['XDI']['Facility']['GUP'] = BMMuser.gup
        thismd['XDI']['Facility']['SAF'] = BMMuser.saf
        thismd['slow_motor'] = slow.name
        thismd['fast_motor'] = fast.name


        if fname is None:
            fname = os.path.join(BMMuser.folder, 'map-'+now()+'.png')
        elif fname.endswith('.png'):
            fname = os.path.join(BMMuser.folder, fname)
        else:
            fname = os.path.join(BMMuser.folder, fname+'.png')

        report(f'Starting areascan at x,y = {fast.position:.3f}, {slow.position:.3f}', level='bold', slack=True)

        ## engage suspenders right before starting scan sequence
        if force is False: BMM_suspenders()
    
        @subs_decorator(areaplot)
        def make_areascan(dets,
                          slow, startslow, stopslow, nslow,
                          fast, startfast, stopfast, nfast,
                          fname, snake=False):
            BMMuser.final_log_entry = False
            
            uid = yield from grid_scan(dets,
                                       slow, startslow, stopslow, nslow,
                                       fast, startfast, stopfast, nfast,
                                       snake, md={'plan_name' : f'grid_scan measurement {slow.name} {fast.name} {detector}',
                                                  'BMM_kafka' : {'hint': f'areascan {detector.capitalize()} {slow.name} {fast.name} {contour} {log} {user_ns["dcm"].energy.position:.1f}',
                                                                 'pngout': fname}})
            BMMuser.final_log_entry = True
            return uid

        rkvs.set('BMM:scan:type',      'area')
        rkvs.set('BMM:scan:starttime', str(datetime.datetime.timestamp(datetime.datetime.now())))
        rkvs.set('BMM:scan:estimated', estimate)
        
        BMM_log_info('begin areascan observing: %s\n%s%s' % (detector, line1, line2))
        uid = yield from make_areascan(dets,
                                       slow, slow.position+startslow, slow.position+stopslow, nslow,
                                       fast, fast.position+startfast, fast.position+stopfast, nfast,
                                       fname, snake=False)
        report(f'map uid = {uid}', level='bold', slack=True)
        

        #     BMMuser.x = None
        #     figs = list(map(plt.figure, plt.get_fignums()))
        #     canvas = figs[0].canvas
        #     action = input('\n' + bold_msg('Pluck motor position from the plot? ' + PROMPT))
        #     if action.lower() == 'n' or action.lower() == 'q':
        #         return(yield from null())
        #     print('Single click the left mouse button on the plot to pluck a point...')
        #     cid = canvas.mpl_connect('button_press_event', interpret_click) # see 65-derivedplot.py and
        #     while BMMuser.x is None:                            #  https://matplotlib.org/users/event_handling.html
        #         yield from sleep(0.5)

        #     # print('Converting plot coordinates to real coordinates...')
        #     # begin = valuefast + startfast
        #     # stepsize = (stopfast - startfast) / (nfast - 1)
        #     # pointfast = begin + stepsize * BMMuser.x
        #     # #print(BMMuser.x, pointfast)
        
        #     # begin = valueslow + startslow
        #     # stepsize = (stopslow - startslow) / (nslow - 1)
        #     # pointslow = begin + stepsize * BMMuser.y
        #     # #print(BMMuser.y, pointslow)

        #     # print('That translates to x=%.3f, y=%.3f' % (pointfast, pointslow))
        #     yield from mv(fast, BMMuser.x, slow, BMMuser.y)
        #     report(f'Moved to position x,y = {fast.position:.3f}, {slow.position:.3f}', level='bold', slack=False)
            
            
        
    def cleanup_plan():
        print('Cleaning up after an area scan')
        db = user_ns['db']
        BMM_clear_suspenders()
        if BMMuser.final_log_entry is True:
            BMM_log_info('areascan finished\n\tuid = %s, scan_id = %d' % (db[-1].start['uid'], db[-1].start['scan_id']))
        yield from resting_state_plan()
        user_ns['RE'].msg_hook = BMM_msg_hook

        print('Disabling plot for re-plucking.')
        try:
            cid = BMMuser.fig.canvas.mpl_disconnect(cid)
        except:
            pass
        BMMuser.x      = None
        BMMuser.y      = None
        BMMuser.motor  = None
        BMMuser.motor2 = None
        BMMuser.fig    = None
        BMMuser.ax     = None

    ######################################################################
    # this is a tool for verifying a macro.  this replaces an xafs scan  #
    # with a sleep, allowing the user to easily map out motor motions in #
    # a macro                                                            #
    if BMMuser.macro_dryrun:
        print(info_msg('\nBMMuser.macro_dryrun is True.  Sleeping for %.1f seconds rather than running an area scan.\n' %
                       BMMuser.macro_sleep))
        countdown(BMMuser.macro_sleep)
        return(yield from null())
    ######################################################################
    BMMuser.final_log_entry = True
    user_ns['RE'].msg_hook = None

    yield from finalize_wrapper(main_plan(detector,
                                          slow, startslow, stopslow, nslow,
                                          fast, startfast, stopfast, nfast,
                                          pluck, force, dwell, fname, contour, log, md),
                                cleanup_plan())
    user_ns['RE'].msg_hook = BMM_msg_hook


def fetch_areaplot(uid=None, signal=None, log=False, contour=False):
    if uid is None:
        print('No uid provided.')
        return
    df = user_ns['db'].v2[uid]
    slow = df.metadata['start']['motors'][0]
    fast = df.metadata['start']['motors'][1]
    x = numpy.array(df.primary.read()[fast])
    y = numpy.array(df.primary.read()[slow])
    el = df.metadata['start']['plan_name'].split(" ")[-1][:-1]
    if signal is None:
        z = numpy.array(df.primary.read()[el+'1']) + numpy.array(df.primary.read()[el+'2']) + numpy.array(df.primary.read()[el+'3']) + numpy.array(df.primary.read()[el+'4'])
    elif signal.lower() in ('it', 'i0a', 'i0b'):
        z = numpy.array(df.primary.read()[signal.capitalize()])
    (nslow, nfast) = df.metadata['start']['shape']
    if log is True:
        z = numpy.log(z)
    
    
    fig = plt.figure(figsize=(nfast/20,nslow/20))
    plt.xlabel(f'fast axis ({fast}) position (mm)')
    plt.ylabel(f'slow axis ({slow}) position (mm)')
    plt.gca().invert_yaxis()  # plot an xafs_x/xafs_y plot upright
    if contour is True:
        plt.contourf(x[:nfast], y[::nfast], z.reshape(nslow, nfast), cmap=plt.cm.viridis)
    else:
        plt.pcolormesh(x[:nfast], y[::nfast], z.reshape(nslow, nfast), cmap=plt.cm.viridis)
    plt.colorbar()
    plt.show()


    
def as2dat(datafile, key):
    '''
    Export an areascan database entry to a simple column data file.

      as2dat('/path/to/myfile.dat', '42447313-46a5-42ef-bf8a-46fedc2c2bd1')

    or

      as2dat('/path/to/myfile.dat', 2948)

    The arguments are a data file name and the database key.
    '''

    if os.path.isfile(datafile):
        print(error_msg('%s already exists!  Bailing out....' % datafile))
        return
    dataframe = user_ns['db'][key]
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
                       BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc3, BMMuser.dtc4,
                       BMMuser.roi1, 'ICR1', 'OCR1',
                       BMMuser.roi2, 'ICR2', 'OCR2',
                       BMMuser.roi3, 'ICR3', 'OCR3',
                       BMMuser.roi4, 'ICR4', 'OCR4']
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
