
from bluesky.plans import rel_scan
from bluesky.plan_stubs import abs_set, sleep, mv, mvr, null
from bluesky import __version__ as bluesky_version
import numpy
import os
import time

#from bluesky.preprocessors import subs_decorator
## see 65-derivedplot.py for DerivedPlot class
## see 10-motors.py and 20-dcm.py for motor definitions

from bluesky_queueserver.manager.profile_tools import set_user_ns

## from IPython import get_ipython
## user_ns = get_ipython().user_ns

from BMM.resting_state import resting_state_plan
from BMM.suspenders    import BMM_clear_to_start
from BMM.logging       import BMM_log_info, BMM_msg_hook
from BMM.functions     import countdown, now
from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper


@set_user_ns
def energystep(filename = None,
               start    = None,
               end      = None,
               nsteps   = None,
               delay    = 5,
               dosteps  = True,
               user_ns  = None):
    '''A simple energy scan, just step forward in energy and don't measure
    anything.  This is a quick hack for use with a crude resonant
    reflectivity experiment with IBM folks.

    Parameters
    ----------
    filename : str
        name of file, will be appended to DATA for the full path (required)
    start : float
        starting energy value (required)
    end : float
        ending energy value (required)
    nsteps : int
        number of energy steps (required)
    delay : float
        pause between energy steps, in seconds [5]
    dosteps : bool
        False to see energy values printed to screen without moving mono [True]

    Writes a data file with columns of energy readback, energy
    requested, time of epoch, and ISO 8601 timestamp

    Example
    -------

    >>> energystep(filename='blahblah', start=18936, end=19036, nsteps=101)
    '''

    BMMuser, dcm = user_ns['BMMuser'], user_ns['dcm']
    BMM_log_info("energystep(filename=%s, start=%.1f, end=%.1f, nsteps=%d, delay=%.1f, dosteps=%s)" % (filename, start, end, nsteps, delay, str(dosteps)))
    datafile = BMMuser.DATA + filename
    handle = open(datafile, 'w')
    handle.write('# energy steps from %.1f to %.1f in %d steps\n' % (start, end, nsteps))
    handle.write('#----------------------------------------------------\n')
    handle.write('# energy        requested          epoch        iso8601\n')
    handle.flush()
    
    if dosteps:
        yield from mv(dcm.energy, start)
    print('  %.1f       %.1f     %.6f    %s' % (dcm.energy.readback.get(), start, time.time(), now()))
    handle.write('  %.1f       %.1f     %.6f    %s\n' % (dcm.energy.readback.get(), start, time.time(), now()))
    handle.flush()
    yield from sleep(delay)

    energy = start
    estep = (end-start) / nsteps
    while energy <= end:
        if dosteps:
            yield from mvr(dcm.energy, estep)
        print('  %.1f       %.1f     %.6f    %s' % (dcm.energy.readback.get(), energy, time.time(), now()))
        handle.write('  %.1f       %.1f     %.6f    %s\n' % (dcm.energy.readback.get(), energy, time.time(), now()))
        handle.flush()
        energy = energy + estep
        yield from sleep(delay)
        

    handle.flush()
    handle.close()
    
