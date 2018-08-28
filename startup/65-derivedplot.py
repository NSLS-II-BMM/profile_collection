from collections import ChainMap
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from cycler import cycler
import numpy as np
import warnings
from numpy import log

from bluesky.callbacks import CallbackBase

run_report(__file__)


## ---- need to do this in the bluesky way -- gives a sensible (non-integer) display of I0/It/Ir in LiveTable:
# caput XF:06BM-BI{EM:1}EM180:Current1:MeanValue_RBV.PREC 5
# caput XF:06BM-BI{EM:1}EM180:Current2:MeanValue_RBV.PREC 5
# caput XF:06BM-BI{EM:1}EM180:Current3:MeanValue_RBV.PREC 5

#####################################################################
# this is used to keep track of mouse events on the plotting window #
# see 70-linescans.py                                               #
#####################################################################
class CurrentPlotLogistics():
    def __init__(self):
        self.motor  = None
        self.motor2 = None
        self.fig    = None
        self.ax     = None
        self.x      = None
        self.y      = None
BMM_cpl = CurrentPlotLogistics()

#############################################################################
# this is the callback that gets assigned to mouse clicks on theplot window #
#############################################################################
def interpret_click(ev):
    print('You clicked on x=%.3f, y=%.3f' % (ev.xdata, ev.ydata))
    BMM_cpl.x = ev.xdata
    BMM_cpl.y = ev.ydata

def handle_close(ev):
    ## if closing a stale plot, take care to preserve current plot in BMM_cpl object
    if BMM_cpl.fig is None:
        return
    recent  = str(BMM_cpl.fig.canvas.__repr__).split()[-1]
    closing = str(ev.canvas).split()[-1]
    if recent == closing:
        BMM_cpl.motor  = None
        BMM_cpl.motor2 = None
        BMM_cpl.fig    = None
        BMM_cpl.ax     = None

class DerivedPlot(CallbackBase):
    def __init__(self, func, ax=None, xlabel=None, ylabel=None, legend_keys=None, **kwargs):
        """
        func expects an Event document which looks like this:
        {'time': <UNIX epoch>,
         'seq_num': integer starting from 1 (!),
         'data': {...},
         'timestamps': {...},  # has same keys as data, always
         'filled': {}  # only important if you have big array data
        }
        and should return (x, y)
        """
        super().__init__()
        self.func = func
        if ax is None:
            fig, ax = plt.subplots()
        self.ax = ax
        BMM_cpl.ax = ax
        BMM_cpl.fig = fig
        BMM_cpl.fig.canvas.mpl_connect('close_event', handle_close)
        if xlabel is None:
            xlabel = ''
        if ylabel is None:
            ylabel = ''
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)

        if legend_keys is None:
            legend_keys = []
        self.legend_keys = ['scan_id'] + legend_keys
        self.ax.margins(.1)
        self.kwargs = kwargs
        self.lines = []
        self.legend = None
        self.legend_title = " :: ".join([name for name in self.legend_keys])

    def start(self, doc):
        # The doc is not used; we just use the signal that a new run began.
        self.x_data, self.y_data = [], []
        label = " :: ".join(
            [str(doc.get(name, name)) for name in self.legend_keys])
        kwargs = ChainMap(self.kwargs, {'label': label})
        self.current_line, = self.ax.plot([], [], **kwargs)
        self.lines.append(self.current_line)
        self.legend = self.ax.legend(
            loc=0, title=self.legend_title).draggable()
        super().start(doc)

    def event(self, doc):
        x, y = self.func(doc)
        self.y_data.append(y)
        self.x_data.append(x)
        self.current_line.set_data(self.x_data, self.y_data)
        # Rescale and redraw.
        self.ax.relim(visible_only=True)
        self.ax.autoscale_view(tight=True)
        self.ax.figure.canvas.draw_idle()

    def stop(self, doc):
        super().stop(doc)
