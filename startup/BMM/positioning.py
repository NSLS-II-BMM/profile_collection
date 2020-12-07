
from bluesky.plans import rel_scan
from bluesky.plan_stubs import abs_set, sleep, mv, null

from IPython import get_ipython
user_ns = get_ipython().user_ns

from BMM.functions     import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.linescans     import linescan

def find_slot(margin=0.5, force=False):
    '''Thin wrapper around repeated calls to linescan in order to align a
    sample wheel slot in the beam. This will perform a linescan in
    xafs_x over the range of -10 to 10 or in xafs_y from -3 to 3
    (which are suitable ranges for the size of the slot).  User is
    prompted to scan in X or Y, or to quit the loop.  The loop will
    return after 6 scans -- 3 iterations is certainly enough for this
    task.

    The high limit in xafs_x will be set to 500 microns above the
    selected position.

    Parameters
    ==========

    margin : float
        margin for setting the high limit of an axis.
    force : bool
        passed along to linescans, flag for forcing a scan even if 
        not clear to start

    '''
    xafs_x, xafs_y = user_ns['xafs_x'], user_ns['xafs_y']
    count = 1
    while True:
        action = input(bold_msg("\nScan axis? [x=xafs_x / y=xafs_y / q=quit] (then Enter) "))
        if action.lower() == 'q' or action.lower() == 'n':
            yield from null()
            close_all_plots()
            return
        if action.lower() == 'x':
            yield from mv(xafs_x.hlm, xafs_x.default_hlm)
            yield from linescan(xafs_x, 'it', -10, 10, 31, force=force)
            yield from mv(xafs_x.hlm, xafs_x.position+margin)
        if action.lower() == 'y':
            yield from linescan(xafs_y, 'it', -3, 3, 31, force=force)
        count += 1
        if count > 5:
            print('Three iterations is plenty....')
            close_all_plots()
            return
