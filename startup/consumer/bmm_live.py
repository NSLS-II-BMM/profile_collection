import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_multitab import MplTabs
import numpy

#from nslsii.kafka_utils import _read_bluesky_kafka_config_file
#from bluesky_kafka.produce import BasicProducer
import pprint

import redis
rkvs = redis.Redis(host='xf06bm-ioc2', port=6379, db=0)

from slack import img_to_slack

class LineScan():
    '''Manage the live plot for a motor scan or a time scan.

    Before yielding from the basic scan type, issue a kafka document
    indicating the start of the scan.  This document will look
    something like this:

      {'linescan' : 'start', ... }

    where the ... elides the various arguments used to construct the
    desired plot.

    Every time an event document from BlueSky is observed, call the
    add method, which will parse the event document, extract the
    latest data point, add it correctly to the data arrays, and redraw
    the plot.

    After the basic scan finishes, issue a kafka document indicating
    the end of the scan.  This document will look
    something like this:

      {'linescan' : 'end',}

    This is a single scan plot.  Over plotting of successive scans is
    not currently supported.

    This works for time scans as well as motor scans.  Those two scan
    types plot the same sorts of signals on the y-axis.  If the
    "motor" attribute is None, then a time scan (with time in seconds
    on the x-axis) will be displayed.

    attributes
    ==========
    ongoing (bool)
      a flag indicating whether a line or time scan is in progress

    xdata (list)
      a list containing all x-axis values measured thus far

    ydata (list)
      a list containing all y-axis values measured thus far

    motor (str)
      the name of the motor in motion or None for a time scan

    numerator (str)
      the name of the detector being plotted, something like io, it,
      ir, if, xs, xs1 ...

    denominator (str or int)
      the name of the signal used to normalize the numerator
      signal. for most plots, this would be "i0", for a plot of the
      reference detector, this would be 'it'. For an plot of a signal
      without a normalization signal (I0) for example, this should be
      1.

    figure (mpl figure object)
      this will hold the reference to the active figure object

    axes (mpl axis object)
      this will hold the reference to the active axis object

    line (mpl line object)
      this will hold the reference to the active line object

    description (str)
      a generated string used in the figure title

    xs1, xs2, xs3, xs4, xs8 (strs)
      strings identifying the names of the fluorescence ROIs for the
      current state of the photon delivery system.  these will be
      fetched from redis.

    plots (list)
      a list of the matplotlib figure objects still on screen

    initial (float)
      the time in epoch seconds of the first point of a time scan

    '''
    ongoing     = False
    xdata       = []
    ydata       = []
    motor       = None
    numerator   = None
    denominator = 1
    figure      = None
    axes        = None
    line        = None
    description = None
    xs1, xs2, xs3, xs4, xs8 = None, None, None, None, None
    plots       = []
    initial     = 0
    
    def start(self, **kwargs):
        #if self.figure is not None:
        #    plt.close(self.figure.number)
        self.ongoing = True
        self.xdata = []
        self.ydata = []
        if 'motor' in kwargs: self.motor = kwargs['motor']
        self.numerator = kwargs['detector']
        self.denominator = None
        self.figure = plt.figure()
        if self.motor is not None:
            cid = self.figure.canvas.mpl_connect('button_press_event', self.interpret_click)
            #cid = BMMuser.fig.canvas.mpl_disconnect(cid)
        
        self.plots.append(self.figure.number)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_facecolor((0.95, 0.95, 0.95))
        self.line, = self.axes.plot([],[])
        self.initial = 0

        self.xs1 = rkvs.get('BMM:user:xs1').decode('utf-8')
        self.xs2 = rkvs.get('BMM:user:xs2').decode('utf-8')
        self.xs3 = rkvs.get('BMM:user:xs3').decode('utf-8')
        self.xs4 = rkvs.get('BMM:user:xs4').decode('utf-8')
        self.xs8 = rkvs.get('BMM:user:xs8').decode('utf-8')


        ## todo:  bicron, new ion chambers, both
        
        ## transmission: plot It/I0
        if self.numerator in ('It', 'Transmission'):
            self.numerator = 'It'
            self.description = 'transmission'
            self.denominator = 'I0'
            self.axes.set_ylabel(f'{self.numerator}/{self.denominator}')

        ## I0: plot just I0
        elif self.numerator == 'I0':
            self.description = 'I0'
            self.denominator = None
            self.axes.set_ylabel(self.numerator)

        ## reference: plot just Ir
        elif self.numerator == 'Ir':
            self.description = 'reference'
            self.denominator = None
            self.axes.set_ylabel(self.numerator)

        ## yield: plot Iy/I0
        elif self.numerator == 'Iy':
            self.description = 'yield'
            self.denominator = 'I0'
            self.axes.set_ylabel(f'{self.numerator}/{self.denominator}')

        ## fluorescence (4 channel): plot sum(If)/I0
        ##xs1, xs2, xs3, xs4 = rkvs.get('BMM:user:xs1'), rkvs.get('BMM:user:xs2'), rkvs.get('BMM:user:xs3'), rkvs.get('BMM:user:xs4')
        elif self.numerator in ('If', 'Xs', 'Fluorescence'):
            self.numerator = 'If'
            self.description = 'fluorescence (4 channel)'
            self.denominator = 'I0'
            self.axes.set_ylabel('fluorescence (4 channel)')

        ## fluorescence (1 channel): plot If/I0
        ##xs8 = rkvs.get('BMM:user:xs8').decode('utf-8')
        elif self.numerator == 'Xs1':
            self.description = 'fluorescence (1 channel)'
            self.denominator = 'I0'
            self.axes.set_ylabel('fluorescence (1 channel)')
            
        if 'motor' in kwargs:
            self.axes.set_xlabel(self.motor)
            self.axes.set_title(f'{self.description} vs. {self.motor}')
        else:                   # this is a time scan
            self.axes.set_xlabel('time (seconds)')
            self.axes.set_title(f'{self.description} vs. time')


    def interpret_click(self, ev):
        '''Grab location of mouse click.  Identify motor by grabbing the
        x-axis label from the canvas clicked upon.

        Stash those in Redis.
        '''
        x,y = ev.xdata, ev.ydata
        #print(x, ev.canvas.figure.axes[0].get_xlabel(), ev.canvas.figure.number)
        rkvs.set('BMM:mouse_event:value', x)
        rkvs.set('BMM:mouse_event:motor', ev.canvas.figure.axes[0].get_xlabel())
        

        
        # kafka_config = _read_bluesky_kafka_config_file(config_file_path="/etc/bluesky/kafka.yml")
        # producer = BasicProducer(bootstrap_servers=kafka_config['bootstrap_servers'],
        #                          topic='bmm.test',
        #                          producer_config=kafka_config["runengine_producer_config"],
        #                          key='abcdef')
        # document = {'mpl_event' : 'mouse_click',
        #             'motor' : self.motor,
        #             'position' : ev.xdata, }
        # pprint.pprint(documemnt)
        # producer.produce(['bmm', document])

        
    def stop(self, **kwargs):
        if 'fname' in kwargs:
            self.figure.savefig(kwargs['fname'])
            img_to_slack(kwargs['fname'])
            
        self.ongoing     = False
        self.xdata       = []
        self.ydata       = []
        self.motor       = None
        self.numerator   = None
        self.denominator = 1
        self.figure      = None
        self.axes        = None
        self.line        = None
        self.description = None
        self.xs1, self.xs2, self.xs3, self.xs4, self.xs8 = None, None, None, None, None
        self.plots       = []
        self.initial     = 0

    # this helped: https://techoverflow.net/2021/08/20/how-to-autoscale-matplotlib-xy-axis-after-set_data-call/
    def add(self, **kwargs):
        if self.numerator in ('If', 'Xs'):
            if self.xs1 in kwargs['data']:  # this is a primary documemnt
                signal = kwargs['data'][self.xs1] + kwargs['data'][self.xs2] + kwargs['data'][self.xs3] + kwargs['data'][self.xs4]
                if numpy.isnan(signal):
                    signal = 0
            else:                           # this is a baseline document
                return
        elif self.numerator == 'Xs1':
            signal = kwargs['data'][self.xs8]
        elif self.numerator in kwargs['data']:  # numerator will not be in baseline document
            signal = kwargs['data'][self.numerator]
        else:
            print(f'could not determine signal, self.numerator is {self.numerator}')
            return
            
        if self.motor is None:   # this is a time scan
            if kwargs['seq_num'] == 1:
                self.initial = kwargs['time']
            self.xdata.append(kwargs['time'] - self.initial)
        else:
            self.xdata.append(kwargs['data'][self.motor])
        if self.denominator is None:
            self.ydata.append(signal)
        else:
            self.ydata.append(signal/kwargs['data'][self.denominator])
        self.line.set_data(self.xdata, self.ydata)
        self.axes.relim()
        self.axes.autoscale_view(True,True,True)
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    def close_all_lineplots(self):
        for i in self.plots:
            plt.close(i)
            


class XAFSScan():
    '''Plot a grid of views of the data streaming from an XAFS scan.

    Care is taken to maintain references to the matplotlib objects in
    each grid panel of the plot.

    In the event of an ion-chamber-only scan, show a 1x3 grid:

    +----------+----------+----------+
    |          |          |          |
    |   mu(E)  |   I0     |  ref(E)  |
    |          |          |          |
    +----------+----------+----------+

    In the event of a scan with fluorescence, show a 2x2 grid:

    +----------+----------+
    |          |          |
    | trans(E) | fluo(E)  |
    |          |          |
    +----------+----------+
    |          |          |
    |    I0    | ref(E)   |
    |          |          |
    +----------+----------+

    '''

    ongoing     = False
    energy      = []
    i0sig       = []
    trans       = []
    fluor       = []
    refer       = []
    xs1, xs2, xs3, xs4, xs8 = None, None, None, None, None
    mode        = None
    filename    = None
    repn        = 0
    reference_material = None
    sample      = None

    fig, gs = None, None
    mut, line_mut = None, None
    muf, line_muf = None, None
    i0 , line_i0  = None, None
    ref, line_ref = None, None
    axis_list = []
    
    def start(self, **kwargs):
        '''Begin a sequence of XAFS live plots.
        '''
        self.ongoing     = True
        self.energy      = []
        self.i0sig       = []
        self.trans       = []
        self.fluor       = []
        self.refer       = []
        self.mode        = kwargs['mode']
        self.filename    = kwargs['filename']
        self.repetitions = kwargs['repetitions']
        self.count       = 1
        self.reference_material = kwargs['reference_material']
        self.sample      = kwargs['sample']
        
        ## close the plot from the last sequence
        if self.fig is not None:
            plt.close(self.fig.number)
        plt.rcParams["figure.raise_window"] = True
        self.fig = plt.figure(num='XAFS live view', tight_layout=True)
        plt.rcParams["figure.raise_window"] = False


        ## 2x2 grid if fluorescence
        if self.mode in ('both', 'fluorescence', 'fluo', 'flourescence', 'flour', 'xs', 'xs1'):
            self.xs1 = rkvs.get('BMM:user:xs1').decode('utf-8')
            self.xs2 = rkvs.get('BMM:user:xs2').decode('utf-8')
            self.xs3 = rkvs.get('BMM:user:xs3').decode('utf-8')
            self.xs4 = rkvs.get('BMM:user:xs4').decode('utf-8')
            self.xs8 = rkvs.get('BMM:user:xs8').decode('utf-8')
            self.fig.canvas.manager.window.setGeometry(1360, 1790, 1200, 1062)
            self.gs = gridspec.GridSpec(2,2)
            self.mut = self.fig.add_subplot(self.gs[0, 0])
            self.muf = self.fig.add_subplot(self.gs[0, 1])
            self.i0  = self.fig.add_subplot(self.gs[1, 0])
            self.ref = self.fig.add_subplot(self.gs[1, 1])
            self.axis_list   = [self.mut,  self.muf,  self.i0,  self.ref]
        ## 1x3 grid if no fluorescence (transmission, reference, test)
        else:
            self.fig.canvas.manager.window.setGeometry(760, 2259, 1800, 593)
            self.gs = gridspec.GridSpec(1,3)
            self.mut = self.fig.add_subplot(self.gs[0, 0])
            self.i0  = self.fig.add_subplot(self.gs[0, 1])
            self.ref = self.fig.add_subplot(self.gs[0, 2])
            self.axis_list   = [self.mut,  self.i0,  self.ref]
        self.fig.suptitle(f'{self.filename}: scan {self.count} of {self.repetitions}')


        ## start lines and set axis labels
        #self.line_mut, = self.mut.plot([],[], label='$\mu_T(E)$')
        self.mut.set_ylabel('$\mu(E)$ (transmission)')
        self.mut.set_xlabel('energy (eV)')
        self.mut.set_title(f'data: {self.sample}')

        #self.line_i0, = self.i0.plot([],[], label='I0')
        self.i0.set_ylabel('I0 (nanoamps)')
        self.i0.set_xlabel('energy (eV)')
        self.i0.set_title('I0')

        #self.line_ref, = self.ref.plot([],[], label='reference')
        self.ref.set_ylabel('reference $\mu(E)$')
        self.ref.set_xlabel('energy (eV)')
        self.ref.set_title(f'reference: {self.reference_material}')

        ## common appearance
        for ax in self.axis_list:
            ax.grid(which='major', axis='both')
            ax.set_facecolor((0.95, 0.95, 0.95))
        
        ## do all that for a fluorescence panel
        if self.mode in ('both', 'fluorescence', 'fluo', 'flourescence', 'flour', 'xs', 'xs1'):
            self.muf.set_ylabel('$\mu(E)$ (fluorescence)')
            self.muf.set_xlabel('energy (eV)')
            self.muf.set_title(f'data: {self.sample}')

        

            
    def Next(self, **kwargs):
        '''Initialize data arrays and plotting lines for next scan.
        '''
        self.count = kwargs['count']
        self.fig.suptitle(f'{self.filename}: scan {self.count} of {self.repetitions}')
        self.energy      = []
        self.i0sig       = []
        self.trans       = []
        self.fluor       = []
        self.refer       = []
        self.line_mut,   = self.mut.plot([],[], label=f'scan {self.count}')
        self.line_i0,    = self.i0.plot([],[],  label=f'scan {self.count}')
        self.line_ref,   = self.ref.plot([],[], label=f'scan {self.count}')
        for ax in (self.mut, self.i0, self.ref):
            if self.count < 16:
                ax.legend(loc='best', shadow=True)
            else:
                ax.legend.remove()
        if self.mode in ('both', 'fluorescence', 'fluo', 'flourescence', 'flou', 'xs', 'xs1'):
            self.line_muf, = self.muf.plot([],[], label=f'scan {self.count}')
            if self.count < 16:
                self.muf.legend(loc='best', shadow=True)
            else:
                self.muf.legend.remove()
            
    def stop(self, **kwargs):
        '''Done with a sequence of XAFS live plots.
        '''
        self.ongoing     = False
        self.xdata       = []
        self.ydata       = []
        self.motor       = None
        self.numerator   = None
        self.denominator = 1
        self.figure      = None
        self.axes        = None
        self.line        = None
        self.description = None
        self.xs1, self.xs2, self.xs3, self.xs4, xs8 = None, None, None, None, None
        self.plots       = []
        self.initial     = 0
        


    def add(self, **kwargs):
        '''Add the most recent event to the current XAFS live plot.
        '''
        if 'dcm_energy' not in kwargs['data']:
            return              # this is a baseline event document

        ## primary event document, append to data arrays
        self.energy.append(kwargs['data']['dcm_energy'])
        self.i0sig.append(kwargs['data']['I0'])
        self.trans.append(numpy.log(abs(kwargs['data']['I0']/kwargs['data']['It'])))
        self.refer.append(numpy.log(abs(kwargs['data']['It']/kwargs['data']['Ir'])))

        ## push the updated data arrays to the various lines
        self.line_mut.set_data(self.energy, self.trans)
        self.line_i0.set_data(self.energy, self.i0sig)
        self.line_ref.set_data(self.energy, self.refer)

        ## and do all that for the fluorescence spectrum if it is being plotted.
        if self.mode in ('both', 'fluorescence', 'fluo', 'flourescence', 'flour', 'xs', 'xs1'):
            if self.mode == 'xs1':
                self.fluor.append( kwargs['data'][self.xs8] / kwargs['data']['I0'] )
            else:
                self.fluor.append( (kwargs['data'][self.xs1]+kwargs['data'][self.xs2]+kwargs['data'][self.xs3]+kwargs['data'][self.xs4])/kwargs['data']['I0'])
            self.line_muf.set_data(self.energy, self.fluor)

        ## rescale everything
        for ax in self.axis_list:
            ax.relim()
            ax.autoscale_view(True,True,True)
        ## redraw and flush the canvas 
        ## Tom's explanation for how to do multiple plots: https://stackoverflow.com/a/31686953
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        
            
