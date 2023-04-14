import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_multitab import MplTabs
import numpy

import redis
rkvs = redis.Redis(host='xf06bm-ioc2', port=6379, db=0)


class LineScan():

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
    
    def start(self, **kwargs):
        #if self.figure is not None:
        #    plt.close(self.figure.number)
        self.ongoing = True
        self.xdata = []
        self.ydata = []
        self.motor = kwargs['motor']
        self.numerator = kwargs['detector']
        self.denominator = None
        self.figure = plt.figure()
        self.plots.append(self.figure.number)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_xlabel(self.motor)
        self.axes.set_ylabel(self.numerator)
        self.axes.set_facecolor((0.95, 0.95, 0.95))
        self.line, = self.axes.plot([],[])

        self.xs1 = rkvs.get('BMM:user:xs1').decode('utf-8')
        self.xs2 = rkvs.get('BMM:user:xs2').decode('utf-8')
        self.xs3 = rkvs.get('BMM:user:xs3').decode('utf-8')
        self.xs4 = rkvs.get('BMM:user:xs4').decode('utf-8')
        self.xs8 = rkvs.get('BMM:user:xs8').decode('utf-8')


        ## todo:  bicron, new ion chambers, both
        
        ## transmission: plot It/I0
        if self.numerator == 'It':
            self.description = 'transmission'
            self.denominator = 'I0'

        ## I0: plot just I0
        elif self.numerator == 'I0':
            self.description = 'I0'
            self.denominator = None

        ## reference: plot just Ir
        elif self.numerator == 'Ir':
            self.description = 'reference'
            self.denominator = None

        ## yield: plot Iy/I0
        elif self.numerator == 'Iy':
            self.description = 'yield'
            self.denominator = 'I0'

        ## fluorescence (4 channel): plot sum(If)/I0
        ##xs1, xs2, xs3, xs4 = rkvs.get('BMM:user:xs1'), rkvs.get('BMM:user:xs2'), rkvs.get('BMM:user:xs3'), rkvs.get('BMM:user:xs4')
        elif self.numerator in ('If', 'Xs'):
            self.description = 'fluorescence (4 channel)'
            self.denominator = 'I0'
            self.axes.set_ylabel('fluorescence (4 channel)')

        ## fluorescence (1 channel): plot If/I0
        ##xs8 = rkvs.get('BMM:user:xs8').decode('utf-8')
        elif self.numerator == 'Xs1':
            self.description = 'fluorescence (1 channel)'
            self.denominator = 'I0'
            self.axes.set_ylabel('fluorescence (1 channel)')
            
        self.axes.set_title(f'{self.description} vs. {self.motor}')

        
    def stop(self, **kwargs):
        self.ongoing = False

    # this helped: https://techoverflow.net/2021/08/20/how-to-autoscale-matplotlib-xy-axis-after-set_data-call/
    def add(self, **kwargs):
        if self.numerator in kwargs['data']:
            #print('*********  ', kwargs['data'][self.motor], kwargs['data'][self.numerator])
            self.xdata.append(kwargs['data'][self.motor])
            if self.numerator in ('If', 'Xs'):
                signal = kwargs['data'][self.xs1] + kwargs['data'][self.xs2] + kwargs['data'][self.xs3] + kwargs['data'][self.xs4]
                if numpy.isnan(signal):
                    signal = 0
            elif self.numerator == 'Xs1':
                signal = kwargs['data'][self.xs8]
            else:
                signal = kwargs['data'][self.numerator]
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
            self.fig.canvas.manager.window.setGeometry(1877, 378, 1200, 1062)
            self.gs = gridspec.GridSpec(2,2)
            self.mut = self.fig.add_subplot(self.gs[0, 0])
            self.i0  = self.fig.add_subplot(self.gs[1, 0])
            self.ref = self.fig.add_subplot(self.gs[1, 1])
        ## 1x3 grid if no fluorescence (transmission, reference, test)
        else:
            self.fig.canvas.manager.window.setGeometry(1377, 778, 1800, 562)
            self.gs = gridspec.GridSpec(1,3)
            self.mut = self.fig.add_subplot(self.gs[0, 0])
            self.i0  = self.fig.add_subplot(self.gs[0, 1])
            self.ref = self.fig.add_subplot(self.gs[0, 2])
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

        ## common appearence
        for ax in (self.mut, self.i0, self.ref):
            ax.grid(which='major', axis='both')
            ax.set_facecolor((0.95, 0.95, 0.95))
        
        ## do all that for a fluorescence panel
        if self.mode in ('both', 'fluorescence', 'fluo', 'flourescence', 'flour', 'xs', 'xs1'):
            self.muf = self.fig.add_subplot(self.gs[0, 1])
            self.line_muf, = self.muf.plot([],[], label='$\mu_F(E)$')
            self.muf.set_ylabel('$\mu(E)$ (fluorescence)')
            self.muf.set_xlabel('energy (eV)')
            self.muf.set_title(f'data: {self.sample}')
            self.muf.grid(which='major', axis='both')
            self.muf.set_facecolor((0.95, 0.95, 0.95))


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
            ax.legend(loc='best', shadow=True)
        if self.mode in ('both', 'fluorescence', 'fluo', 'flourescence', 'flou', 'xs', 'xs1'):
            self.line_muf, = self.muf.plot([],[], label=f'scan {self.count}')
            self.muf.legend(loc='best', shadow=True)
        
            
    def stop(self, **kwargs):
        '''Done with a sequence of XAFS live plots.
        '''
        self.ongoing = False


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

        ## rescale everything
        for ax in (self.mut, self.i0, self.ref):
            ax.relim()
            ax.autoscale_view(True,True,True)

        ## and do all that for the fluorescence spectrum if it is being plotted.
        if self.mode in ('both', 'fluorescence', 'fluo', 'flourescence', 'flour', 'xs', 'xs1'):
            if self.mode == 'xs1':
                self.fluor.append( kwargs['data'][self.xs8] / kwargs['data']['I0'] )
            else:
                self.fluor.append( (kwargs['data'][self.xs1]+kwargs['data'][self.xs2]+kwargs['data'][self.xs3]+kwargs['data'][self.xs4])/kwargs['data']['I0'])
            self.line_muf.set_data(self.energy, self.fluor)
            self.muf.relim()
            self.muf.autoscale_view(True,True,True)

        ## redraw and flush the canvas 
        ## Tom's explanation for how to do multiple plots: https://stackoverflow.com/a/31686953
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        
            
class XAFSScan_tabbed():

    ongoing     = False
    energy      = []
    i0          = []
    trans       = []
    fluo        = []
    ref         = []
    xs1, xs2, xs3, xs4, xs8 = None, None, None, None, None
    mode        = None

    fig_mut, ax_mut, line_mut = None, None, None
    fig_muf, ax_muf, line_muf = None, None, None
    fig_i0 , ax_i0 , line_i0  = None, None, None
    fig_ref, ax_ref, line_ref = None, None, None
    
    def start(self, **kwargs):
        #if self.figure is not None:
        #    plt.close(self.figure.number)
        self.ongoing = True
        self.energy = []
        self.i0 = []
        self.mut = []
        self.muf = []
        self.ref = []
        self.ui = MplTabs()
        self.mode = kwargs['mode']
        
        ## tab with transmission mu(E)
        self.fig_mut = self.ui.add_tab('trans')
        self.ax_mut  = self.fig_mut.subplots()
        self.ax_mut.set_xlabel('Energy (eV)')
        self.ax_mut.set_ylabel('mu(E)  (transmission)')
        self.ax_mut.set_facecolor((0.95, 0.95, 0.95))
        self.line_mut, = self.ax_mut.plot([],[])

        if kwargs['mode'] in ('both', 'fluorescence', 'fluo', 'flourescence', 'flour', 'xs', 'xs1'):
            ## tab with fluorescence mu(E)
            self.fig_muf = self.ui.add_tab('fluo')
            self.ax_muf  = self.fig_muf.subplots()
            self.ax_muf.set_xlabel('Energy (eV)')
            self.ax_muf.set_ylabel('mu(E)  (fluorescence)')
            self.ax_muf.set_facecolor((0.95, 0.95, 0.95))
            self.line_muf, = self.ax_muf.plot([],[])

        ## tab with I0
        self.fig_i0 = self.ui.add_tab('I0')
        self.ax_i0  = self.fig_i0.subplots()
        self.ax_i0.set_xlabel('Energy (eV)')
        self.ax_i0.set_ylabel('I0  (nanoamps)')
        self.ax_i0.set_facecolor((0.95, 0.95, 0.95))
        self.line_i0, = self.ax_i0.plot([],[])

        ## tab with reference
        self.fig_ref = self.ui.add_tab('ref')
        self.ax_ref  = self.fig_ref.subplots()
        self.ax_ref.set_xlabel('Energy (eV)')
        self.ax_ref.set_ylabel('reference')
        self.ax_ref.set_facecolor((0.95, 0.95, 0.95))
        self.line_ref, = self.ax_ref.plot([],[])

        self.xs1 = rkvs.get('BMM:user:xs1').decode('utf-8')
        self.xs2 = rkvs.get('BMM:user:xs2').decode('utf-8')
        self.xs3 = rkvs.get('BMM:user:xs3').decode('utf-8')
        self.xs4 = rkvs.get('BMM:user:xs4').decode('utf-8')
        self.xs8 = rkvs.get('BMM:user:xs8').decode('utf-8')

        if kwargs['mode'] in ('both', 'fluorescence', 'fluo', 'flourescence', 'flour', 'xs', 'xs1'):
            self.ui.set_focus(1)
        else:
            self.ui.set_focus(0)
        self.ui.show()

        
    def stop(self, **kwargs):
        self.ongoing = False

    def add(self, **kwargs):
        if 'dcm_energy' not in kwargs['data']:
            return              # this is a baseline event document
        self.energy.append(kwargs['data']['dcm_energy'])
        self.i0.append(kwargs['data']['I0'])
        self.mut.append(numpy.log(kwargs['data']['I0']/kwargs['data']['It']))
        self.ref.append(numpy.log(kwargs['data']['It']/kwargs['data']['Ir']))

        ## transmission plot tab
        self.line_mut.set_data(self.energy, self.mut)
        self.ax_mut.relim()
        self.ax_mut.autoscale_view(True,True,True)
        self.fig_mut.canvas.draw()
        self.fig_mut.canvas.flush_events()

        ## i0 plot tab
        self.line_i0.set_data(self.energy, self.i0)
        self.ax_i0.relim()
        self.ax_i0.autoscale_view(True,True,True)
        self.fig_i0.canvas.draw()
        self.fig_i0.canvas.flush_events()

        ## reference plot tab
        self.line_ref.set_data(self.energy, self.ref)
        self.ax_ref.relim()
        self.ax_ref.autoscale_view(True,True,True)
        self.fig_ref.canvas.draw()
        self.fig_ref.canvas.flush_events()

        if self.mode in ('both', 'fluorescence', 'fluo', 'flourescence', 'flour', 'xs', 'xs1'):
            self.muf.append( (kwargs['data'][self.xs1]+kwargs['data'][self.xs2]+kwargs['data'][self.xs3]+kwargs['data'][self.xs4]) / kwargs['data']['I0'] )
            ## fluorescence plot tab
            self.line_muf.set_data(self.energy, self.muf)
            self.ax_muf.relim()
            self.ax_muf.autoscale_view(True,True,True)
            self.fig_muf.canvas.draw()
            self.fig_muf.canvas.flush_events()
