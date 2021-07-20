
from bluesky.plans import rel_scan
from bluesky.plan_stubs import abs_set, sleep, mv, null

import matplotlib.pyplot as plt
from lmfit.models import StepModel
import numpy

from IPython import get_ipython
from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

from BMM.derivedplot   import close_all_plots, close_last_plot
from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.linescans     import linescan

def find_slot(xmargin=0.5, ymargin=2, force=False):
    '''Thin wrapper around repeated calls to linescan in order to align a
    sample wheel slot in the beam. This will perform a linescan in
    xafs_x over the range of -10 to 10 or in xafs_y from -3 to 3
    (which are suitable ranges for the size of the slot).  User is
    prompted to scan in X or Y, or to quit the loop.  The loop will
    return after 6 scans -- 3 iterations is certainly enough for this
    task.

    In bsui terms, this is a wrapper around these command:

       linescan(xafs_x, 'it', -10, 10, 31)

    and 

       linescan(xafs_y, 'it', -3, 3, 31)

    which are suitable linescans for aligning the sample wheel once it
    has been aligned roughly by hand.

    The high limit in xafs_x will be set to 500 microns (the default)
    above the selected position.  The margin cannot be less than 50
    microns.  The low limit in xafs_x is presumed not to be important.

    The high limit in xafs_y will be set to 2 mm (the default) above
    the selected position.  The low limit in xafs_y will be set to 2
    mm (the default) below the selected position.  The margin cannot
    be less than 50 microns.

    Parameters
    ==========

    xmargin : float
        margin for setting the high limit of the xafs_x axis, 
        default=0.5, minimum=0.05
    ymargin : float
        margin for setting the high limit of the xafs_y axis, 
        default=2, minimum=0.05
    force : bool
        passed along to linescan(), flag for forcing a scan even if 
        not clear to start

    '''
    xafs_x, xafs_y = user_ns['xafs_x'], user_ns['xafs_y']
    count = 1
    if xmargin < 0.05:
        xmargin = 0.05
    if ymargin < 0.05:
        ymargin = 0.05
    while True:
        action = input(bold_msg("\nScan axis? [x=xafs_x / y=xafs_y / q=quit] (then Enter) "))
        if action[:1].lower() == 'x':
            yield from mv(xafs_x.hlm, xafs_x.default_hlm)
            yield from linescan(xafs_x, 'it', -10, 10, 31, force=force)
            yield from mv(xafs_x.hlm, xafs_x.position+xmargin)
        elif action[:1].lower() == 'y':
            yield from mv(xafs_y.hlm, xafs_y.default_hlm, xafs_y.llm, xafs_y.default_llm)
            yield from linescan(xafs_y, 'it', -3, 3, 31, force=force)
            yield from mv(xafs_y.hlm, xafs_y.position+ymargin, xafs_y.llm, xafs_y.position-ymargin)
        elif action[:1].lower() in ('q', 'n', 'c'): # quit/no/cancel
            yield from null()
            close_all_plots()
            return
        else:
            continue
        count += 1
        if count > 6:
            print('Three iterations is plenty....')
            close_all_plots()
            return


def align_ga(ymargin=0.5, force=False):
    '''Thin wrapper around repeated calls to linescan in order to align 
    the glancing angle stage in the beam. This will perform a linescan in
    xafs_pitch over the range of -2 to 2 or in xafs_y from -1 to 1
    (which are suitable ranges for the size of the slot).  User is
    prompted to scan in pitch or Y, or to quit the loop.  The loop will
    return after 6 scans -- 3 iterations is certainly enough for this
    task.

    In bsui terms, this is a wrapper around these command:

       linescan(xafs_y, 'it', -1, 1, 31)

    and 

       linescan(xafs_pitch, 'it', -2, 2, 31)

    which are suitable linescans for aligning the glancing angle stage
    once it has been aligned roughly by hand.

    The high limit in xafs_y will be set to 0.5 mm (the default) above
    the selected position.  The low limit in xafs_y will be set to 0.5
    mm (the default) below the selected position.  The margin cannot
    be less than 50 microns.

    Parameters
    ==========

    ymargin : float
        margin for setting the high limit of the xafs_y axis, 
        default=2, minimum=0.05
    force : bool
        passed along to linescan(), flag for forcing a scan even if 
        not clear to start

    '''
    xafs_pitch, xafs_y = user_ns['xafs_pitch'], user_ns['xafs_y']
    db = user_ns['db']
    count = 1
    if ymargin < 0.05:
        ymargin = 0.05
    while True:
        action = input(bold_msg("\nScan axis? [p=xafs_pitch / y=xafs_y / q=quit] (then Enter) "))
        if action[:1].lower() == 'p':
            yield from linescan(xafs_pitch, 'it', -3, 3, 31, force=force)
        elif action[:1].lower() == 'y':
            yield from mv(xafs_y.hlm, xafs_y.default_hlm, xafs_y.llm, xafs_y.default_llm)
            yield from linescan(xafs_y, 'it', -2, 2, 31, force=force)
            #yield from mv(xafs_y.hlm, xafs_y.position+ymargin, xafs_y.llm, xafs_y.position-ymargin)
        elif action[:1].lower() in ('q', 'n', 'c'): # quit/no/cancel
            yield from null()
            close_all_plots()
            return
        else:
            continue
        count += 1
        if count > 6:
            print('Three iterations is plenty....')
            close_all_plots()
            return

    
