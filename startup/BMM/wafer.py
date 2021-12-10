
from bluesky.plan_stubs import sleep, mv, mvr, null

import numpy
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from lmfit.models import StepModel

from BMM.linescans   import linescan
from BMM.derivedplot import close_all_plots, close_last_plot
from BMM.functions   import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.resting_state import resting_state_plan

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

def wafer_edge(motor='x'):
    '''Fit an error function to the linear scan against It. Plot the
    result. Move to the centroid of the error function.'''
    if motor == 'x':
        motor = user_ns['xafs_linx']
    else:
        motor = user_ns['xafs_liny']
    yield from linescan(motor, 'it', -2, 2, 41, pluck=False)
    close_last_plot()
    table  = user_ns['db'][-1].table()
    yy     = table[motor.name]
    signal = table['It']/table['I0']
    if float(signal[2]) > list(signal)[-2] :
        ss     = -(signal - signal[2])
    else:
        ss     = signal - signal[2]
    mod    = StepModel(form='erf')
    pars   = mod.guess(ss, x=numpy.array(yy))
    out    = mod.fit(ss, pars, x=numpy.array(yy))
    print(whisper(out.fit_report(min_correl=0)))
    out.plot()
    target = out.params['center'].value
    yield from mv(motor, target)
    yield from resting_state_plan()
    print(f'Edge found at X={user_ns["xafs_x"].position} and Y={user_ns["xafs_y"].position}')
