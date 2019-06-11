import bluesky as bs
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import numpy
import os
import re
import subprocess
import textwrap

run_report(__file__)

# p = scan_metadata(inifile='/home/bravel/commissioning/scan.ini', filename='humbleblat.flarg', start=10)
# (energy_grid, time_grid, approx_time) = conventional_grid(p['bounds'],p['steps'],p['times'],e0=p['e0'])
# then call bmm_metadata() to get metadata in an XDI-ready format

CS_BOUNDS     = [-200, -30, 15.3, '14k']
CS_STEPS      = [10, 0.5, '0.05k']
CS_TIMES      = [0.5, 0.5, '0.25k']
CS_MULTIPLIER = 0.7
######################################################################
## replacing this with BMMuser, see 74-modes.py
# CS_DEFAULTS   = {'bounds':        [-200, -30, 15.3, '14k'],        #
#                  'steps':         [10, 0.5, '0.05k'],              #
#                  'times':         [0.5, 0.5, '0.25k'],             #
#                                                                    #
#                  'folder':        os.environ.get('HOME')+'/data/', #
#                  'filename':      'data.dat',                      #
#                  'experimenters': '',                              #
#                  'e0':            7112,                            #
#                  'element':       'Fe',                            #
#                  'edge':          'K',                             #
#                  'sample':        '',                              #
#                  'prep':          '',                              #
#                  'comment':       '',                              #
#                  'nscans':        1,                               #
#                  'start':         0,                               #
#                  'inttime':       1,                               #
#                  'snapshots':     True,                            #
#                  'usbstick':      True,                            #
#                  'rockingcurve':  False,                           #
#                  'htmlpage':      True,                            #
#                  'bothways':      False,                           #
#                  'channelcut':    True,                            #
#                  'mode':          'transmission',                  #
#                                                                    #
#                  'npoints':       0, # see 71-timescans.py         #
#                  'dwell':         1.0,                             #
#                  'delay':         0.1}                             #
######################################################################


import configparser
    #folder=None, filename=None,
    #e0=None, element=None, edge=None, sample=None, prep=None, comment=None,
    #nscans=None, start=None, inttime=None,
    #snapshots=None, bothways=None, channelcut=None, focus=None, hr=None,
    #mode=None, bounds=None, steps=None, times=None):

def next_index(folder, stub):
    '''Find the next numeric filename extension for a filename stub in folder.'''
    listing = os.listdir(folder)
    r = re.compile(re.escape(stub) + '\.\d+')
    results = sorted(list(filter(r.match, listing)))
    if len(results) == 0:
        return 1
    return int(results[-1][-3:]) + 1

## need more error checking:
##   ✓ sanitize the '#.#k' strings
##   ✓ check that bounds are float or float+'k'
##   ✓ negative boundaries must be floats
##   ✓ steps cannot be negative
##   ✓ times cannot be negative
##   ✓ steps smaller than, say, '0.01k'
##   ✓ steps smaller than 0.01
##   ✓ out of order boundaries -- sort?
##   * k^2 times
##   * switch back to energy units after a k-valued boundary?
##   * pre-edge k-values steps & times


def sanitize_step_scan_parameters(bounds, steps, times):
    '''Attempt to identify and flag/correct some common scan parameter mistakes.'''
    problem = False
    text = ''

    ############################################################################
    # bounds is one longer than steps/times, length of steps = length of times #
    ############################################################################
    if (len(bounds) - len(steps)) != 1:
        text += error_msg('\nbounds must have one more item than steps\n')
        text += error_msg('\tbounds = %s\n' % ' '.join(map(str, bounds)))
        text += error_msg('\tsteps = %s\n'  % ' '.join(map(str, steps)))
        problem = True
    if (len(bounds) - len(times)) != 1:
        text += error_msg('\nbounds must have one more item than times\n')
        text += error_msg('\tbounds = %s\n' % ' '.join(map(str, bounds)))
        text += error_msg('\ttimes = %s\n'  % ' '.join(map(str, times)))
        problem = True

    ############################
    # tests of boundary values #
    ############################
    for b in bounds:
        if not isfloat(b) and b[-1:].lower() == 'k':
            if not isfloat(b[:-1]):
                text += error_msg('\n%s is not a valid scan boundary value\n' % b)
                problem = True
        elif not isfloat(b):
            text += error_msg('\n%s is not a valid scan boundary value\n' % b)
            problem = True

        if not isfloat(b) and b[:1] == '-' and b[-1:].lower() == 'k':
            text += error_msg('\nNegative bounds must be energy-valued, not k-valued (%s)\n' % b) 
            problem = True
               
    #############################
    # tests of step size values #
    #############################
    for s in steps:
        if not isfloat(s) and s[-1:].lower() == 'k':
            if not isfloat(s[:-1]):
                text += error_msg('\n%s is not a valid scan step size value\n' % s)
                problem = True
            elif float(s[:-1]) < 0:
                text += error_msg('\nStep sizes cannot be negative (%s)\n' % s)
                problem = True
        elif not isfloat(s):
            text += error_msg('\n%s is not a valid scan step size value\n' % s)
            problem = True

        if isfloat(s) and float(s) < 0:
            text += error_msg('\nStep sizes cannot be negative (%s)\n' % s)
            problem = True
        elif isfloat(s) and float(s) <= 0.1:
            text += warning_msg('\n%s is a very small step size!\n' % s)
        elif not isfloat(s) and s[-1:].lower() == 'k' and isfloat(s[-1:]) and float(s[:-1]) < 0.01:
            text += warning_msg('\n%s is a very small step size!\n' % s)
            
                
    ####################################
    # tests of integration time values #
    ####################################
    for t in times:
        if not isfloat(t) and t[-1:].lower() == 'k':
            if not isfloat(t[:-1]):
                text += error_msg('\n%s is not a valid integration time value\n' % t)
                problem = True
            elif float(t[:-1]) < 0:
                text += error_msg('\nIntegration times cannot be negative (%s)\n' % t)
                problem = True
        elif not isfloat(t):
            text += error_msg('\n%s is not a valid integration time value\n' % t)
            problem = True

        if isfloat(t) and float(t) < 0:
            text += error_msg('\nIntegration times cannot be negative (%s)\n' % t)
            problem = True
        elif isfloat(t) and float(t) <= 0.1:
            text += warning_msg('\n%s is a very short integration time!\n' % t)
        elif not isfloat(t) and t[-1:].lower() == 'k' and isfloat(t[-1:]) and float(t[:-1]) < 0.05:
            text += warning_msg('\n%s is a very short integration time!\n' % t)

    if text:
        text += error_msg('\nsee ') + url_msg('https://nsls-ii-bmm.github.io/BeamlineManual/xafs.html#scan-regions\n')

            
    return problem, text
    


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
      usbstick:     [bool]  True = munge filenames so they can be written to a VFAT USB stick
      rockingcurve  [bool]  True = measure rocking curve at pseudo channel cut energy
      htmlpage:     [bool]  True = capture dossier of a scan sequence as a static html page
      bothways:     [bool]  True = measure in both monochromator directions
      channelcut:   [bool]  True = measure in pseudo-channel-cut mode
      ththth:       [bool]  True = measure using the Si(333) reflection
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
        print(error_msg('\nNo inifile specified\n'))
        return {}, {}
    if not os.path.isfile(inifile):
        print(error_msg('\ninifile does not exist\n'))
        return {}, {}

    config = configparser.ConfigParser(interpolation=None)
    config.read_file(open(inifile))

    found = dict()

    ## ----- scan regions (what about kwargs???)
    for a in ('bounds', 'steps', 'times'):
        found[a] = False
        parameters[a] = []
        if a not in kwargs:
            try:
                for f in config.get('scan', a).split():
                    try:
                        parameters[a].append(float(f))
                    except:
                        parameters[a].append(f)
                    found[a] = True
            except:
                parameters[a] = getattr(BMMuser, a)
        else:
            this = str(kwargs[a])
            for f in this.split():
                try:
                    parameters[a].append(float(f))
                except:
                    parameters[a].append(f)
            found[a] = True
        parameters['bounds_given'] = parameters['bounds'].copy()

    (problem, text) = sanitize_step_scan_parameters(parameters['bounds'], parameters['steps'], parameters['times'])
    print(text)
    if problem:
        return {}, {}

    ## ----- strings
    for a in ('folder', 'experimenters', 'element', 'edge', 'filename', 'comment',
              'mode', 'sample', 'prep'):
        found[a] = False
        if a not in kwargs:
            try:
                parameters[a] = config.get('scan', a)
                found[a] = True
            except configparser.NoOptionError:
                parameters[a] = getattr(BMMuser, a)
        else:
            parameters[a] = str(kwargs[a])
            found[a] = True

    if not os.path.isdir(parameters['folder']):
        print(error_msg('\nfolder %s does not exist\n' % parameters['folder']))
        return {}, {}

            
    ## ----- start value
    if 'start' not in kwargs:
        try:
            parameters['start'] = str(config.get('scan', 'start'))
            found['start'] = True
        except configparser.NoOptionError:
            parameters[a] = getattr(BMMuser, a)
    else:
        parameters['start'] = str(kwargs['start'])
        found['start'] = True
    try:
        if parameters['start'] == 'next':
            parameters['start'] = next_index(parameters['folder'],parameters['filename'])
        else:
            parameters['start'] = int(parameters['start'])
    except ValueError:
        print(error_msg('\nstart value must be a positive integer or "next"'))
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
                parameters[a] = getattr(BMMuser, a)
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
                parameters[a] = getattr(BMMuser, a)
        else:
            parameters[a] = float(kwargs[a])
            found[a] = True

    ## ----- booleans
    for a in ('snapshots', 'htmlpage', 'bothways', 'channelcut', 'usbstick', 'rockingcurve', 'ththth'):
        found[a] = False
        if a not in kwargs:
            try:
                parameters[a] = config.getboolean('scan', a)
                found[a] = True
            except configparser.NoOptionError:
                parameters[a] = getattr(BMMuser, a)
        else:
            parameters[a] = bool(kwargs[a])
            found[a] = True

    if dcm._crystal != '111' and parameters['ththth']:
        print(error_msg('\nYou must be using the Si(111) crystal to make a Si(333) measurement\n'))
        return {}, {}

    if not found['e0'] and found['element'] and found['edge']:
        parameters['e0'] = edge_energy(parameters['element'], parameters['edge'])
        if parameters['e0'] is None:
            print(error_msg('\nCannot figure out edge energy from element = %s and edge = %s\n' % (parameters['element'], parameters['edge'])))
            return {}, {}
        else:
            found['e0'] = True
            print('\nUsing tabulated value of %.1f for the %s %s edge\n' % (parameters['e0'], parameters['element'], parameters['edge']))
        
    return parameters, found


def conventional_grid(bounds=CS_BOUNDS, steps=CS_STEPS, times=CS_TIMES, e0=7112, ththth=False):
    '''Input:
       bounds:   (list) N relative energy values denoting the region boundaries of the step scan
       steps:    (list) N-1 energy step sizes
       times:    (list) N-1 integration time values
       e0:       (float) edge energy, reference for boundary values
       ththth:   (Boolean) using the Si(333) reflection
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
    bounds.sort()

    enot = e0
    if ththth:
        enot = e0/3.0
        bounds = list(array(bounds)/3)
    grid = list()
    timegrid = list()
    for i,s in enumerate(steps):
        if type(s) is str:
            step = float(s[:-1])
            if ththth: step = step/3.
            ar = enot + ktoe(numpy.arange(etok(bounds[i]), etok(bounds[i+1]), step))
        else:
            step = steps[i]
            if ththth: step = step/3.
            ar = numpy.arange(enot+bounds[i], enot+bounds[i+1], step)
        grid = grid + list(ar)
        grid = list(numpy.round(grid, decimals=2))
        if type(times[i]) is str:
            tar = etok(ar-enot)*float(times[i][:-1])
        else:
            tar = times[i]*numpy.ones(len(ar))
        timegrid = timegrid + list(tar)
        timegrid = list(numpy.round(timegrid, decimals=2))
    approximate_time = (sum(timegrid) + float(len(timegrid))*CS_MULTIPLIER) / 60.0
    return (grid, timegrid, round(approximate_time, 1))

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


def channelcut_energy(e0, bounds, ththth):
    '''From the scan parameters, find the energy at the center of the angular range of the scan.'''
    for i,s in enumerate(bounds):
        if type(s) is str:
            this = float(s[:-1])
            bounds[i] = ktoe(this)
    amin = dcm.e2a(e0+bounds[0])
    amax = dcm.e2a(e0+bounds[-1])
    if ththth:
        amin = dcm.e2a((e0+bounds[0])/3.0)
        amax = dcm.e2a((e0+bounds[-1])/3.0)
    aave = amin + 1.0*(amax - amin) / 2.0
    wavelength = dcm.wavelength(aave)
    eave = e2l(wavelength)
    return eave


def ini_sanity(found):
    '''Very simple sanity checking of the scan control file.'''
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

    The arguments are the resolved path to the output XDI file and
    a database key.
    '''
    if os.path.isfile(datafile):
        print(error_msg('%s already exists!  Bailing out....' % datafile))
        return
    header = db[key]
    ## sanity check, make sure that db returned a header AND that the header was an xafs scan
    write_XDI(datafile, header)
    print(bold_msg('wrote %s' % datafile))

from pygments import highlight
from pygments.lexers import PythonLexer, IniLexer
from pygments.formatters import HtmlFormatter

from urllib.parse import quote

def scan_sequence_static_html(inifile       = None,
                              filename      = None,
                              start         = None,
                              end           = None,
                              experimenters = None,
                              seqstart      = None,
                              seqend        = None,
                              e0            = None,
                              edge          = None,
                              element       = None,
                              scanlist      = None,
                              motors        = None,
                              sample        = None,
                              prep          = None,
                              comment       = None,
                              mode          = None,
                              pccenergy     = None,
                              bounds        = None,
                              steps         = None,
                              times         = None,
                              clargs        = '',
                              websnap       = '',
                              anasnap       = '',
                              htmlpage      = None,
                              ththth        = None,
                              ):
    '''
    Gather information from various places, including html_dict, a temporary dictionary 
    filled up during an XAFS scan, then write a static html file as a dossier for a scan
    sequence using a bespoke html template file
    '''
    if filename is None or start is None:
        return None
    firstfile = "%s.%3.3d" % (filename, start)
    if not os.path.isfile(os.path.join(DATA, firstfile)):
        return None
    
    with open(os.path.join(DATA, 'dossier', 'sample.tmpl')) as f:
        content = f.readlines()
    basename     = filename
    htmlfilename = os.path.join(DATA, 'dossier/',   filename+'-01.html')
    seqnumber = 1
    if os.path.isfile(htmlfilename):
        seqnumber = 2
        while os.path.isfile(os.path.join(DATA, 'dossier', "%s-%2.2d.html" % (filename,seqnumber))):
            seqnumber += 1
        basename     = "%s-%2.2d" % (filename,seqnumber)
        htmlfilename = os.path.join(DATA, 'dossier', "%s-%2.2d.html" % (filename,seqnumber))


    ## write out the project file & crude processing image for this batch of scans
    save = ''
    try:
        save = os.environ['DEMETER_FORCE_IFEFFIT'] # FIX ME!!!
    except:
        save = ''
    if save is None: save = ''
    os.environ['DEMETER_FORCE_IFEFFIT'] = '1' # FIX ME!!!
    try:
        ##########################################################################################
        # Hi Tom!  Yes, I am making a system call right here.  Again.  And to run a perl script, #
        # no less!  Are you having an aneurysm?  If so, please get someone to film it.  I'm      #
        # going to want to see that!  XOXO, Bruce                                                #
        ##########################################################################################
        print("/home/xf06bm/bin/toprj.pl --folder=%s --name=%s --base=%s --start=%d --end=%d --bounds=%s --mode=%s" %
              (DATA, filename, basename, int(start), int(end), bounds, mode))
        result = subprocess.run(['/home/xf06bm/bin/toprj.pl',
                                 "--folder=%s" % DATA,         # data folder
                                 "--name=%s"   % filename,     # file stub
                                 "--base=%s"   % basename,     # basename (without scan sequence numbering)		 
                                 "--start=%d"  % int(start),   # first suffix number					 
                                 "--end=%d"    % int(end),     # last suffix number					 
                                 "--bounds=%s" % bounds,       # scan boundaries (used to distinguish XANES from EXAFS)
                                 "--mode=%s"   % mode],        # measurement mode
                                stdout=subprocess.PIPE)
        png = open(os.path.join(DATA, 'snapshots', basename+'.png'), 'wb')
        png.write(result.stdout)
        png.close()
    except Exception as e:
        print(e)
    os.environ['DEMETER_FORCE_IFEFFIT'] = save # FIX ME!!!
    
    with open(os.path.join(DATA, inifile)) as f:
        initext = ''.join(f.readlines())
        
    o = open(htmlfilename, 'w')
    pdstext = '%s (%s)' % (get_mode(), describe_mode())
    o.write(''.join(content).format(filename      = filename,
                                    basename      = basename,
                                    encoded_basename = quote(basename),
                                    experimenters = experimenters,
                                    gup           = BMMuser.gup,
                                    saf           = BMMuser.saf,
                                    seqnumber     = seqnumber,
                                    seqstart      = seqstart,
                                    seqend        = seqend,
                                    mono          = 'Si(%s)' % dcm._crystal,
                                    pdsmode       = pdstext,
                                    e0            = '%.1f' % e0,
                                    edge          = edge,
                                    element       = '%s (<a href="https://en.wikipedia.org/wiki/%s">%s</a>, %d)' % (element, element_name(element), element_name(element), Z_number(element)),
                                    date          = BMMuser.date,
                                    scanlist      = scanlist,
                                    motors        = motors,
                                    sample        = sample,
                                    prep          = prep,
                                    comment       = comment,
                                    mode          = mode,
                                    pccenergy     = '%.1f' % pccenergy,
                                    bounds        = bounds,
                                    steps         = steps,
                                    times         = times,
                                    clargs        = highlight(clargs, PythonLexer(), HtmlFormatter()),
                                    websnap       = quote('../snapshots/'+websnap),
                                    anasnap       = quote('../snapshots/'+anasnap),
                                    initext       = highlight(initext, IniLexer(), HtmlFormatter()),
                                ))
    o.close()

    manifest = open(os.path.join(DATA, 'dossier', 'MANIFEST'), 'a')
    manifest.write(htmlfilename + '\n')
    manifest.close()

    write_manifest()
    return(htmlfilename)


import bluesky.preprocessors
from bluesky.preprocessors import subs_decorator
import pprint
pp = pprint.PrettyPrinter(indent=4)


def write_manifest():
    '''Update the scan manifest and the corresponding static html file.'''
    with open(os.path.join(DATA, 'dossier', 'MANIFEST')) as f:
        lines = [line.rstrip('\n') for line in f]

    experimentlist = ''
    for l in lines:
        if not os.path.isfile(l):
            continue
        experimentlist += '<li><a href="%s">%s</a></li>\n' % (l, os.path.basename(l))
        
    with open(os.path.join(DATA, 'dossier', 'manifest.tmpl')) as f:
        content = f.readlines()
    indexfile = os.path.join(DATA, 'dossier', '00INDEX.html')
    o = open(indexfile, 'w')
    o.write(''.join(content).format(date           = BMMuser.date,
                                    experimentlist = experimentlist,))
    o.close()
    


#########################
# -- the main XAFS scan #
#########################
def xafs(inifile, **kwargs):
    '''
    Read an INI file for scan matadata, then perform an XAFS scan sequence.
    '''
    def main_plan(inifile, **kwargs):
        if '311' in dcm._crystal and dcm_x.user_readback.value < 10:
            BMMuser.final_log_entry = False
            print(error_msg('The DCM is in the 111 position, configured as 311'))
            print(error_msg('\tdcm.x: %.2f mm\t dcm._crystal: %s' % (dcm_x.user_readback.value, dcm._crystal)))
            yield from null()
            return
        if '111' in dcm._crystal and dcm_x.user_readback.value > 10:
            BMMuser.final_log_entry = False
            print(error_msg('The DCM is in the 311 position, configured as 111'))
            print(error_msg('\tdcm_x: %.2f mm\t dcm._crystal: %s' % (dcm_x.user_readback.value, dcm._crystal)))
            yield from null()
            return

        
        verbose = False
        if 'verbose' in kwargs and kwargs['verbose'] is True:
            verbose = True
            
        supplied_metadata = dict()
        if 'md' in kwargs and type(kwargs['md']) == dict:
            supplied_metadata = kwargs['md']

        if verbose: print(verbosebold_msg('checking clear to start (unless force=True)')) 
        if 'force' in kwargs and kwargs['force'] is True:
            (ok, text) = (True, '')
        else:
            (ok, text) = BMM_clear_to_start()
            if ok is False:
                BMMuser.final_log_entry = False
                print(error_msg('\n'+text))
                print(bold_msg('Quitting scan sequence....\n'))
                yield from null()
                return

        ## make sure we are ready to scan
        #yield from abs_set(_locked_dwell_time.quadem_dwell_time.settle_time, 0)
        #yield from abs_set(_locked_dwell_time.struck_dwell_time.settle_time, 0)
        _locked_dwell_time.quadem_dwell_time.settle_time = 0
        _locked_dwell_time.struck_dwell_time.settle_time = 0


        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## user input, find and parse the INI file
        if verbose: print(verbosebold_msg('time estimate')) 
        inifile, estimate = howlong(inifile, interactive=False, **kwargs)
        if estimate == -1:
            BMMuser.final_log_entry = False
            yield from null()
            return
        (p, f) = scan_metadata(inifile=inifile, **kwargs)
        if not any(p):          # scan_metadata returned having printed an error message
            return(yield from null())

        if p['usbstick']:
            sub_dict = {'*' : '_STAR_',
                        '/' : '_SLASH_',
                        '\\': '_BACKSLASH_',
                        '?' : '_QM_',
                        '%' : '_PERCENT_',
                        ':' : '_COLON_',
                        '|' : '_VERBAR_',
                        '"' : '_QUOTE_',
                        '<' : '_LT_',
                        '>' : '_GT_',
                    }

            vfatify = lambda m: sub_dict[m.group()]
            new_filename = re.sub(r'[*:?"<>|/\\]', vfatify, p['filename'])
            if new_filename != p['filename']: 
                report('\nChanging filename from "%s" to %s"' % (p['filename'], new_filename), 'error')
                print(error_msg('\nThese characters cannot be in file names copied onto most memory sticks:'))
                print(error_msg('\n\t* : ? " < > | / \\'))
                print(error_msg('\nSee ')+url_msg('https://en.wikipedia.org/wiki/Filename#Reserved_characters_and_words'))
                p['filename'] = new_filename

            ## 255 character limit for filenames on VFAT
            # if len(p['filename']) > 250:
            #     BMMuser.final_log_entry = False
            #     print(error_msg('\nYour filename is too long,'))
            #     print(error_msg('\nFilenames longer than 255 characters cannot be copied onto most memory sticks,'))
            #     yield from null()
            #     return


        bail = False
        count = 0
        for i in range(p['start'], p['start']+p['nscans'], 1):
            count += 1
            fname = "%s.%3.3d" % (p['filename'], i)
            datafile = os.path.join(p['folder'], fname)
            if os.path.isfile(datafile):
                report('%s already exists!' % (datafile), 'error')
                bail = True
        if bail:
            report('\nOne or more output files already exist!  Quitting scan sequence....\n', 'error')
            BMMuser.final_log_entry = False
            yield from null()
            return

            
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## user verification (disabled by BMMuser.prompt)
        if verbose: print(verbosebold_msg('computing pseudo-channelcut energy')) 
        eave = channelcut_energy(p['e0'], p['bounds'], p['ththth'])
        length = 0
        if BMMuser.prompt:
            text = '\n'
            for k in ('bounds', 'bounds_given', 'steps', 'times'):
                addition = '      %-13s : %-50s\n' % (k,p[k])
                text = text + addition.rstrip() + '\n'
                if len(addition) > length: length = len(addition)
            for (k,v) in p.items():
                if k in ('bounds', 'bounds_given', 'steps', 'times'):
                    continue
                if k in ('npoints', 'dwell', 'delay', 'inttime', 'channelcut', 'bothways'):
                    continue
                addition = '      %-13s : %-50s\n' % (k,v)
                text = text + addition.rstrip() + '\n'
                if len(addition) > length: length = len(addition)
                if length < 75: length = 75
            boxedtext('How does this look?', text, 'green', width=length+4) # see 05-functions

            outfile = os.path.join(p['folder'], "%s.%3.3d" % (p['filename'], p['start']))
            print('\nFirst data file to be written to "%s"' % outfile)

            print(estimate)

            if not dcm.suppress_channel_cut:
                if p['ththth']:
                    print('\nSi(111) pseudo-channel-cut energy = %.1f ; %.1f on the Si(333)' % (eave,eave*3))
                else:
                    print('\nPseudo-channel-cut energy = %.1f' % eave)

            action = input("\nBegin scan sequence? [Y/n then Enter] ")
            if action.lower() == 'q' or action.lower() == 'n':
                BMMuser.final_log_entry = False
                yield from null()
                return

        
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## gather up input data into a fomat suitable for the dossier
        with open(inifile, 'r') as fd: content = fd.read()
        output = re.sub(r'\n+', '\n', re.sub(r'\#.*\n', '\n', content)) # remove comment and blank lines
        clargs = textwrap.fill(str(kwargs), width=50).replace('\n', '<br>')
        BMM_log_info('starting XAFS scan using %s:\n%s\ncommand line arguments = %s' % (inifile, output, str(kwargs)))
        BMM_log_info(motor_status())

        ## perhaps enter pseudo-channel-cut mode
        ## need to do this define defining the plotting lambda otherwise
        ## BlueSky gets confused about the plotting window
        if not dcm.suppress_channel_cut:
            report('entering pseudo-channel-cut mode at %.1f eV' % eave, 'bold')
            dcm.mode = 'fixed'
            yield from mv(dcm.energy, eave)
            if p['rockingcurve']:
                report('running rocking curve at pseudo-channel-cut energy %.1f eV' % eave, 'bold')
                yield from rocking_curve()
                RE.msg_hook = None
                close_last_plot()
            dcm.mode = 'channelcut'

        #legends = []
        #for i in range(p['start'], p['start']+p['nscans'], 1):
        #    legends.append("%s.%3.3d" % (p['filename'], i))
        
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## set up a plotting subscription, anonymous functions for plotting various forms of XAFS
        test  = lambda doc: (doc['data']['dcm_energy'], doc['data']['I0'])
        trans = lambda doc: (doc['data']['dcm_energy'], log(doc['data']['I0'] / doc['data']['It']))
        ref   = lambda doc: (doc['data']['dcm_energy'], log(doc['data']['It'] / doc['data']['Ir']))
        Yield = lambda doc: (doc['data']['dcm_energy'], -1*doc['data']['Iy'] / doc['data']['I0'])
        fluo  = lambda doc: (doc['data']['dcm_energy'], (doc['data'][BMMuser.dtc1] +
                                                         doc['data'][BMMuser.dtc2] +
                                                         doc['data'][BMMuser.dtc3] +
                                                         doc['data'][BMMuser.dtc4]) / doc['data']['I0'])
        if 'fluo'    in p['mode'] or 'flou' in p['mode']:
            plot =  DerivedPlot(fluo,  xlabel='energy (eV)', ylabel='absorption (fluorescence)',   title=p['filename'])
        elif 'trans' in p['mode']:
            plot =  DerivedPlot(trans, xlabel='energy (eV)', ylabel='absorption (transmission)',   title=p['filename'])
        elif 'ref'   in p['mode']:
            plot =  DerivedPlot(ref,   xlabel='energy (eV)', ylabel='absorption (reference)',      title=p['filename'])
        elif 'yield' in p['mode']:
            plot =  DerivedPlot(Yield, xlabel='energy (eV)', ylabel='absorption (electron yield)', title=p['filename'])
        elif 'test'  in p['mode']:
            plot =  DerivedPlot(test,  xlabel='energy (eV)', ylabel='I0 (test)',                   title=p['filename'])
        elif 'both'  in p['mode']:
            plot = [DerivedPlot(trans, xlabel='energy (eV)', ylabel='absorption (transmission)',   title=p['filename']),
                    DerivedPlot(fluo,  xlabel='energy (eV)', ylabel='absorption (fluorescence)',   title=p['filename'])]
        else:
            print(error_msg('Plotting mode not specified, falling back to a transmission plot'))
            plot =  DerivedPlot(trans, xlabel='energy (eV)', ylabel='absorption (transmission)',   title=p['filename'])


        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## engage suspenders right before starting scan sequence
        if 'force' in kwargs and kwargs['force'] is True:
            pass
        else:
            BMM_suspenders()
            
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## begin the scan sequence with the plotting subscription
        @subs_decorator(plot)
        def scan_sequence(clargs):
            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## compute energy and dwell grids
            print(bold_msg('computing energy and dwell time grids'))
            (energy_grid, time_grid, approx_time) = conventional_grid(p['bounds'], p['steps'], p['times'], e0=p['e0'], ththth=p['ththth'])
            if energy_grid is None or time_grid is None or approx_time is None:
                print(error_msg('Cannot interpret scan grid parameters!  Bailing out....'))
                BMMuser.final_log_entry = False
                yield from null()
                return
            if any(y > 23500 for y in energy_grid):
                print(error_msg('Your scan goes above 23500 eV, the maximum energy available at BMM.  Bailing out....'))
                BMMuser.final_log_entry = False
                yield from null()
                return
            if dcm._crystal == '111' and any(y > 21200 for y in energy_grid):
                print(error_msg('Your scan goes above 21200 eV, the maximum energy value on the Si(111) mono.  Bailing out....'))
                BMMuser.final_log_entry = False
                yield from null()
                return
            if dcm._crystal == '111' and any(y < 2900 for y in energy_grid): # IS THIS CORRECT???
                print(error_msg('Your scan goes below 2900 eV, the minimum energy value on the Si(111) mono.  Bailing out....'))
                BMMuser.final_log_entry = False
                yield from null()
                return
            if dcm._crystal == '311' and any(y < 5500 for y in energy_grid):
                print(error_msg('Your scan goes below 5500 eV, the minimum energy value on the Si(311) mono.  Bailing out....'))
                BMMuser.final_log_entry = False
                yield from null()
                return


            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## organize metadata for injection into database and XDI output
            print(bold_msg('gathering metadata'))
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
                              ththth        = p['ththth'],
            )

            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## show the metadata to the user
            display_XDI_metadata(md)
                
            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## this dictionary is used to populate the static html page for this scan sequence
            html_scan_list = ''
            html_dict['filename']      = p['filename']
            html_dict['experimenters'] = p['experimenters']
            html_dict['start']         = p['start']
            html_dict['end']           = p['start']+p['nscans']-1
            html_dict['seqstart']      = now('%A, %B %d, %Y %I:%M %p')
            html_dict['e0']            = p['e0']
            html_dict['element']       = p['element']
            html_dict['edge']          = p['edge']
            html_dict['motors']        = motor_sidebar()
            html_dict['sample']        = p['sample']
            html_dict['prep']          = p['prep']
            html_dict['comment']       = p['comment']
            html_dict['mode']          = p['mode']
            html_dict['pccenergy']     = eave
            html_dict['bounds']        = ' '.join(map(str, p['bounds_given'])) # see https://stackoverflow.com/a/5445983
            html_dict['steps']         = ' '.join(map(str, p['steps']))
            html_dict['times']         = ' '.join(map(str, p['times']))
            html_dict['clargs']        = clargs
            html_dict['htmlpage']      = p['htmlpage']
            html_dict['ththth']        = p['ththth']

            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## snap photos
            if p['snapshots']:
                ahora = now()

                html_dict['websnap'] = "%s_XASwebcam_%s.jpg" % (p['filename'], ahora)
                image = os.path.join(p['folder'], 'snapshots', html_dict['websnap'])
                annotation = 'NIST BMM (NSLS-II 06BM)      ' + p['filename'] + '      ' + ahora
                snap('XAS', filename=image, annotation=annotation)

                html_dict['anasnap'] = "%s_analog_%s.jpg" % (p['filename'], ahora)
                image = os.path.join(p['folder'], 'snapshots', html_dict['anasnap'])
                snap('analog', filename=image, sample=p['filename'])

            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## write dotfile, used by cadashboard
            with open(dotfile, "w") as f:
                f.write(str(datetime.datetime.timestamp(datetime.datetime.now())) + '\n')
                f.write('%.1f\n' % (approx_time * int(p['nscans']) * 60))
                
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
                    report('%s already exists! (How did that happen?) Bailing out....' % (datafile), 'error')
                    yield from null()
                    return
                print(bold_msg('starting scan %d of %d, %d energy points' % (count, p['nscans'], len(energy_grid))))
                md['_filename'] = fname
                
                ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
                ## compute trajectory
                energy_trajectory    = cycler(dcm.energy, energy_grid)
                dwelltime_trajectory = cycler(dwell_time, time_grid)

                ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
                ## need to set certain metadata items on a per-scan basis... temperatures, ring stats
                ## mono direction, ... things that can change during or between scan sequences
                
                md['Mono']['direction'] = 'forward'
                if p['bothways'] and count%2 == 0:
                    energy_trajectory    = cycler(dcm.energy, energy_grid[::-1])
                    dwelltime_trajectory = cycler(dwell_time, time_grid[::-1])
                    md['Mono']['direction'] = 'backward'
                else:
                    ## if not measuring in both direction, lower acceleration of the mono
                    ## for the rewind, explicitly rewind, then reset for measurement
                    yield from abs_set(dcm_bragg.acceleration, BMMuser.acc_slow, wait=True)
                    print(whisper('  Rewinding DCM to %.1f eV with acceleration time = %.2f sec' % (energy_grid[0], dcm_bragg.acceleration.value)))
                    yield from mv(dcm.energy, energy_grid[0])
                    yield from abs_set(dcm_bragg.acceleration, BMMuser.acc_fast, wait=True)
                    print(whisper('  Resetting DCM acceleration time to %.2f sec' % dcm_bragg.acceleration.value))
                    
                rightnow = metadata_at_this_moment() # see 62-metadata.py
                for family in rightnow.keys():       # transfer rightnow to md
                    if type(rightnow[family]) is dict:
                        if family not in md:
                            md[family] = dict()
                        for k in rightnow[family].keys():
                            md[family][k] = rightnow[family][k]
                
                md['_kind'] = 'xafs'
                if p['ththth']: md['_kind'] = '333'

                xdi = {'XDI': md}
                
                ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
                ## call the stock scan_nd plan with the correct detectors
                #if 'trans' in p['mode'] or 'ref' in p['mode'] or 'yield' in p['mode'] or 'test' in p['mode']:
                if any(md in p['mode'] for md in ('trans', 'ref', 'yield', 'test')):
                    yield from scan_nd([quadem1], energy_trajectory + dwelltime_trajectory,
                                       md={**xdi, **supplied_metadata})
                else:
                    yield from scan_nd([quadem1, vor], energy_trajectory + dwelltime_trajectory,
                                       md={**xdi, **supplied_metadata})
                header = db[-1]
                write_XDI(datafile, header)
                print(bold_msg('wrote %s' % datafile))
                BMM_log_info('energy scan finished, uid = %s, scan_id = %d\ndata file written to %s'
                             % (header.start['uid'], header.start['scan_id'], datafile))

                ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
                ## generate left sidebar text for the static html page for this scan sequence
                js_text = '<a href="javascript:void(0)" onclick="toggle_visibility(\'%s\');" title="This is the scan number for %s, click to show/hide its UID">#%d</a><div id="%s" style="display:none;"><small>%s</small></div>' \
                          % (fname, fname, header.start['scan_id'], fname, header.start['uid'])
                printedname = fname
                if len(p['filename']) > 11:
                    printedname = fname[0:6] + '&middot;&middot;&middot;' + fname[-5:]
                html_scan_list += '<li><a href="../%s" title="Click to see the text of %s">%s</a>&nbsp;&nbsp;&nbsp;&nbsp;%s</li>\n' \
                                  % (quote(fname), fname, printedname, js_text)
                html_dict['scanlist'] = html_scan_list


            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## finish up, close out
            html_dict['seqend'] = now('%A, %B %d, %Y %I:%M %p')
            print('Returning to fixed exit mode and returning DCM to %1.f' % eave)
            dcm.mode = 'fixed'
            yield from abs_set(dcm_bragg.acceleration, BMMuser.acc_slow, wait=True)
            yield from mv(dcm.energy, eave)
            yield from abs_set(dcm_bragg.acceleration, BMMuser.acc_fast, wait=True)

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## execute this scan sequence plan
        yield from scan_sequence(clargs)

    def cleanup_plan(inifile):
        print('Cleaning up after an XAFS scan sequence')
        RE.clear_suspenders()
        if os.path.isfile(dotfile):
            os.remove(dotfile)

        ## db[-1].stop['num_events']['primary'] should equal db[-1].start['num_points'] for a complete scan
        how = 'finished'
        if 'primary' not in db[-1].stop['num_events']:
            how = 'stopped'
        elif db[-1].stop['num_events']['primary'] != db[-1].start['num_points']:
            how = 'stopped'
        if BMMuser.final_log_entry is True:
            BMM_log_info('XAFS scan sequence %s\nmost recent uid = %s, scan_id = %d'
                         % (how, db[-1].start['uid'], db[-1].start['scan_id']))
            if 'htmlpage' in html_dict and html_dict['htmlpage']:
                htmlout = scan_sequence_static_html(inifile=inifile, **html_dict)
                if htmlout is not None:
                    report('wrote dossier %s' % htmlout, 'bold')
        #else:
        #    BMM_log_info('XAFS scan sequence finished early')
        dcm.mode = 'fixed'
        yield from resting_state_plan()
        yield from bps.sleep(2.0)
        yield from abs_set(dcm_pitch.kill_cmd, 1)
        yield from abs_set(dcm_roll.kill_cmd, 1)

    dotfile = '/home/xf06bm/Data/.xafs.scan.running'
    html_scan_list = ''
    html_dict = {}
    BMMuser.final_log_entry = True
    RE.msg_hook = None
    ## encapsulation!
    yield from bluesky.preprocessors.finalize_wrapper(main_plan(inifile, **kwargs), cleanup_plan(inifile))
    RE.msg_hook = BMM_msg_hook


def howlong(inifile, interactive=True, **kwargs):
    ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
    ## user input, find and parse the INI file
    ## try inifile as given then DATA + inifile
    ## this allows something like RE(xafs('myscan.ini')) -- short 'n' sweet
    orig = inifile
    if not os.path.isfile(inifile):
        inifile = os.path.join(DATA, inifile)
        if not os.path.isfile(inifile):
            print(warning_msg('\n%s does not exist!  Bailing out....\n' % orig))
            return(orig, -1)
    print(bold_msg('reading ini file: %s' % inifile))
    (p, f) = scan_metadata(inifile=inifile, **kwargs)
    if not p:
        print(error_msg('%s could not be read as an XAFS control file\n' % inifile))
        return(orig, -1)
    (ok, missing) = ini_sanity(f)
    if not ok:
        print(error_msg('\nThe following keywords are missing from your INI file: '), '%s\n' % str.join(', ', missing))
        return(orig, -1)
    (energy_grid, time_grid, approx_time) = conventional_grid(p['bounds'], p['steps'], p['times'], e0=p['e0'], ththth=p['ththth'])
    text = 'One scan of %d points will take about %.1f minutes\n' % (len(energy_grid), approx_time)
    text +='The sequence of %s will take about %s' % (inflect('scan', p['nscans']),
                                                    inflect('hour', int(approx_time * int(p['nscans'])/60)))
    if interactive:
        print(text)
    else:
        return(inifile, text)


    
