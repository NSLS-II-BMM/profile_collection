
from bluesky.plans import grid_scan
from bluesky.callbacks import LiveGrid
from bluesky.plan_stubs import abs_set, sleep, mv, mvr, null
from bluesky import __version__ as bluesky_version

import numpy
import os
import pandas

from bluesky.preprocessors import subs_decorator
## see 65-derivedplot.py for DerivedPlot class
## see 10-motors.py and 20-dcm.py for motor definitions

from BMM.resting_state import resting_state_plan
from BMM.suspenders    import BMM_clear_to_start, BMM_clear_suspenders
from BMM.logging       import BMM_log_info, BMM_msg_hook
from BMM.functions     import countdown
from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.derivedplot   import DerivedPlot, interpret_click
from BMM.metadata      import bmm_metadata

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)


####################################
# generic timescan vs. It/If/Ir/I0 #
####################################
def timescan(detector, readings, dwell, delay, force=False, md={}):
    '''
    Generic timescan plan.

    Parameters
    ----------
    detector : str
        detector to display -- if, it, ir, or i0
    readings : int
        number of measurements to make
    dwell : float
        dwell time in seconds for each measurement
    delay : float
        pause in seconds between measurements
    outfile :  str
        data file name (relative to DATA), False to not write
    force : bool
        flag for forcing a scan even if not clear to start

    This does not write an ASCII data file, but it does make a log entry.

    Use the ts2dat() function to extract the linescan from the
    database and write it to a file.

    Examples
       
    >>> RE(timescan('it', 100, 0.5))

    '''

    RE, BMMuser, quadem1, _locked_dwell_time = user_ns['RE'], user_ns['BMMuser'], user_ns['quadem1'], user_ns['_locked_dwell_time']
    rkvs = user_ns['rkvs']
    ######################################################################
    # this is a tool for verifying a macro.  this replaces an xafs scan  #
    # with a sleep, allowing the user to easily map out motor motions in #
    # a macro                                                            #
    if BMMuser.macro_dryrun:
        print(info_msg('\nBMMuser.macro_dryrun is True.  Sleeping for %.1f seconds rather than running a time scan.\n' %
                       BMMuser.macro_sleep))
        countdown(BMMuser.macro_sleep)
        return(yield from null())
    ######################################################################
    
    (ok, text) = BMM_clear_to_start()
    if force is False and ok is False:
        print(error_msg(text))
        yield from null()
        return

    
    RE.msg_hook = None
    ## sanitize and sanity checks on detector
    detector = detector.capitalize()
    if detector not in ('It', 'If', 'I0', 'Iy', 'Ir') and 'Dtc' not in detector:
        print(error_msg('\n*** %s is not a timescan measurement (%s)\n' %
                        (detector, 'it, if, i0, iy, ir')))
        yield from null()
        return

    yield from abs_set(_locked_dwell_time, dwell, wait=True)
    dets  = [quadem1,]
    denominator = ''

    epoch_offset = pandas.Timestamp.now(tz='UTC').value/10**9
    ## func is an anonymous function, built on the fly, for feeding to DerivedPlot
    if detector == 'It':
        denominator = ' / I0'
        func = lambda doc: (doc['time']-epoch_offset, doc['data']['It']/doc['data']['I0'])
    elif detector == 'Ir':
        denominator = ' / It'
        func = lambda doc: (doc['time']-epoch_offset, doc['data']['Ir']/doc['data']['It'])
    elif detector == 'I0':
        func = lambda doc: (doc['time']-epoch_offset, doc['data']['I0'])
    elif detector == 'Iy':
        denominator = ' / I0'
        func = lambda doc: (doc['time']-epoch_offset, doc['data']['Iy']/doc['data']['I0'])
    elif detector == 'Dtc':
        dets.append(vor)
        denominator = ' / I0'
        func  = lambda doc: (doc['time']-epoch_offset, doc['data'][BMMuser.dtc2]/doc['data']['I0'])
        func3 = lambda doc: (doc['time']-epoch_offset, doc['data'][BMMuser.dtc3]/doc['data']['I0'])
    elif detector == 'If':
        dets.append(vor)
        denominator = ' / I0'
        func = lambda doc: (doc['time']-epoch_offset,
                            (doc['data'][BMMuser.dtc1] +
                             doc['data'][BMMuser.dtc2] +
                             doc['data'][BMMuser.dtc3] +
                             doc['data'][BMMuser.dtc4]   ) / doc['data']['I0'])

    ## and this is the appropriate way to plot this linescan
    if detector == 'Dtc':
        plot = [DerivedPlot(func,  xlabel='elapsed time (seconds)', ylabel='dtc2', title='time scan'),
                DerivedPlot(func3, xlabel='elapsed time (seconds)', ylabel='dtc3', title='time scan')]
    else:
        plot = DerivedPlot(func,
                           xlabel='elapsed time (seconds)',
                           ylabel=detector+denominator,
                           title='time scan')

    line1 = '%s, N=%s, dwell=%.3f, delay=%.3f\n' % (detector, readings, dwell, delay)
    
    thismd = dict()
    thismd['XDI'] = dict()
    thismd['XDI']['Facility'] = dict()
    thismd['XDI']['Facility']['GUP']    = BMMuser.gup
    thismd['XDI']['Facility']['SAF']    = BMMuser.saf
    thismd['XDI']['Beamline'] = dict()
    thismd['XDI']['Beamline']['energy'] = dcm.energy.readback.get()
    thismd['XDI']['Scan'] = dict()
    thismd['XDI']['Scan']['dwell_time'] = dwell
    thismd['XDI']['Scan']['delay']      = delay
    
    @subs_decorator(plot)
    #@subs_decorator(src.callback)
    def count_scan(dets, readings, delay):
        #if 'purpose' not in md:
        #    md['purpose'] = 'measurement'
        uid = yield from count(dets, num=readings, delay=delay, md={**thismd, **md, 'plan_name' : f'count measurement {detector}'})
        return uid
        
    rkvs.set('BMM:scan:type',      'time')
    rkvs.set('BMM:scan:starttime', str(datetime.datetime.timestamp(datetime.datetime.now())))
    rkvs.set('BMM:scan:estimated', 0)

    uid = yield from count_scan(dets, readings, delay, md)
    
    BMM_log_info('timescan: %s\tuid = %s, scan_id = %d' %
                 (line1, uid, db[-1].start['scan_id']))

    yield from abs_set(_locked_dwell_time, 0.5, wait=True)
    RE.msg_hook = BMM_msg_hook
    return(uid)



def ts2dat(datafile, key):
    '''
    Export an timescan database entry to a simple column data file.

    Parameters
    ----------
    datafile : str
        name of output data file
    key : str
        UID of record in database

    Examples
    --------
    >>> ts2dat('/path/to/myfile.dat', '42447313-46a5-42ef-bf8a-46fedc2c2bd1')

    

    >>> ts2dat('/path/to/myfile.dat', 2948)

    '''

    BMMuser, db = user_ns['BMMuser'], user_ns['db']
    if os.path.isfile(datafile):
        print(error_msg('%s already exists!  Bailing out....' % datafile))
        return
    dataframe = db[key]

    devices = dataframe.devices() # note: this is a _set_ (this is helpful: https://snakify.org/en/lessons/sets/)
    if 'vor' in devices:
        column_list = ['time', 'I0', 'It', 'Ir',
                       BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc3, BMMuser.dtc4,
                       BMMuser.roi1, 'ICR1', 'OCR1',
                       BMMuser.roi2, 'ICR2', 'OCR2',
                       BMMuser.roi3, 'ICR3', 'OCR3',
                       BMMuser.roi4, 'ICR4', 'OCR4']
        template = "  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f  %.1f\n"
    else:
        column_list = ['time', 'I0', 'It', 'Ir']
        template = "  %.3f  %.6f  %.6f  %.6f\n"


    ## set Scan.start_time & Scan.end_time ... this is how it is done
    d=datetime.datetime.fromtimestamp(round(dataframe.start['time']))
    start_time = datetime.datetime.isoformat(d)
    d=datetime.datetime.fromtimestamp(round(dataframe.stop['time']))
    end_time   = datetime.datetime.isoformat(d)

    st = pandas.Timestamp(start_time) # this is a UTC problem
        
    table = dataframe.table()
    this = table.loc[:,column_list]

        
    handle = open(datafile, 'w')
    handle.write('# XDI/1.0 BlueSky/%s'      % bluesky_version)
    handle.write('# Scan.start_time: %s\n'   % start_time)
    handle.write('# Scan.end_time: %s\n'     % end_time)
    handle.write('# Scan.uid: %s\n'          % dataframe['start']['uid'])
    handle.write('# Scan.transient_id: %d\n' % dataframe['start']['scan_id'])
    handle.write('# Beamline.energy: %.3f\n' % dataframe['start']['XDI']['Beamline']['energy'])
    handle.write('# Scan.dwell_time: %d\n'   % dataframe['start']['XDI']['Scan']['dwell_time'])
    handle.write('# Scan.delay: %d\n'        % dataframe['start']['XDI']['Scan']['delay'])
    try:
        handle.write('# Facility.GUP: %d\n'  % dataframe['start']['XDI']['Facility']['GUP'])
    except:
        pass
    try:
        handle.write('# Facility.SAF: %d\n'  % dataframe['start']['XDI']['Facility']['SAF'])
    except:
        pass
    handle.write('# ==========================================================\n')
    handle.write('# ' + '  '.join(column_list) + '\n')
    slowval = None
    for i in range(0,len(this)):
        ti = this.iloc[i, 0]
        elapsed =  (ti.value - st.value)/10**9
        datapoint = list(this.iloc[i])
        datapoint[0] = elapsed
        handle.write(template % tuple(datapoint))

    handle.flush()
    handle.close()
    print(bold_msg('wrote timescan to %s' % datafile))



##########################################################################################################################################
# See                                                                                                                                    #
#   Single-energy x-ray absorption detection: a combined electronic and structural local probe for phase transitions in condensed matter #
#   A Filipponi, M Borowski, P W Loeffen, S De Panfilis, A Di Cicco, F Sperandini, M Minicucci and M Giorgetti                           #
#   Journal of Physics: Condensed Matter, Volume 10, Number 1                                                                            #
#   http://iopscience.iop.org/article/10.1088/0953-8984/10/1/026/meta                                                                    #
##########################################################################################################################################
def sead(inifile, force=False, **kwargs):
    '''
    Read an INI file for scan matadata, then perform a single energy
    absorption detection measurement.

    '''
    def main_plan(inifile, force, **kwargs):
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## read and check INI content
        orig = inifile
        if not os.path.isfile(inifile):
            inifile = DATA + inifile
            if not os.path.isfile(inifile):
                print(warning_msg('\n%s does not exist!  Bailing out....\n' % orig))
                return(orig, -1)
        print(bold_msg('reading ini file: %s' % inifile))
        (p, f) = scan_metadata(inifile=inifile, **kwargs)
        if not any(p):          # scan_metadata returned having printed an error message
            return(yield from null())
        #if not os.path.isdir(p['folder']):
        #    print(error_msg('\n%s is not a folder\n' % p['folder']))
        #    return(yield from null())
              
        detector = 'It'
        if 'trans' in p['mode']:
            detector = 'It'
        elif 'fluo' in p['mode']:
            detector = 'If'


        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## verify output file name won't be overwritten
        outfile = '%s.%3.3d' % (os.path.join(p['folder'], p['filename']), p['start'])
        if os.path.isfile(outfile):
            print(error_msg('%s already exists!  Bailing out....' % outfile))
            return(yield from null())

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## prompt user and verify that we are clear to start
        text = '\n'
        for k in ('folder', 'filename', 'experimenters', 'e0', 'npoints', 'dwell', 'delay',
                  'sample', 'prep', 'comment', 'mode', 'snapshots'):
            text = text + '      %-13s : %-50s\n' % (k,p[k])
        if BMMuser.prompt:
            boxedtext('How does this look?', text + '\n      %-13s : %-50s\n' % ('output file',outfile), 'green', width=len(outfile)+25) # see 05-functions
            action = input("\nBegin time scan? [Y/n then Enter] ")
            if action.lower() == 'q' or action.lower() == 'n':
                return(yield from null())

        (ok, ctstext) = BMM_clear_to_start()
        if force is False and ok is False:
            print(error_msg(ctstext))
            yield from null()
            return


        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        # organize metadata for injection into database and XDI output
        print(bold_msg('gathering metadata'))
        md = bmm_metadata(measurement   = p['mode'],
                          experimenters = p['experimenters'],
                          edge          = p['edge'],
                          element       = p['element'],
                          edge_energy   = p['e0'],
                          direction     = 0,
                          scantype      = 'fixed',
                          channelcut    = p['channelcut'],
                          mono          = 'Si(%s)' % dcm._crystal,
                          i0_gas        = 'N2', #\
                          it_gas        = 'N2', # > these three need to go into INI file
                          ir_gas        = 'N2', #/
                          sample        = p['sample'],
                          prep          = p['prep'],
                          stoichiometry = None,
                          mode          = p['mode'],
                          comment       = p['comment'],)
        del(md['XDI']['Element']['edge'])
        del(md['XDI']['Element']['symbol'])
        md['XDI']['Column']['01'] = 'time seconds'
        md['XDI']['Column']['02'] = md.copy()['XDI']['Column']['03']
        md['XDI']['Column']['03'] = md.copy()['XDI']['Column']['04']
        md['XDI']['Column']['04'] = md['XDI']['Column']['05']
        del(md['XDI']['Column']['05'])
        md['_kind'] = 'sead'

        rightnow = metadata_at_this_moment() # see 62-metadata.py
        for family in rightnow.keys():       # transfer rightnow to md
            if type(rightnow[family]) is dict:
                if family not in md:
                    md[family] = dict()
                for k in rightnow[family].keys():
                    md[family][k] = rightnow[family][k]
        xdi = {'XDI': md}

        BMM_log_info('Starting single-energy absorption detection time scan using\n%s:\n%s\nCommand line arguments = %s\nMoving to measurement energy: %.1f eV' %
                     (inifile, text, str(kwargs), p['e0']))


        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## move to the energy specified in the INI file
        print(bold_msg('Moving to measurement energy: %.1f eV' % p['e0']))
        dcm.mode = 'fixed'
        yield from mv(dcm.energy, p['e0'])

        
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## snap photos
        if p['snapshots']:
            image = os.path.join(p['folder'], 'snapshots', "%s_XASwebcam_%s.jpg" % (p['filename'], now()))
            snap('XAS', filename=image)
            image = os.path.join(p['folder'], 'snapshots', "%s_analog_%s.jpg" % (p['filename'], now()))
            snap('analog', filename=image)

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## engage suspenders right before starting measurement
        if not force: BMM_suspenders()

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## perform the actual time scan
        uid = yield from timescan(detector, p['npoints'], p['dwell'], p['delay'], force=force, md={**xdi})
        
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## write the output file
        header = db[uid]
        write_XDI(outfile, header) # yield from ?
        report('wrote time scan to %s' % outfile)
        #BMM_log_info('wrote time scan to %s' % outfile)
        #print(bold_msg('wrote %s' % outfile))

    def cleanup_plan():
        print('Cleaning up after single energy absorption detector measurement')
        BMM_clear_suspenders()
        #RE.clear_suspenders()
        yield from resting_state_plan()
        dcm.mode = 'fixed'

    RE.msg_hook = None
    ## encapsulation!
    yield from bluesky.preprocessors.finalize_wrapper(main_plan(inifile, force, **kwargs), cleanup_plan())
    RE.msg_hook = BMM_msg_hook
        
