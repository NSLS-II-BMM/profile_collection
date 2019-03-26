import bluesky as bs
import bluesky.plans as bp
import bluesky.plan_stubs as bps
from bluesky import __version__ as bluesky_version
import numpy
import pandas
import os

from bluesky.preprocessors import subs_decorator
## see 65-derivedplot.py for DerivedPlot class
## see 10-motors.py and 20-dcm.py for motor definitions

run_report(__file__)

####################################
# generic timescan vs. It/If/Ir/I0 #
####################################
def timescan(detector, readings, dwell, delay, force=False, md={}):
    '''
    Generic timescan plan.

    For example:
       RE(timescan('it', 100, 0.5))

       detector: detector to display -- if, it, ir, or i0
       readings: number of measurements to make
       dwell:    dwell time in seconds for each measurement
       delay:    pause in seconds between measurements
       outfile:  data file name (relative to DATA), False to not write
       force:    flag for forcing a scan even if not clear to start

    This does not write an ASCII data file, but it does make a log entry.

    Use the ts2dat() function to extract the linescan from the
    database and write it to a file.
    '''

    (ok, text) = BMM_clear_to_start()
    if force is False and ok is False:
        print(colored(text, 'lightred'))
        yield from null()
        return

    
    RE.msg_hook = None
    ## sanitize and sanity checks on detector
    detector = detector.capitalize()
    if detector not in ('It', 'If', 'I0', 'Iy', 'Ir'):
        print(colored('\n*** %s is not a timescan measurement (%s)\n' %
                      (detector, 'it, if, i0, iy, ir'), 'lightred'))
        yield from null()
        return

    yield from abs_set(_locked_dwell_time, dwell)
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
    elif detector == 'If':
        dets.append(vor)
        denominator = ' / I0'
        func = lambda doc: (doc['time']-epoch_offset,
                            (doc['data']['DTC1'] +
                             doc['data']['DTC2'] +
                             doc['data']['DTC3'] +
                             doc['data']['DTC4']   ) / doc['data']['I0'])

    ## and this is the appropriate way to plot this linescan
    plot = DerivedPlot(func,
                       xlabel='elapsed time (seconds)',
                       ylabel=detector+denominator)

    line1 = '%s, N=%s, dwell=%.3f, delay=%.3f\n' % (detector, readings, dwell, delay)
    
    thismd = dict()
    thismd['XDI,Facility,GUP']    = BMM_xsp.gup
    thismd['XDI,Facility,SAF']    = BMM_xsp.saf
    thismd['XDI,Beamline,energy'] = dcm.energy.readback.value
    thismd['XDI,Scan,dwell_time'] = dwell
    thismd['XDI,Scan,delay']      = delay
    
    @subs_decorator(plot)
    def count_scan(dets, readings, delay):
        yield from count(dets, num=readings, delay=delay, md={**thismd, **md})

    dotfile = '/home/xf06bm/Data/.time.scan.running'
    with open(dotfile, "w") as f:
        f.write(str(datetime.datetime.timestamp(datetime.datetime.now())) + '\n')
    yield from count_scan(dets, readings, delay)
    
    BMM_log_info('timescan: %s\tuid = %s, scan_id = %d' %
                 (line1, db[-1].start['uid'], db[-1].start['scan_id']))
    if os.path.isfile(dotfile): os.remove(dotfile)

    yield from abs_set(_locked_dwell_time, 0.5)
    RE.msg_hook = BMM_msg_hook



def ts2dat(datafile, key):
    '''
    Export an timescan database entry to a simple column data file.

      ts2dat('/path/to/myfile.dat', 2948)

    or

      ts2dat('/path/to/myfile.dat', '42447313-46a5-42ef-bf8a-46fedc2c2bd1')

    The arguments are a data file name and the database key.
    '''

    if os.path.isfile(datafile):
        print(colored('%s already exists!  Bailing out....' % datafile, 'lightred'))
        return
    dataframe = db[key]

    devices = dataframe.devices() # note: this is a _set_ (this is helpful: https://snakify.org/en/lessons/sets/)
    if 'vor' in devices:
        column_list = ['time', 'I0', 'It', 'Ir',
                       'DTC1', 'DTC2', 'DTC3', 'DTC4',
                       'ROI1', 'ICR1', 'OCR1',
                       'ROI2', 'ICR2', 'OCR2',
                       'ROI3', 'ICR3', 'OCR3',
                       'ROI4', 'ICR4', 'OCR4']
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
    handle.write('# Beamline.energy: %.3f\n' % dataframe['start']['XDI,Beamline,energy'])
    handle.write('# Scan.dwell_time: %d\n'   % dataframe['start']['XDI,Scan,dwell_time'])
    handle.write('# Scan.delay: %d\n'        % dataframe['start']['XDI,Scan,delay'])
    try:
        handle.write('# Facility.GUP: %d\n'  % dataframe['start']['XDI,Facility,GUP'])
    except:
        pass
    try:
        handle.write('# Facility.SAF: %d\n'  % dataframe['start']['XDI,Facility,SAF'])
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
    print(colored('wrote timescan to %s' % datafile, 'white'))



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
                print(colored('\n%s does not exist!  Bailing out....\n' % orig, 'yellow'))
                return(orig, -1)
        print(colored('reading ini file: %s' % inifile, 'white'))
        (p, f) = scan_metadata(inifile=inifile, **kwargs)
        if not any(p):          # scan_metadata returned having printed an error message
            return(yield from null())
        #if not os.path.isdir(p['folder']):
        #    print(colored('\n%s is not a folder\n' % p['folder'], 'lightred'))
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
            print(colored('%s already exists!  Bailing out....' % outfile, 'lightred'))
            return(yield from null())

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## prompt user and verify that we are clear to start
        text = '\n'
        for k in ('folder', 'filename', 'experimenters', 'e0', 'npoints', 'dwell', 'delay',
                  'sample', 'prep', 'comment', 'mode', 'snapshots'):
            text = text + '      %-13s : %-50s\n' % (k,p[k])
        if BMM_xsp.prompt:
            boxedtext('How does this look?', text + '\n      %-13s : %-50s\n' % ('output file',outfile), 'green', width=len(outfile)+25) # see 05-functions
            action = input("\nBegin time scan? [Y/n then Enter] ")
            if action.lower() == 'q' or action.lower() == 'n':
                return(yield from null())

        (ok, ctstext) = BMM_clear_to_start()
        if force is False and ok is False:
            print(colored(ctstext, 'lightred'))
            yield from null()
            return


        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        # organize metadata for injection into database and XDI output
        print(colored('gathering metadata', 'white'))
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
        del(md['XDI,Element,edge'])
        del(md['XDI,Element,symbol'])
        md['XDI,Column,01'] = 'time seconds'
        md['XDI,Column,02'] = md.copy()['XDI,Column,03']
        md['XDI,Column,03'] = md.copy()['XDI,Column,04']
        md['XDI,Column,04'] = md['XDI,Column,05']
        del(md['XDI,Column,05'])

        rightnow = metadata_at_this_moment() # see 62-metadata.py
    
        BMM_log_info('Starting single-energy absorption detection time scan using\n%s:\n%s\nCommand line arguments = %s\nMoving to measurement energy: %.1f eV' %
                     (inifile, text, str(kwargs), p['e0']))


        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## move to the energy specified in the INI file
        print(colored('Moving to measurement energy: %.1f eV' % p['e0'], 'white'))
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
        yield from timescan(detector, p['npoints'], p['dwell'], p['delay'], force=force, md={**md, **rightnow})
        
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## write the output file
        header = db[-1]
        write_XDI(outfile, header, p['mode'], p['comment'], kind='sead') # yield from ?
        report('wrote time scan to %s' % outfile)
        #BMM_log_info('wrote time scan to %s' % outfile)
        #print(colored('wrote %s' % outfile, 'white'))

    def cleanup_plan():
        print('Cleaning up after single energy absorption detector measurement')
        RE.clear_suspenders()
        yield from abs_set(_locked_dwell_time, 0.5)
        dotfile = '/home/xf06bm/Data/.time.scan.running'
        if os.path.isfile(dotfile): os.remove(dotfile)
        dcm.mode = 'fixed'

    RE.msg_hook = None
    ## encapsulation!
    yield from bluesky.preprocessors.finalize_wrapper(main_plan(inifile, force, **kwargs), cleanup_plan())
    RE.msg_hook = BMM_msg_hook
        
