try:
    from bluesky_queueserver import is_re_worker_active
except ImportError:
    # TODO: delete this when 'bluesky_queueserver' is distributed as part of collection environment
    def is_re_worker_active():
        return False

from bluesky.plans import count
from bluesky.callbacks import LiveGrid
from bluesky.plan_stubs import sleep, mv, mvr, null
from bluesky import __version__ as bluesky_version
from bluesky.preprocessors import subs_decorator, finalize_wrapper

import numpy
import os, datetime, re, textwrap, configparser, uuid
import pandas

import matplotlib
import matplotlib.pyplot as plt


from BMM.derivedplot   import DerivedPlot
from BMM.dossier       import BMMDossier
from BMM.functions     import countdown, boxedtext, now, isfloat, inflect, e2l, etok, ktoe, present_options, plotting_mode, PROMPT
from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.kafka           import kafka_message
from BMM.logging       import BMM_log_info, BMM_msg_hook, report, img_to_slack, post_to_slack
from BMM.metadata      import bmm_metadata, display_XDI_metadata, metadata_at_this_moment
from BMM.motor_status  import motor_sidebar #, motor_status
from BMM.resting_state import resting_state, resting_state_plan
from BMM.suspenders    import BMM_suspenders, BMM_clear_to_start, BMM_clear_suspenders
from BMM.xafs          import scan_metadata
from BMM.xdi           import write_XDI

from BMM.user_ns.detectors import quadem1, ic0, ic1, vor, xs, xs1
from BMM.user_ns.dwelltime import _locked_dwell_time, use_4element, use_1element

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)


####################################
# generic timescan vs. It/If/Ir/I0 #
####################################
def timescan(detector, readings, dwell, delay, outfile=None, force=False, md={}):
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

    RE, BMMuser, quadem1, xs, dcm, db = user_ns['RE'], user_ns['BMMuser'], user_ns['quadem1'], user_ns['xs'], user_ns['dcm'], user_ns['db']
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

    if force is False:
        (ok, text) = BMM_clear_to_start()
        if ok is False:
            print(error_msg(text))
            yield from null()
            return

    
    RE.msg_hook = None
    ## sanitize and sanity checks on detector
    detector = detector.capitalize()
    if detector not in ('It', 'If', 'I0', 'Iy', 'Ir', 'Ic1', 'Test', 'Transmission', 'Fluorescence', 'Flourescence') and 'Dtc' not in detector:
        print(error_msg(f'\n*** {detector} is not a timescan measurement (it, if, i0, iy, ir, ic1, transmission, fluorescence)\n'))
        yield from null()
        return None

    yield from mv(_locked_dwell_time, dwell)
    dets  = [quadem1, ic0,]
    denominator = ''

    epoch_offset = pandas.Timestamp.now(tz='UTC').value/10**9
    ## func is an anonymous function, built on the fly, for feeding to DerivedPlot
    if detector == 'It':
        denominator = ''
        func = lambda doc: (doc['time']-epoch_offset, doc['data']['It'])
    elif detector == 'Transmission':
        denominator = ' / It'
        func = lambda doc: (doc['time']-epoch_offset, numpy.log(doc['data']['I0']/doc['data']['It']))
    elif detector == 'Ir':
        denominator = ''
        func = lambda doc: (doc['time']-epoch_offset, doc['data']['Ir'])
    elif detector == 'I0':
        func = lambda doc: (doc['time']-epoch_offset, doc['data']['I0'])
    elif detector == 'Iy':
        denominator = ' / I0'
        func = lambda doc: (doc['time']-epoch_offset, doc['data']['Iy']/doc['data']['I0'])
    elif detector == 'Test':
        func = lambda doc: (doc['time']-epoch_offset, doc['data']['I0'])
    elif detector == 'Ic1':
        dets.append(ic1)
        denominator = ' / I0'
        func  = lambda doc: (doc['time']-epoch_offset, doc['data']['Ita']/doc['data']['I0'])
        func3 = lambda doc: (doc['time']-epoch_offset, doc['data']['Itb']/doc['data']['I0'])
    elif detector == 'Dtc':
        dets.append(vor)
        denominator = ' / I0'
        func  = lambda doc: (doc['time']-epoch_offset, doc['data'][BMMuser.dtc2]/doc['data']['I0'])
        func3 = lambda doc: (doc['time']-epoch_offset, doc['data'][BMMuser.dtc3]/doc['data']['I0'])
    elif detector == 'Fluorescence' or detector == 'Flourescence':
        dets.append(xs)
        yield from mv(xs.cam.acquire_time, dwell)
        yield from mv(xs.total_points, readings)
        denominator = ' / I0'
        func = lambda doc: (doc['time']-epoch_offset, (doc['data'][BMMuser.xs1] +
                                                       doc['data'][BMMuser.xs2] +
                                                       doc['data'][BMMuser.xs3] +
                                                       doc['data'][BMMuser.xs4] ) / doc['data']['I0'])
    elif detector == 'If':
        dets.append(xs)
        yield from mv(xs.cam.acquire_time, dwell)
        yield from mv(xs.total_points, readings)
        denominator = ''
        func = lambda doc: (doc['time']-epoch_offset, (doc['data'][BMMuser.xs1] +
                                                       doc['data'][BMMuser.xs2] +
                                                       doc['data'][BMMuser.xs3] +
                                                       doc['data'][BMMuser.xs4] ))
        
        # dets.append(vor)
        # denominator = ' / I0'
        # func = lambda doc: (doc['time']-epoch_offset,
        #                     (doc['data'][BMMuser.dtc1] +
        #                      doc['data'][BMMuser.dtc2] +
        #                      doc['data'][BMMuser.dtc3] +
        #                      doc['data'][BMMuser.dtc4]   ) / doc['data']['I0'])

    ## and this is the appropriate way to plot this linescan
    if detector == 'Dtc':
        plot = [DerivedPlot(func,  xlabel='elapsed time (seconds)', ylabel='dtc2', title='time scan'),
                DerivedPlot(func3, xlabel='elapsed time (seconds)', ylabel='dtc3', title='time scan')]
    elif detector == 'Ic1':
        plot = [DerivedPlot(func,  xlabel='elapsed time (seconds)', ylabel='Ita', title='time scan'),
                DerivedPlot(func3, xlabel='elapsed time (seconds)', ylabel='Itb', title='time scan')]
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
    thismd['XDI']['Scan']['element']    = BMMuser.element

    if 'BMM_kafka' not in md:
        md['BMM_kafka'] = dict()
    if 'hint' not in md['BMM_kafka']:
        md['BMM_kafka']['hint'] = f'timescan {detector}'
        
    ## This helped Bruce understand how to make a decorator conditional:
    ## https://stackoverflow.com/a/49204061
    def conditional_subs_decorator(function):
        if user_ns['BMMuser'].enable_live_plots is True:
            return subs_decorator(plot)(function)
        else:
            return function

    @conditional_subs_decorator
    def count_scan(dets, readings, delay, md):
        #if 'purpose' not in md:
        #    md['purpose'] = 'measurement'
        uid = yield from count(dets, num=readings, delay=delay, md={**thismd, **md, 'plan_name' : f'count measurement {detector}'})
        return uid
        
    rkvs.set('BMM:scan:type',      'time')
    rkvs.set('BMM:scan:starttime', str(datetime.datetime.timestamp(datetime.datetime.now())))
    rkvs.set('BMM:scan:estimated', 0)

    kafka_message({'timescan': 'start',
                   'detector' : detector,})

    
    uid = yield from count_scan(dets, readings, delay, md)

    kafka_message({'timescan': 'stop',
                   'fname' : outfile, })
    
    BMM_log_info('timescan: %s\tuid = %s, scan_id = %d' %
                 (line1, uid, db[-1].start['scan_id']))

    yield from mv(_locked_dwell_time, 0.5)
    RE.msg_hook = BMM_msg_hook
    resting_state()
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
    elif '4-element SDD' in devices:
        el = dataframe.start['XDI']['Scan']['element']
        column_list = ['time', 'I0', 'It', 'Ir', f'{el}1', f'{el}2', f'{el}3', f'{el}4']
        template = "  %.3f  %.6f  %.6f  %.6f  %.2f  %.2f  %.2f  %.2f\n"        
    elif 'Ic1' in devices:
        el = dataframe.start['XDI']['Scan']['element']
        column_list = ['time', 'I0', 'It', 'Ir', 'Ita', 'Itb']
        template = "  %.3f  %.6f  %.6f  %.6f  %.6f  %.6f\n"        
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
    handle.write('# XDI/1.0 BlueSky/%s\n'    % bluesky_version)
    handle.write('# Scan.start_time: %s\n'   % start_time)
    handle.write('# Scan.end_time: %s\n'     % end_time)
    handle.write('# Scan.uid: %s\n'          % dataframe['start']['uid'])
    handle.write('# Scan.transient_id: %d\n' % dataframe['start']['scan_id'])
    handle.write('# Beamline.energy: %.3f\n' % dataframe['start']['XDI']['Beamline']['energy'])
    handle.write('# Scan.dwell_time: %.3f\n' % dataframe['start']['XDI']['Scan']['dwell_time'])
    handle.write('# Scan.delay: %.3f\n'      % dataframe['start']['XDI']['Scan']['delay'])
    handle.write('# Scan.element: %s\n'      % dataframe['start']['XDI']['Scan']['element'])
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
        #elapsed =  (ti.value - st.value)/10**9
        elapsed = (ti.value - this.iloc[0, 0].value)/10**9
        datapoint = list(this.iloc[i])
        datapoint[0] = elapsed
        handle.write(template % tuple(datapoint))

    handle.flush()
    handle.close()
    print(bold_msg('wrote timescan to %s' % datafile))



###############################################################################
# See                                                                         #
#   Single-energy x-ray absorption detection: a combined electronic and       #
#   structural local probe for phase transitions in condensed matter          #
#   A Filipponi, M Borowski, P W Loeffen, S De Panfilis, A Di Cicco,          #
#   F Sperandini, M Minicucci and M Giorgetti                                 #
#   Journal of Physics: Condensed Matter, Volume 10, Number 1                 #
#   http://iopscience.iop.org/article/10.1088/0953-8984/10/1/026/meta         #
###############################################################################
def sead(inifile=None, force=False, **kwargs):
    '''
    Read an INI file for scan matadata, then perform a single energy
    absorption detection measurement.

    '''
    def main_plan(inifile, force, **kwargs):


        # if force is False:
        #     (ok, ctstext) = BMM_clear_to_start()
        #     if ok is False:
        #         print(error_msg(ctstext))
        #         yield from null()
        #         return

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## read and check INI content
        orig = inifile
        if not os.path.isfile(inifile):
            inifile = os.path.join(BMMuser.folder, inifile)
            if not os.path.isfile(inifile):
                print(inifile)
                print(warning_msg('\n%s does not exist!  Bailing out....\n' % orig))
                return(orig, -1)
        print(bold_msg('reading ini file: %s' % inifile))
        (p, f) = scan_metadata(inifile=inifile, **kwargs)
        if not any(p):          # scan_metadata returned having printed an error message
            return(yield from null())
        #if not os.path.isdir(p['folder']):
        #    print(error_msg('\n%s is not a folder\n' % p['folder']))
        #    return(yield from null())

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## close the shutter if requested
        if p['shutter'] is True:
            yield from shb.close_plan()
        
        detector = 'It'
        if 'trans' in p['mode'].lower():
            detector = 'transmission'
        elif 'fluo' in p['mode'].lower() or 'flou' in p['mode'].lower():
            detector = 'fluorescence'
        elif 'test' in p['mode'].lower():
            detector = 'Test'


        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## verify output file name won't be overwritten
        outfile = '%s.%3.3d' % (os.path.join(p['folder'], p['filename']), p['start'])
        if os.path.isfile(outfile):
            print(error_msg('%s already exists!  Bailing out....' % outfile))
            return(yield from null())

        dossier.rid = str(uuid.uuid4())[:8]
        report(f'== starting single energy absorption detection scan', level='bold', slack=True, rid=dossier.rid)

        
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## prompt user and verify that we are clear to start
        text = '\n'
        for k in ('folder', 'filename', 'experimenters', 'energy', 'npoints', 'dwell', 'delay',
                  'sample', 'prep', 'comment', 'mode', 'shutter', 'snapshots'):
            text = text + '      %-13s : %-50s\n' % (k,p[k])
        ## NEVER prompt when using queue server
        if is_re_worker_active() is True:
            BMMuser.prompt = False
        if BMMuser.prompt:
            boxedtext('How does this look?', text + '\n      %-13s : %-50s\n' % ('output file',outfile), 'green', width=len(outfile)+25) # see 05-functions
            action = input("\nBegin time scan? " + PROMPT)
            if action != '':
                if action[0].lower() == 'n' or action[0].lower() == 'q':
                    return(yield from null())

        ## gather up input data into a format suitable for the dossier
        with open(inifile, 'r') as fd: content = fd.read()
        output = re.sub(r'\n+', '\n', re.sub(r'\#.*\n', '\n', content)) # remove comment and blank lines
        clargs = textwrap.fill(str(kwargs), width=50) # .replace('\n', '<br>')
        BMM_log_info('starting raster scan using %s:\n%s\ncommand line arguments = %s' % (inifile, output, str(kwargs)))

            
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        # organize metadata for injection into database and XDI output
        print(bold_msg('gathering metadata'))
        md = bmm_metadata(measurement   = p['mode'],
                          experimenters = p['experimenters'],
                          edge          = p['edge'],
                          element       = p['element'],
                          edge_energy   = p['energy'],
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
        md['Beamline']['energy'] = dcm.energy.position
        md['Scan']['dwell_time'] = p['dwell']
        md['Scan']['delay']      = p['delay']
        md['_kind'] = 'sead'

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## snap photos
        if p['snapshots']:
            yield from dossier.cameras(p['folder'], p['filename'], md)
            
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## capture dossier metadata for start document
        md['_snapshots'] = {**dossier.cameras_md}

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## populate the static html page for this scan 
        these_kwargs = {'npoints': p['npoints'], 'dwell': p['dwell'], 'delay': p['delay'], 'shutter': p['shutter']}
        dossier.prep_metadata(p, inifile, clargs, these_kwargs)

        rightnow = metadata_at_this_moment() # see 62-metadata.py
        for family in rightnow.keys():       # transfer rightnow to md
            if type(rightnow[family]) is dict:
                if family not in md:
                    md[family] = dict()
                for k in rightnow[family].keys():
                    md[family][k] = rightnow[family][k]
        xdi = {'XDI': md}

        BMM_log_info('Starting single-energy absorption detection time scan using\n%s:\n%s\nCommand line arguments = %s\nMoving to measurement energy: %.1f eV' %
                     (inifile, text, str(kwargs), p['energy']))


        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## move to the energy specified in the INI file
        print(bold_msg('Moving to measurement energy: %.1f eV' % p['energy']))
        dcm.mode = 'fixed'
        yield from mv(dcm.energy, p['energy'])

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## open the shutters (which were closed at the start of sead)
        if p['shutter'] is True:
            yield from shb.open_plan()

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## engage suspenders right before starting measurement
        if not force: BMM_suspenders()

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## perform the actual time scan
        pngout = os.path.join(BMMuser.folder, 'snapshots', f"{p['filename']}_sead_{now()}.png")
        dossier.seaduid = yield from timescan(detector, p['npoints'], p['dwell'], p['delay'],
                                              outfile=pngout,
                                              force=force, md={**xdi})

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## close the shutters again
        if p['shutter'] is True:
            yield from shb.close_plan()

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## save a mode-specific plot
        # thisagg = matplotlib.get_backend()
        # matplotlib.use('Agg') # produce a plot without screen display
        # table = db.v2[dossier.seaduid].primary.read()
        # if detector == 'Test':
        #     plt.plot(table['time']-table['time'][0], table['I0'])
        #     plt.xlabel('time (seconds)')
        #     plt.ylabel('I0 signal')
        # elif detector == 'I0':
        #     plt.plot(table['time']-table['time'][0], table['I0'])
        #     plt.xlabel('time (seconds)')
        #     plt.ylabel('I0 signal')
        # elif detector == 'It':
        #     plt.plot(table['time']-table['time'][0], table['It'])
        #     plt.xlabel('time (seconds)')
        #     plt.ylabel('It signal')
        # elif 'Trans' in detector:
        #     signal = numpy.log(table['I0'] / table['It'])
        #     plt.plot(table['time']-table['time'][0], signal)
        #     plt.xlabel('time (seconds)')
        #     plt.ylabel('It signal')
        # elif detector == 'If':
        #     signal = table[BMMuser.xs1]+table[BMMuser.xs2]+table[BMMuser.xs3]+table[BMMuser.xs4]
        #     plt.plot(table['time']-table['time'][0], signal)
        #     plt.xlabel('time (seconds)')
        #     plt.ylabel('If signal')
        # elif 'Fluo' in detector or 'Flour' in detector:
        #     signal = (table[BMMuser.xs1]+table[BMMuser.xs2]+table[BMMuser.xs3]+table[BMMuser.xs4]) / table['I0']
        #     plt.plot(table['time']-table['time'][0], signal)
        #     plt.xlabel('time (seconds)')
        #     plt.ylabel('If signal')
        # elif detector == 'Ir':
        #     plt.plot(table['time']-table['time'][0], table['Ir'])
        #     plt.xlabel('time (seconds)')
        #     plt.ylabel('Ir signal')
        # plt.show()

        ahora = now()
        dossier.seadimage = os.path.basename(pngout)
        # plt.savefig(os.path.join(BMMuser.folder, 'snapshots', dossier.seadimage))
        # matplotlib.use(thisagg) # return to screen display
        # img_to_slack(os.path.join(BMMuser.folder, 'snapshots', dossier.seadimage))

        
        if dossier.seaduid is not None:
            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## write the output file
            header = db[dossier.seaduid]
            write_XDI(outfile, header) # yield from ?
            report('wrote time scan to %s' % outfile)
            dossier.sead = os.path.basename(outfile)
            #BMM_log_info('wrote time scan to %s' % outfile)
            #print(bold_msg('wrote %s' % outfile))

    def cleanup_plan():
        print('Cleaning up after single energy absorption detection measurement')
        BMM_clear_suspenders()
        try:
            dossier.seqend = now('%A, %B %d, %Y %I:%M %p')
            how = 'finished  :tada:'
            try:
                if 'primary' not in db[-1].stop['num_events']:
                    how = '*stopped*'
                elif db[-1].stop['num_events']['primary'] != db[-1].start['num_points']:
                    how = '*stopped*'
            except:
                how = '*stopped*'
            report(f'== SEAD scan {how}', level='bold', slack=True)
            try:
                htmlout = dossier.sead_dossier()
                report('wrote dossier %s' % htmlout, 'bold')
            except Exception as E:
                print(error_msg('Failed to write SEAD dossier.  Here is the exception message:'))
                print(E)
                htmlout, prjout, pngout = None, None, None
            rsync_to_gdrive()
            synch_gdrive_folder()
        except:
            print(whisper('Quitting SEAD scan.'))

        yield from resting_state_plan()

    
    RE, dcm, BMMuser, db, shb = user_ns['RE'], user_ns['dcm'], user_ns['BMMuser'], user_ns['db'], user_ns['shb']
    openclose = False
    #if openclose is True:
    #    shb.close_plan()
    RE.msg_hook = None
    dossier = BMMDossier()
    dossier.measurement = 'SEAD'

    if is_re_worker_active():
        inifile = '/home/xf06bm/Data/bucket/sead.ini'
    if inifile is None:
        inifile = present_options('ini')
    if inifile is None:
        return(yield from null())
    if inifile[-4:] != '.ini':
        inifile = inifile+'.ini'
    yield from finalize_wrapper(main_plan(inifile, force, **kwargs), cleanup_plan())
    RE.msg_hook = BMM_msg_hook
        
