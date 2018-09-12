import bluesky as bs
import bluesky.plans as bp
import bluesky.plan_stubs as bps
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
def timescan(detector, readings, dwell, delay, outfile=False, force=False, md={}):
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

    if DATA not in outfile:
        outfile = DATA + outfile
    if outfile is not False and os.path.isfile(outfile):
        print(colored('%s already exists!  Bailing out....' % outfile, 'lightred'))
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
    
    @subs_decorator(plot)
    def count_scan(dets, readings, delay):
        yield from count(dets, num=readings, delay=delay, md={**thismd, **md})

    yield from count_scan(dets, readings, delay)
    if outfile is not False:
        ts2dat(outfile, -1)
        line1 = '%s, N=%s, dwell=%.3f, delay=%.3f, outfile=%s \n' % (detector, readings, dwell, delay, outfile)
    
    BMM_log_info('timescan: %s\tuid = %s, scan_id = %d' %
                 (line1, db[-1].start['uid'], db[-1].start['scan_id']))

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
    handle.write('# Beamline.energy: %.3f\n' % dataframe['start']['XDI,Beamline,energy'])
    handle.write('# Scan.start_time: %s\n'   % start_time)
    handle.write('# Scan.end_time: %s\n'     % end_time)
    handle.write('# Scan.uid: %s\n'          % dataframe['start']['uid'])
    handle.write('# Scan.transient_id: %d\n' % dataframe['start']['scan_id'])
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

