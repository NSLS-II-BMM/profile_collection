import bluesky as bs
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import numpy
import os
import re

run_report(__file__)

# p = scan_metadata(inifile='/home/bravel/commissioning/scan.ini', filename='humbleblat.flarg', start=10)
# (energy_grid, time_grid, approx_time) = conventional_grid(p['bounds'],p['steps'],p['times'],e0=p['e0'])
# then call bmm_metadata() to get metadata in an XDI-ready format

CS_BOUNDS     = [-200, -30, 15.3, '14k']
CS_STEPS      = [10, 0.5, '0.05k']
CS_TIMES      = [0.5, 0.5, '0.25k']
CS_MULTIPLIER = 1.425
CS_DEFAULTS   = {'bounds':        [-200, -30, 15.3, '14k'],
                 'steps':         [10, 0.5, '0.05k'],
                 'times':         [0.5, 0.5, '0.25k'],

                 'folder':        os.environ.get('HOME')+'/data/',
                 'filename':      'data.dat',
                 'experimenters': '',
                 'e0':            7112,
                 'element':       'Fe',
                 'edge':          'K',
                 'sample':        '',
                 'prep':          '',
                 'comment':       '',
                 'nscans':        1,
                 'start':         0,
                 'inttime':       1,
                 'snapshots':     True,
                 'bothways':      False,
                 'channelcut':    True,
                 'mode':          'transmission',

                 'npoints':       0,
                 'dwell':         1.0,
                 'delay':         0.1}


#import inspect
import configparser
    #folder=None, filename=None,
    #e0=None, element=None, edge=None, sample=None, prep=None, comment=None,
    #nscans=None, start=None, inttime=None,
    #snapshots=None, bothways=None, channelcut=None, focus=None, hr=None,
    #mode=None, bounds=None, steps=None, times=None):

def next_index(folder, stub):
    listing = os.listdir(folder)
    r = re.compile(stub + '\.\d\d\d')
    results = sorted(list(filter(r.match, listing)))
    if len(results) == 0:
        return 1
    return int(results[-1][-3:]) + 1


def scan_metadata(inifile=None, **kwargs):
    """Typical use is to specify an INI file, which contains all the
    metadata relevant to a set of scans.  This function is called with
    one argument:

      parameters = scan_metadata(inifile='/path/to/inifile')

      inifile:  fully resolved path to INI file describing the measurement.

    A dictionary of metadata is returned.

    As part of a multi-scan plan (i.e. a macro), individual metadata
    can be specified as kwargs to override values in the INI file.
    The kwarg keys are the same as the keys in the dictionary which is
    returned:

      folder:       [str]   folder for saved XDI files
      filename:     [str]   filename stub for saved XDI files
      experimenters [str]   names of people involved in this measurements
      e0:           [float] edge energy, reference value for energy grid
      element:      [str]   one- or two-letter element symbol
      edge:         [str]   K, L3, L2, or L1
      sample:       [str]   description of sample, perhaps stoichiometry
      prep:         [str]   a short statement about sample preparation
      comment:      [str]   user-supplied comment about the data
      nscan:        [int]   number of repetitions
      start:        [int]   starting scan number, XDI file will be filename.###
      snapshots:    [bool]  True = capture analog and XAS cameras before scan sequence
      bothways:     [bool]  True = measure in both monochromator directions
      channelcut:   [bool]  True = measure in pseudo-channel-cut mode
      mode:         [str]   transmission, fluorescence, or reference -- how to display the data
      bounds:       [list]  scan grid boundaries (not kwarg-able at this time)
      steps:        [list]  scan grid step sizes (not kwarg-able at this time)
      times:        [list]  scan grid dwell times (not kwarg-able at this time)

    Any or all of these can be specified.  Values from the INI file
    are read first, then overridden with specified values.  If values
    are specified neither in the INI file nor in the function call,
    (possibly) sensible defaults are used.

    """
    #frame = inspect.currentframe()          # see https://stackoverflow.com/a/582206 and
    #args  = inspect.getargvalues(frame)[3]  # https://docs.python.org/3/library/inspect.html#inspect.getargvalues

    parameters = dict()

    if inifile is None:
        print(colored('\nNo inifile specified\n', 'lightred'))
        return {}, {}
    if not os.path.isfile(inifile):
        print(colored('\ninifile does not exist\n', 'lightred'))
        return {}, {}

    config = configparser.ConfigParser(interpolation=None)
    config.read_file(open(inifile))

    found = dict()

    ## ----- scan regions
    for a in ('bounds', 'steps', 'times'):
        found[a] = False
        if a not in kwargs:
            parameters[a] = []
            try:
                for f in config.get('scan', a).split():
                    try:
                        parameters[a].append(float(f))
                    except:
                        parameters[a].append(f)
                    found[a] = True
            except:
                parameters[a] = CS_DEFAULTS[a]
    parameters['bounds_given'] = parameters['bounds'].copy()

    ## ----- strings
    for a in ('folder', 'experimenters', 'element', 'edge', 'filename', 'comment',
              'mode', 'sample', 'prep'):
        found[a] = False
        if a not in kwargs:
            try:
                parameters[a] = config.get('scan', a)
                found[a] = True
            except configparser.NoOptionError:
                parameters[a] = CS_DEFAULTS[a]
        else:
            parameters[a] = str(kwargs[a])
            found[a] = True

    if not os.path.isdir(parameters['folder']):
        print(colored('\nfolder %s does not exist\n' % parameters['folder'], 'lightred'))
        return {}, {}

            
    ## ----- start value
    if 'start' not in kwargs:
        try:
            parameters['start'] = str(config.get('scan', 'start'))
            found['start'] = True
        except configparser.NoOptionError:
            parameters['start'] = CS_DEFAULTS['start']
    else:
        parameters['start'] = str(kwargs['start'])
        found['start'] = True
    try:
        if parameters['start'] == 'next':
            parameters['start'] = next_index(parameters['folder'],parameters['filename'])
        else:
            parameters['start'] = int(parameters['start'])
    except ValueError:
        print(colored('\nstart value must be a positive integer or "next"', 'lightred'))
        parameters['start'] = -1
        found['start'] = False

    ## ----- integers
    for a in ('nscans', 'npoints'):
        found[a] = False
        if a not in kwargs:
            try:
                parameters[a] = int(config.get('scan', a))
                found[a] = True
            except configparser.NoOptionError:
                parameters[a] = CS_DEFAULTS[a]
        else:
            parameters[a] = int(kwargs[a])
            found[a] = True

    ## ----- floats
    for a in ('e0', 'inttime', 'dwell', 'delay'):
        found[a] = False
        if a not in kwargs:
            try:
                parameters[a] = float(config.get('scan', a))
                found[a] = True
            except configparser.NoOptionError:
                parameters[a] = CS_DEFAULTS[a]
        else:
            parameters[a] = float(kwargs[a])
            found[a] = True

    ## ----- booleans
    for a in ('snapshots', 'bothways', 'channelcut'):
        found[a] = False
        if a not in kwargs:
            try:
                parameters[a] = config.getboolean('scan', a)
                found[a] = True
            except configparser.NoOptionError:
                parameters[a] = CS_DEFAULTS[a]
        else:
            parameters[a] = bool(kwargs[a])
            found[a] = True

    return parameters, found


## need more error checking:
##   * sanitize the '#.#k' strings
##   * check that bounds are float or float+'k'
##   * negative boundaries must be floats
##   * steps cannot be negative
##   * times cannot be negative
##   * steps smaller than, say, '0.01k'
##   * steps smaller than 0.01
##   * k^2 times
##   * switch back to energy units afetr a k-valued boundary?
##   * out of order boundaries -- sort?
def conventional_grid(bounds=CS_BOUNDS, steps=CS_STEPS, times=CS_TIMES, e0=7112):
    '''Input:
       bounds:   (list) N relative energy values denoting the region boundaries of the step scan
       steps:    (list) N-1 energy step sizes
       times:    (list) N-1 integration time values
       e0:       (float) edge energy, reference for boundary values
    Output:
       grid:     (list) absolute energy values
       timegrid: (list) integration times
       approximate_time: (float) a very crude estimate of how long in minutes the scan will take

    Boundary values are either in eV units or wavenumber units.
    Values in eV units are floats, wavenumber units are strings of the
    form '0.5k' or '1k'.  String valued boundaries indicate a value to
    be converted from wavenumber to energy.  E.g. '14k' will be
    converted to 746.75 eV, i.e. that much above the edge energy.

    Step values are either in eV units (floats) or wavenumber units
    (strings).  Again, wavenumber values will be converted to energy
    steps as appropriate.  For example, '0.05k' will be converted into
    energy steps such that the steps are constant 0.05 invAng in
    wavenumber.

    Time values are either in units of seconds (floats) or strings.
    If strings, the integration time will be a multiple of the
    wavenumber value of the energy point.  For example, '0.5k' says to
    integrate for a number of seconds equal to half the wavenumber.
    So at 5 invAng, integrate for 2.5 seconds.  At 10 invAng,
    integrate for 5 seconds.

    Examples:
       -- this is the default (same as (g,it,at) = conventional_grid()):
       (grid, inttime, time) = conventional_grid(bounds=[-200, -30, 15.3, '14k'],
                                                 steps=[10, 0.5, '0.05k'],
                                                 times=[0.5, 0.5, '0.25k'], e0=7112)

       -- more regions
       (grid, inttime, time) = conventional_grid(bounds=[-200.0, -20.0, 30.0, '5k', '14.5k'],
                                                 steps=[10.0, 0.5, 2, '0.05k'],
                                                 times=[1, 1, 1, '1k'], e0=7112)

       -- many regions, energy boundaries, k-steps
       (grid, inttime, time) = conventional_grid(bounds=[-200, -30, -10, 15, 100, 300, 500, 700, 900],
                                                 steps=[10, 2, 0.5, '0.05k', '0.05k', '0.05k', '0.05k', '0.05k'],
                                                 times=[0.5, 0.5, 0.5, 1, 2, 3, 4, 5], e0=7112)

       -- a one-region xanes scan
       (grid, inttime, time) = conventional_grid(bounds=[-10, 40],
                                                 steps=[0.25,],
                                                 times=[0.5,], e0=7112)
    '''
    if (len(bounds) - len(steps)) != 1:
        return (None, None, None)
    if (len(bounds) - len(times)) != 1:
        return (None, None, None)
    for i,s in enumerate(bounds):
        if type(s) is str:
            this = float(s[:-1])
            bounds[i] = ktoe(this)

    grid = list()
    timegrid = list()
    for i,s in enumerate(steps):
        if type(s) is str:
            step = float(s[:-1])
            ar = e0 + ktoe(numpy.arange(etok(bounds[i]), etok(bounds[i+1]), step))
        else:
            ar = numpy.arange(e0+bounds[i], e0+bounds[i+1], steps[i])
        grid = grid + list(ar)
        grid = list(numpy.round(grid, decimals=2))
        if type(times[i]) is str:
            tar = etok(ar-e0)*float(times[i][:-1])
        else:
            tar = times[i]*numpy.ones(len(ar))
        timegrid = timegrid + list(tar)
        timegrid = list(numpy.round(timegrid, decimals=2))
    approximate_time = (sum(timegrid) + float(len(timegrid))*CS_MULTIPLIER) / 60.0
    return (grid, timegrid, round(approximate_time, 1))

## vor.count_mode.put(0)               put the Struck in OneCount mode (1 is AutoCount)
## vor.preset_time.put(0.5)            set the OneCount accumulation time
## vor.auto_count_time.put(0.5)        set the AutoCount accumulation time
## vor.count.put(1)                    trigger a OneCount
## ... then can get the channel values

## quadem1.acquire_mode.put(0)                Continuous acquire mode
## quadem1.acquire_mode.put(1)                Multiple acquire mode
## quadem1.acquire_mode.put(2)                Single acquire mode
## quadem1.acquire.put(1)                     trigger acquisition in any of the modes
## ... then can get the channel values

## -----------------------
##  energy step scan plan concept
##  1. collect metadata from an INI file
##  2. compute scan grid
##  3. move to center of angular range
##  4. drop into pseudo channel cut mode
##  5. set OneCount and Single modes on the detectors
##  6. begin scan repititions, for each one
##     a. scan:
##          i. make metadata dict, set md argument in call to scan plan
##         ii. move
##        iii. set acquisition time for this point
##         iv. trigger
##          v. collect
##     b. grab dataframe from Mongo
##        http://nsls-ii.github.io/bluesky/tutorial.html#aside-access-saved-data
##     c. write XDI file
##  8. return to fixed exit mode
##  9. return detectors to AutoCount and Continuous modes


def channelcut_energy(e0, bounds):
    for i,s in enumerate(bounds):
        if type(s) is str:
            this = float(s[:-1])
            bounds[i] = ktoe(this)
    amin = dcm.e2a(e0+bounds[0])
    amax = dcm.e2a(e0+bounds[-1])
    aave = amin + 1.0*(amax - amin) / 2.0
    wavelength = dcm.wavelength(aave)
    eave = e2l(wavelength)
    return eave


def ini_sanity(found):
    ok = True
    missing = []
    for a in ('bounds', 'steps', 'times', 'e0', 'element', 'edge', 'folder', 'filename', 'nscans', 'start'):
        if found[a] is False:
            ok = False
            missing.append(a)
    return (ok, missing)



##########################################################
# --- export a database energy scan entry to an XDI file #
##########################################################
def db2xdi(datafile, key):
    '''
    Export a database entry for an XAFS scan to an XDI file.

       db2xdi('/path/to/myfile.xdi', 1533)

    or

       db2xdi('/path/to/myfile.xdi', '0783ac3a-658b-44b0-bba5-ed4e0c4e7216')

    The arguments are th resolved path to the output XDI file and
    a database key.
    '''
    if os.path.isfile(datafile):
        print(colored('%s already exists!  Bailing out....' % datafile, 'lightred'))
        return
    header = db[key]
    ## sanity check, make sure that db returned a header AND that the header was an xafs scan
    write_XDI(datafile, header, header.start['XDI,_mode'][0], header.start['XDI,_comment'][0])
    print(colored('wrote %s' % datafile, 'white'))



import bluesky.preprocessors
from bluesky.preprocessors import subs_decorator
import pprint
pp = pprint.PrettyPrinter(indent=4)



#########################
# -- the main XAFS scan #
#########################
def xafs(inifile, **kwargs):
    '''
    Read an INI file for scan matadata, then perform an XAFS scan sequence.
    '''
    def main_plan(inifile, **kwargs):
        if '311' in dcm._crystal and dcm_x.user_readback.value < 0:
            BMM_xsp.final_log_entry = False
            print(colored('The DCM is in the 111 position, configured as 311', 'lightred'))
            print(colored('\tdcm.x: %.2f mm\t dcm._crystal: %s' % (dcm_x.user_readback.value, dcm._crystal), 'lightred'))
            yield from null()
            return
        if '111' in dcm._crystal and dcm_x.user_readback.value > 0:
            BMM_xsp.final_log_entry = False
            print(colored('The DCM is in the 311 position, configured as 111', 'lightred'))
            print(colored('\tdcm_x: %.2f mm\t dcm._crystal: %s' % (dcm_x.user_readback.value, dcm._crystal), 'lightred'))
            yield from null()
            return

        supplied_metadata = dict()
        if 'md' in kwargs and type(kwargs['md']) == dict:
            supplied_metadata = kwargs['md']
        
        (ok, text) = BMM_clear_to_start()
        if 'force' in kwargs and kwargs['force'] is True:
            (ok, text) = (True, '')
        if ok is False:
            BMM_xsp.final_log_entry = False
            print(colored('\n'+text, 'lightred'))
            print(colored('Quitting scan sequence....\n', 'white'))
            yield from null()
            return

        ## make sure we are ready to scan
        #yield from abs_set(_locked_dwell_time.quadem_dwell_time.settle_time, 0)
        #yield from abs_set(_locked_dwell_time.struck_dwell_time.settle_time, 0)
        _locked_dwell_time.quadem_dwell_time.settle_time = 0
        _locked_dwell_time.struck_dwell_time.settle_time = 0


        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## user input, find and parse the INI file
        inifile, estimate = howlong(inifile, interactive=False, **kwargs)
        if estimate == -1:
            BMM_xsp.final_log_entry = False
            yield from null()
            return
        (p, f) = scan_metadata(inifile=inifile, **kwargs)
        if not any(p):          # scan_metadata returned having printed an error message
            return(yield from null())        
        
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## user verification (disabled by BMM_xsp.prompt)
        eave = channelcut_energy(p['e0'], p['bounds'])
        length = 0
        if BMM_xsp.prompt:
            text = '\n'
            for k in ('bounds', 'bounds_given', 'steps', 'times'):
                addition = '      %-13s : %-50s\n' % (k,p[k])
                text = text + addition
                if len(addition) > length: length = len(addition)
            for (k,v) in p.items():
                if k in ('bounds', 'bounds_given', 'steps', 'times'):
                    continue
                if k in ('npoints', 'dwell', 'delay', 'inttime', 'channelcut', 'bothways'):
                    continue
                addition = '      %-13s : %-50s\n' % (k,v)
                text = text + addition
                if len(addition) > length: length = len(addition)
            boxedtext('How does this look?', text, 'green', width=length+4) # see 05-functions

            outfile = os.path.join(p['folder'], "%s.%3.3d" % (p['filename'], p['start']))
            print('\nFirst data file to be written to "%s"' % outfile)

            bail = False
            count = 0
            for i in range(p['start'], p['start']+p['nscans'], 1):
                count += 1
                fname = "%s.%3.3d" % (p['filename'], i)
                datafile = os.path.join(p['folder'], fname)
                if os.path.isfile(datafile):
                    print(colored('%s already exists!' % datafile, 'lightred'))
                    bail = True
            if bail:
                print(colored('\nOne or more output files already exist!  Quitting scan sequence....', 'lightred'))
                BMM_xsp.final_log_entry = False
                yield from null()
                return
            print(estimate)

            if not dcm.suppress_channel_cut:
                print('\nPseudo-channel-cut energy = %.1f' % eave)
            action = input("\nBegin scan sequence? [Y/n then Enter] ")
            if action.lower() == 'q' or action.lower() == 'n':
                BMM_xsp.final_log_entry = False
                yield from null()
                return

        with open(inifile, 'r') as fd: content = fd.read()
        output = re.sub(r'\n+', '\n', re.sub(r'\#.*\n', '\n', content)) # remove comment and blank lines
        BMM_log_info('starting XAFS scan using %s:\n%s\ncommand line arguments = %s' % (inifile, output, str(kwargs)))
        BMM_log_info(motor_status())

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## set up a plotting subscription, anonymous functions for plotting various forms of XAFS
        trans = lambda doc: (doc['data']['dcm_energy'], log(doc['data']['I0'] / doc['data']['It']))
        ref   = lambda doc: (doc['data']['dcm_energy'], log(doc['data']['It'] / doc['data']['Ir']))
        Yield = lambda doc: (doc['data']['dcm_energy'], -1*doc['data']['Iy'] / doc['data']['I0'])
        fluo  = lambda doc: (doc['data']['dcm_energy'], (doc['data']['DTC1'] +
                                                         doc['data']['DTC2'] +
                                                         doc['data']['DTC3'] +
                                                         doc['data']['DTC4']) / doc['data']['I0'])
        if 'fluo'    in p['mode']:
            plot =  DerivedPlot(fluo,  xlabel='energy (eV)', ylabel='absorption (fluorescence)')
        elif 'trans' in p['mode']:
            plot =  DerivedPlot(trans, xlabel='energy (eV)', ylabel='absorption (transmission)')
        elif 'ref'   in p['mode']:
            plot =  DerivedPlot(ref,   xlabel='energy (eV)', ylabel='absorption (reference)')
        elif 'yield' in p['mode']:
            plot =  DerivedPlot(Yield, xlabel='energy (eV)', ylabel='absorption (electron yield)')
        elif 'both'  in p['mode']:
            plot = [DerivedPlot(trans, xlabel='energy (eV)', ylabel='absorption (transmission)'),
                    DerivedPlot(fluo,  xlabel='energy (eV)', ylabel='absorption (fluorescence)')]
        else:
            print(colored('Plotting mode not specified, falling back to a transmission plot', 'lightred'))
            plot =  DerivedPlot(trans, xlabel='energy (eV)', ylabel='absorption (transmission)')


        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## engage suspenders right before starting scan sequence
        BMM_suspenders()

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## begin the scan sequence with the plotting subscription
        @subs_decorator(plot)
        def scan_sequence():
            ## perhaps enter pseudo-channel-cut mode
            if not dcm.suppress_channel_cut:
                BMM_log_info('entering pseudo-channel-cut mode at %.1f eV' % eave)
                print(colored('entering pseudo-channel-cut mode at %.1f eV' % eave, 'white'))
                dcm.mode = 'fixed'
                yield from mv(dcm.energy, eave)
                dcm.mode = 'channelcut'


            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## compute energy and dwell grids
            print(colored('computing energy and dwell time grids', 'white'))
            (energy_grid, time_grid, approx_time) = conventional_grid(p['bounds'], p['steps'], p['times'], e0=p['e0'])
            if energy_grid is None or time_grid is None or approx_time is None:
                print(colored('Cannot interpret scan grid parameters!  Bailing out....' % outfile, 'lightred'))
                BMM_xsp.final_log_entry = False
                yield from null()
                return


            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## organize metadata for injection into database and XDI output
            print(colored('gathering metadata', 'white'))
            md = bmm_metadata(measurement   = p['mode'],
                              experimenters = p['experimenters'],
                              edge          = p['edge'],
                              element       = p['element'],
                              edge_energy   = p['e0'],
                              direction     = 1,
                              scantype      = 'step',
                              channelcut    = p['channelcut'],
                              mono          = 'Si(%s)' % dcm._crystal,
                              i0_gas        = 'N2', #\
                              it_gas        = 'N2', # > these three need to go into INI file
                              ir_gas        = 'N2', #/
                              sample        = p['sample'],
                              prep          = p['prep'],
                              stoichiometry = None,
                              mode          = p['mode'],
                              comment       = p['comment'],
                          )

            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## show the metadata to the user
            for (k, v) in md.items():
                print('\t%-28s : %s' % (k[4:].replace(',','.'),v))

            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## snap photos
            if p['snapshots']:
                #now = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
                image = os.path.join(p['folder'], 'snapshots', "%s_XASwebcam_%s.jpg" % (p['filename'], now()))
                snap('XAS', filename=image)
                image = os.path.join(p['folder'], 'snapshots', "%s_analog_%s.jpg" % (p['filename'], now()))
                snap('analog', filename=image)

            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## write dotfile
            with open(dotfile, "w") as f:
                f.write(str(datetime.datetime.timestamp(datetime.datetime.now())) + '\n')
                f.write('%.1f\n' % approx_time * int(p['nscans']) * 60)
                
            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## loop over scan count
            count = 0
            for i in range(p['start'], p['start']+p['nscans'], 1):
                count += 1
                fname = "%s.%3.3d" % (p['filename'], i)
                datafile = os.path.join(p['folder'], fname)
                if os.path.isfile(datafile):
                    ## shouldn't be able to get here, unless a file
                    ## was written since the scan sequence began....
                    print(colored('%s already exists!  Bailing out....' % datafile, 'lightred'))
                    yield from null()
                    return
                print(colored('starting scan %d of %d, %d energy points' %
                              (count, p['nscans'], len(energy_grid)), 'white'))

                ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
                ## compute trajectory
                energy_trajectory    = cycler(dcm.energy, energy_grid)
                dwelltime_trajectory = cycler(dwell_time, time_grid)

                ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
                ## need to set certain metadata items on a per-scan basis... temperatures, ring stats
                ## mono direction, ... things that can change during or between scan sequences
                md['XDI,Mono,direction'] = 'forward'
                if p['bothways'] and count%2 == 0:
                    energy_trajectory    = cycler(dcm.energy, energy_grid[::-1])
                    dwelltime_trajectory = cycler(dwell_time, time_grid[::-1])
                    md['XDI,Mono,direction'] = 'backward'
                rightnow = metadata_at_this_moment() # see 62-metadata.py


                ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
                ## call the stock scan plan with the correct detectors
                if 'trans' in p['mode'] or 'ref' in p['mode'] or 'yield' in p['mode']:
                    yield from scan_nd([quadem1], energy_trajectory + dwelltime_trajectory,
                                       md={**md, **rightnow, **supplied_metadata})
                else:
                    yield from scan_nd([quadem1, vor], energy_trajectory + dwelltime_trajectory,
                                       md={**md, **rightnow, **supplied_metadata})
                header = db[-1]
                write_XDI(datafile, header, p['mode'], p['comment']) # yield from ?
                print(colored('wrote %s' % datafile, 'white'))
                BMM_log_info('energy scan finished, uid = %s, scan_id = %d\ndata file written to %s'
                             % (db[-1].start['uid'], db[-1].start['scan_id'], datafile))


            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## finish up, close out
            print('Returning to fixed exit mode and returning DCM to %1.f' % eave)
            dcm.mode = 'fixed'
            yield from mv(dcm.energy, eave)

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## execute this scan sequence plan
        yield from scan_sequence()

    def cleanup_plan():
        print('Cleaning up after an XAFS scan sequence')
        RE.clear_suspenders()
        if os.path.isfile(dotfile):
            os.remove(dotfile)
        if BMM_xsp.final_log_entry is True:
            BMM_log_info('XAFS scan sequence finished\nmost recent uid = %s, scan_id = %d'
                         % (db[-1].start['uid'], db[-1].start['scan_id']))
        #else:
        #    BMM_log_info('XAFS scan sequence finished early')
        dcm.mode = 'fixed'
        yield from abs_set(_locked_dwell_time.struck_dwell_time.setpoint, 0.5)
        yield from abs_set(_locked_dwell_time.quadem_dwell_time.setpoint, 0.5)
        yield from bps.sleep(2.0)
        yield from abs_set(dcm_pitch.kill_cmd, 1)
        yield from abs_set(dcm_roll.kill_cmd, 1)

    dotfile = '/home/xf06bm/Data/.xafs.scan.running'
    BMM_xsp.final_log_entry = True
    RE.msg_hook = None
    ## encapsulation!
    yield from bluesky.preprocessors.finalize_wrapper(main_plan(inifile, **kwargs), cleanup_plan())
    RE.msg_hook = BMM_msg_hook


def howlong(inifile, interactive=True, **kwargs):
    ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
    ## user input, find and parse the INI file
    ## try inifile as given then DATA + inifile
    ## this allows something like RE(xafs('myscan.ini')) -- short 'n' sweet
    orig = inifile
    if not os.path.isfile(inifile):
        inifile = DATA + inifile
        if not os.path.isfile(inifile):
            print(colored('\n%s does not exist!  Bailing out....\n' % orig, 'yellow'))
            return(orig, -1)
    print(colored('reading ini file: %s' % inifile, 'white'))
    (p, f) = scan_metadata(inifile=inifile, **kwargs)
    (ok, missing) = ini_sanity(f)
    if not ok:
        print(colored('\nThe following keywords are missing from your INI file: ', 'lightred'),
              '%s\n' % str.join(', ', missing))
        return(orig, -1)
    (energy_grid, time_grid, approx_time) = conventional_grid(p['bounds'], p['steps'], p['times'], e0=p['e0'])
    text = '\nEach scan will take about %.1f minutes\n' % approx_time
    text +='The sequence of %s will take about %.1f hours' % (inflect('scan', p['nscans']), approx_time * int(p['nscans'])/60)
    if interactive:
        print(text)
    else:
        return(inifile, text)
