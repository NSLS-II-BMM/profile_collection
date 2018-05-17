import bluesky as bs
import bluesky.plans as bp
import numpy
import os

# p = scan_metadata(inifile='/home/bravel/commissioning/scan.ini', filename='humbleblat.flarg', start=10)
# (energy_grid, time_grid, approx_time) = conventional_grid(p['bounds'],p['steps'],p['times'],e0=p['e0'])  
# then call bmm_metadata() to get metadata in an XDI-ready format


KTOE = 3.8099819442818976
def etok(ee):
    return numpy.sqrt(ee/KTOE)
def ktoe(k):
    return k*k*KTOE


CS_BOUNDS     = [-200, -30, 15.3, '14k']
CS_STEPS      = [10, 0.5, '0.05k']
CS_TIMES      = [0.5, 0.5, '0.25k']
CS_MULTIPLIER = 1.3
CS_DEFAULTS   = {'folder':    os.environ.get('HOME')+'/data/',
                 'filename':  'data.dat',
                 'e0':        7112,
                 'element':   'Fe',
                 'edge':      'K',
                 'sample':    '',
                 'prep':      '',
                 'comment':   '',
                 'nscans':    1,
                 'start':     0,
                 'inttime':   1,
                 'bothways':  False,
                 'channelcut':True,
                 'focus':     False,
                 'hr':        True,
                 'mode':      'transmission'}
               

import inspect
import configparser
def scan_metadata(inifile=None, folder=None, filename=None,
                  e0=None, element=None, edge=None, sample=None, prep=None, comment=None,
                  nscans=None, start=None, inttime=None,
                  bothways=None, channelcut=None, focus=None, hr=None,
                  mode=None, bounds=None, steps=None, times=None):
    """Typical use is to specify an INI file, which contains all the
    metadata relevant to a set of scans.  In that case, this is called
    with one argument:

      parameters = scan_metadata(inifile='/path/to/inifile')

      inifile:  fully resolved path to INI file describing the measurement.

      returns a dictionary of metadata

    As part of a multi-scan plan (i.e. a macro), individual metadatum
    can be specified to override values in the INI file:

      folder:     folder for saved XDI files
      filename:   filename stub for saved XDI files
      e0:         edge energy, reference value for energy grid
      element:    one- or two-letter element symbol
      edge:       K, L3, L2, or L1
      sample:     description of sample, perhaps stoichiometry
      prep:       a short statement about sample preparation
      comment:    user-supplied comment about the data
      nscan:      number of repetitions
      start:      starting scan number, XDI file will be filename.###
      inttime:    <not used>
      bothways:   a flag for measuring in both monochromator directions
      channelcut: a flag for measuring in pseudo-channel-cut mode
      focus:      a flag indicating whether the focusing mirror is in use
      hr:         a flag indicating whether the flat harmonic rejection mirror is in use
      mode:       transmission, fluorescence, or reference -- basically a hint for how to display the data
      bounds:     a list with the scan grid boundaries
      steps:      a list with the scan grid step sizes
      times:      a list with the scan grid dwell times

    Any or all of these can be specified.  Values from the INI file
    are read first, then overridden with specified values.  If values
    are specified neither in the INI file nor in the function call,
    (possibly) sensible defaults are used.

    """
    #args = dict(zip(scan_metadata.__code__.co_varnames, scan_metadata.__defaults__))
    #args = locals()
    frame = inspect.currentframe()         # see https://stackoverflow.com/a/582206 and
    args = inspect.getargvalues(frame)[3]  # https://docs.python.org/3/library/inspect.html#inspect.getargvalues

    p = dict()

    if inifile is None:
        print('No inifile specified')
        return
    if not os.path.isfile(inifile):
        print('inifile does not exist')
        return
    config = configparser.ConfigParser()
    config.read_file(open(inifile))

    ## ----- scan regions
    if bounds is None:
        bounds = []
        try:
            for f in config.get('scan', 'bounds').split():
                try:
                    bounds.append(float(f))
                except:
                    bounds.append(f)
        except:
            bounds = CS_BOUNDS

    if steps is None:
        steps = []
        try:
            for f in config.get('scan', 'steps').split():
                try:
                    steps.append(float(f))
                except:
                    steps.append(f)
        except:
            steps = CS_STEPS
    
    if times is None:
        times = []
        try:
            for f in config.get('scan', 'times').split():
                try:
                    times.append(float(f))
                except:
                    times.append(f)
        except:
            times = CS_TIMES

    ## strings
    for a in ('folder', 'element', 'edge', 'filename', 'comment', 'mode', 'sample', 'prep'):
        if args[a] is None:
            try:
                p[a] = config.get('scan', a)
            except configparser.NoOptionError:
                p[a] = CS_DEFAULTS[a]
        else:
            p[a] = str(args[a])

    ## integers
    for a in ('start', 'nscans'):
        if args[a] is None:
            try:
                p[a] = int(config.get('scan', a))
            except configparser.NoOptionError:
                p[a] = CS_DEFAULTS[a]
        else:
            p[a] = int(args[a])
        
    ## floats
    for a in ('e0', 'inttime'):
        if args[a] is None:
            try:
                p[a] = float(config.get('scan', a))
            except configparser.NoOptionError:
                p[a] = CS_DEFAULTS[a]
        else:
            p[a] = float(args[a])
        
    ## booleans
    for a in ('bothways', 'channelcut', 'focus', 'hr'):
        if args[a] is None:
            try:
                p[a] = config.getboolean('scan', a)
            except configparser.NoOptionError:
                p[a] = CS_DEFAULTS[a]
        else:
            p[a] = bool(args[a])

    p['bounds'] = bounds
    p['steps']  = steps
    p['times']  = times
    return p

        
## need more error checking:
##   * sanitize the '#.#k' strings
##   * negative boundaries must be floats
##   * steps cannot be negative
##   * times cannot be negative
##   * steps smaller than, say, '0.01k'
##   * k^2 times
def conventional_grid(bounds=CS_BOUNDS, steps=CS_STEPS, times=CS_TIMES, e0=7112):
    '''Input:
       bounds:   (list) N relative energy values denoting the region boundaries of the step scan
       steps:    (list) N-1 energy step sizes
       times:    (list) N-1 integration time values
       e0:       (float) edge energy, reference for boundary values
    Output:
       grid:     (list) absolute energy values
       timegrid: (list) integration times
       approximate_time: (float) a very crude estimnate of how long in minutes the scan will take

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
        return (None, None)
    if (len(bounds) - len(times)) != 1:
        return (None, None)
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
        if type(times[i]) is str:
            tar = etok(ar-e0)*float(times[i][:-1])
        else:
            tar = times[i]*numpy.ones(len(ar))
        timegrid = timegrid + list(tar)
    approximate_time = "%.1f" % ((sum(timegrid) + float(len(timegrid))*CS_MULTIPLIER) / 60.0)
    return (grid, timegrid, float(approximate_time))

## vortex_me4.count_mode.put(0)               put the Struck in OneCount mode (1 is AutoCount)
## vortex_me4.preset_time.put(0.5)            set the OneCount accumulation time
## vortex_me4.auto_count_time.put(0.5)        set the AutoCount accumulation time
## vortex_me4.count.put(1)                    trigger a OneCount
## ... then can get the channel values

## quadem1.acquire_mode.put(0)                Continuous acquire mode
## quadem1.acquire_mode.put(1)                Multiple acquire mode
## quadem1.acquire_mode.put(2)                Single acquire mode
## quadem1.acquire.put(1)                     trigger acquisition in any of the modes
## ... then can get the channel values

## -----------------------
##  energy scan plan concept
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
