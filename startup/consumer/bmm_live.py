import matplotlib.pyplot as plt
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
        pass

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
            
