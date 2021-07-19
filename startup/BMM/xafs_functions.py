
from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.functions     import countdown, boxedtext, now, isfloat, inflect, e2l, etok, ktoe
import numpy

try:
    from bluesky_queueserver.manager.profile_tools import set_user_ns
except ModuleNotFoundError:
    from ._set_user_ns import set_user_ns

# from IPython import get_ipython
# user_ns = get_ipython().user_ns

CS_BOUNDS     = [-200, -30, 15.3, '14k']
CS_STEPS      = [10, 0.5, '0.05k']
CS_TIMES      = [0.5, 0.5, '0.25k']
CS_MULTIPLIER = 0.72


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
        elif isfloat(s) and float(s) <= 0.09:
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
    


@set_user_ns
def conventional_grid(bounds=CS_BOUNDS, steps=CS_STEPS, times=CS_TIMES, e0=7112,
                      element=None, edge=None, ththth=False, *, user_ns):
    '''
    Parameters
    ----------
    bounds : list of float or str
        N relative energy values denoting the region boundaries of the step scan
    steps : list of float or str
        N-1 energy step sizes
    times : list of float or str
        N-1 integration time values
    e0 : float
        edge energy, reference for boundary values
    ththth : Boolean
        using the Si(333) reflection

    Output
    ------
    grid : list
        absolute energy values
    timegrid : list
        integration times
    approximate_time : float
        a very crude estimate of how long in minutes the scan will take
    delta : float
        uncertainty in execution time (if available)

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

    Examples
    --------
    this is the default (same as (g,it,at) = conventional_grid()):

    >>> (grid, inttime, time) = conventional_grid(bounds=[-200, -30, 15.3, '14k'],
    >>>                                           steps=[10, 0.5, '0.05k'],
    >>>                                           times=[0.5, 0.5, '0.25k'], e0=7112)

    more regions

    >>> (grid, inttime, time) = conventional_grid(bounds=[-200.0, -20.0, 30.0, '5k', '14.5k'],
    >>>                                           steps=[10.0, 0.5, 2, '0.05k'],
    >>>                                           times=[1, 1, 1, '1k'], e0=7112)

    many regions, energy boundaries, k-steps

    >>> (grid, inttime, time) = conventional_grid(bounds=[-200, -30, -10, 15, 100, 300, 500, 700, 900],
    >>>                                           steps=[10, 2, 0.5, '0.05k', '0.05k', '0.05k', '0.05k', '0.05k'],
    >>>                                           times=[0.5, 0.5, 0.5, 1, 2, 3, 4, 5], e0=7112)

    a one-region xanes scan

    >>> (grid, inttime, time) = conventional_grid(bounds=[-10, 40],
    >>>                                           steps=[0.25,],
    >>>                                           times=[0.5,], e0=7112)
    '''
    tele = user_ns['tele']
    
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
        bounds = list(numpy.array(bounds)/3)
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

    if element is not None:
        overhead, uncertainty = tele.overhead_per_point(element, edge)
    else:
        overhead = tele.interpolate(e0)
        
    approximate_time = (sum(timegrid) + float(len(timegrid))*overhead) / 60.0
    delta = float(len(timegrid))*uncertainty / 60.0
    return (grid, timegrid, round(approximate_time, 1), round(delta, 1))

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

