import matplotlib
import matplotlib.pyplot as plt
import numpy
import matplotlib.gridspec as gridspec

from slack import img_to_slack

class AlignWheel():
    fig = None
    ongoing = False
    
    x_xaxis = []
    x_data = []
    x_best_fit = []
    x_center = 0
    x_amplitude = 0
    x_detector = ''

    y_xaxis = []
    y_data = []
    y_best_fit = []
    y_center = 0
    y_amplitude = 0
    y_detector = ''

    def start(self, **kwargs):
        self.ongoing = True
        self.fig = None

    def plot_rectangle(self, **kwargs):
        motor     = kwargs['motor']
        detector  = kwargs['detector']
        center    = kwargs['center'] 
        amplitude = kwargs['amplitude']
        xaxis     = kwargs['xaxis']
        data      = kwargs['data']
        best_fit  = kwargs['best_fit']

        direction = motor.split('_')[1]

        if direction == 'x':
            self.x_xaxis = xaxis
            self.x_data = data
            self.x_best_fit = best_fit
            self.x_center = center
            self.x_amplitude = amplitude
            self.x_detector = detector
        else:
            self.y_xaxis = xaxis
            self.y_data = data
            self.y_best_fit = best_fit
            self.y_center = center
            self.y_amplitude = amplitude
            self.y_detector = detector
            
            
        if self.fig is not None:
            plt.close(self.fig.number)
        self.fig = plt.figure()
        ax = self.fig.gca()
        ax.scatter(xaxis, data, color='blue')
        ax.plot(xaxis, best_fit, color='red')
        ax.scatter(center, abs(amplitude), s=160, marker='x', color='green')
        ax.set_facecolor((0.95, 0.95, 0.95))
        ax.set_xlabel(f'{motor} (mm)')
        ax.set_ylabel(f'{detector.capitalize()}/I0 and error function')
        ax.set_title(f'fit to {direction} scan, center={center:.3f}')
        self.fig.canvas.manager.show()
        self.fig.canvas.flush_events() 
        
    def stop(self):
        self.ongoing = False

        if self.fig is not None:
            plt.close(self.fig.number)

        self.fig = plt.figure(tight_layout=True) #, figsize=(9,6))
        gs = gridspec.GridSpec(2,1)

        x  = self.fig.add_subplot(gs[0, 0])
        x.scatter(self.x_xaxis, self.x_data, color='blue')
        x.plot(self.x_xaxis, self.x_best_fit, color='red')
        x.scatter(self.x_center, self.x_amplitude, s=160, marker='x', color='green')
        x.set_facecolor((0.95, 0.95, 0.95))
        x.set_xlabel('xafs_x (mm)')
        x.set_ylabel(f'{self.x_detector.capitalize()}/I0')
        x.set_title('Sample wheel alignment')
        
        y  = self.fig.add_subplot(gs[1, 0])
        y.scatter(self.y_xaxis, self.y_data, color='blue')
        y.plot(self.y_xaxis, self.y_best_fit, color='red')
        y.scatter(self.y_center, self.y_amplitude, s=160, marker='x', color='green')
        y.set_facecolor((0.95, 0.95, 0.95))
        y.set_xlabel('xafs_y (mm)')
        y.set_ylabel(f'{self.y_detector.capitalize()}/IO')
        
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        
        #self.fig.savefig(self.filename)
        #img_to_slack(self.filename)
