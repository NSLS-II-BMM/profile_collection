
from bluesky.plan_stubs import sleep, mv, mvr, null

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from lmfit.models import StepModel

import numpy
from sympy import geometry

from BMM.linescans   import linescan
from BMM.derivedplot import close_all_plots, close_last_plot
from BMM.functions   import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.resting_state import resting_state_plan

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)


class Wafer():
    points = []
    center = []
    diameter = 0
    
    def clear(self):
        self.points = []
    
    def push(self):
        xafs_x, xafs_y = user_ns['xafs_x'], user_ns['xafs_y']
        self.points.append([xafs_x.position, xafs_y.position])

    def find_center(self):
        tri = geometry.Triangle(*self.points)
        self.center = numpy.array(tri.circumcenter, dtype=float)
        self.diameter= numpy.array(tri.circumradius, dtype=float)*2
        print(f'The center is at {self.center}.   The diameter is {self.diameter}.')

    def goto_center(self):
        xafs_x, xafs_y = user_ns['xafs_x'], user_ns['xafs_y']
        yield from (mv(xafs_x, self.center[0], xafs_y, self.center[1]))
        
    def edge(self, motor='x'):
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
