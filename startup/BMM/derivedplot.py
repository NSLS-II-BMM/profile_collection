from collections import ChainMap
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from cycler import cycler
import numpy as np
import warnings
from numpy import log
import threading

#from bluesky.callbacks import CallbackBase
from bluesky.callbacks.mpl_plotting import QtAwareCallback, initialize_qt_teleporter

from IPython import get_ipython
from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)


## ---- need to do this in the bluesky way -- gives a sensible (non-integer) display of I0/It/Ir in LiveTable:
# caput XF:06BM-BI{EM:1}EM180:Current1:MeanValue_RBV.PREC 5
# caput XF:06BM-BI{EM:1}EM180:Current2:MeanValue_RBV.PREC 5
# caput XF:06BM-BI{EM:1}EM180:Current3:MeanValue_RBV.PREC 5

#############################################################################
# this is the callback that gets assigned to mouse clicks on theplot window #
#############################################################################
def interpret_click(ev):
    BMMuser = user_ns['BMMuser']
    print('You clicked on x=%.3f, y=%.3f' % (ev.xdata, ev.ydata))
    BMMuser.x = ev.xdata
    BMMuser.y = ev.ydata

def handle_close(ev):
    ## if closing a stale plot, take care to preserve current plot in BMMuser object
    BMMuser = user_ns['BMMuser']    
    if BMMuser.fig is None:
        return
    recent  = str(BMMuser.fig.canvas.__repr__).split()[-1]
    closing = str(ev.canvas).split()[-1]
    if recent == closing:
        BMMuser.motor  = None
        BMMuser.motor2 = None
        BMMuser.fig    = None
        BMMuser.ax     = None

def close_last_plot():
    '''Close the most recent plot on screen'''
    BMMuser = user_ns['BMMuser']    
    if BMMuser.fig is None:
        #print('Oops... No last plot.')
        return
    if BMMuser.prev_fig is not None:
        plt.close(BMMuser.prev_fig)
        #if BMMuser.prev_fig in BMMuser.all_figs:
        #    BMMuser.all_figs.remove(BMMuser.prev_fig)
    plt.close(BMMuser.fig)
    #if BMMuser.fig in BMMuser.all_figs:
    #    BMMuser.all_figs.remove(BMMuser.fig)

def close_all_plots():
    '''Close all plots on screen'''
    BMMuser = user_ns['BMMuser']    
    plt.close('all')
    #for fig in BMMuser.all_figs:
    #    plt.close(fig)
    #BMMuser.all_figs = []
    BMMuser.motor    = None
    BMMuser.motor2   = None
    BMMuser.fig      = None
    BMMuser.ax       = None


initialize_qt_teleporter()
#class DerivedPlot(CallbackBase):
class DerivedPlot(QtAwareCallback):
    def __init__(self, func, ax=None, xlabel=None, ylabel=None, title=None, legend_keys=None, stream_name='primary', **kwargs):
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
        self.__setup_lock = threading.Lock()
        self.__setup_event = threading.Event()
        def setup():
            nonlocal func, ax, xlabel, ylabel, title, legend_keys, stream_name, kwargs
            BMMuser = user_ns['BMMuser']    
            with self.__setup_lock:
                if self.__setup_event.is_set():
                    return
                self.__setup_event.set()
            self.func = func
            if ax is None:
                fig, ax = plt.subplots()
            self.ax = ax
            if BMMuser.fig is not None:
                BMMuser.prev_fig = BMMuser.fig
            if BMMuser.ax is not None:
                BMMuser.prev_ax  = BMMuser.ax
            BMMuser.ax = ax
            BMMuser.fig = fig
            #BMMuser.all_figs.append(fig)
            BMMuser.fig.canvas.mpl_connect('close_event', handle_close)
            if xlabel is None:
                xlabel = ''
            if ylabel is None:
                ylabel = ''
            self.ax.set_xlabel(xlabel)
            self.ax.set_ylabel(ylabel)
            if title is not None:
                plt.title(title)

            if legend_keys is None:
                legend_keys = []
            self.legend_keys = ['scan_id'] + legend_keys
            self.ax.margins(.1)
            self.kwargs = kwargs
            self.lines = []
            self.legend = None
            self.legend_title = " :: ".join([name for name in self.legend_keys])
            self.stream_name = stream_name
            self.descriptors = {}
        self.__setup = setup

    def start(self, doc):
        self.__setup()
        # The doc is not used; we just use the signal that a new run began.
        self.x_data, self.y_data = [], []
        self.descriptors.clear()
        label = " :: ".join(
            [str(doc.get(name, name)) for name in self.legend_keys])
        kwargs = ChainMap(self.kwargs, {'label': label})
        self.current_line, = self.ax.plot([], [], **kwargs)
        self.lines.append(self.current_line)
        self.legend = self.ax.legend(
            loc=0, title=self.legend_title).set_draggable(True)
        super().start(doc)
        
    def descriptor(self, doc):
        if doc['name'] == self.stream_name:
            self.descriptors[doc['uid']] = doc

    def event(self, doc):
        if not doc['descriptor'] in self.descriptors:
            # This is from some other event stream and we should ignore it.
            return
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
