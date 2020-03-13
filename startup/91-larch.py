
from larch import (Group, Parameter, isParameter, param_value, isNamedClass, Interpreter) 
from larch.xafs import (find_e0, pre_edge, autobk, xftf, xftr)
import larch.utils.show as lus

import matplotlib.pyplot as plt

run_report(__file__)

LARCH = Interpreter()
LARCH_COLOR_COUNTER = 0


class Pandrosus():
    def __init__(self):
        self.name   = None
        self.group  = None
        self.energy = numpy.array(list())
        self.xmu    = numpy.array(list())
        ## pre and post
        self.pre    = {'e0':None, 'pre1':None, 'pre2':None, 'norm1':None, 'norm2':None, 'nnorm':None}
        self.bkg    = {'rbkg':1, 'e0':None, 'kmin':0, 'kmax':None, 'kweight':1,}
        self.fft    = {'window':'Hanning', 'kmin':3, 'kmax':12, 'dk':2,}
        self.bft    = {'window':'Hanning', 'rmin':1, 'rmax':3, 'dr':0.1,}

    def fetch(self, uid, name=None):
        header = db[uid]
        table = header.table()
        if name is not None:
            self.name = name
        else:
            self.name = uid[-6:]
        self.group = Group(__name__=self.name)
        self.energy = numpy.array(table['dcm_energy'])
        self.xmu = numpy.array(log(table['I0']/table['It']))
        self.group.energy = self.energy
        self.group.mu = self.xmu
        self.prep()
        
    def prep(self):
        autobk(self.energy, mu=self.xmu, group=self.group,
               rbkg    = self.bkg['rbkg'],
               e0      = self.bkg['e0'],
               kmin    = self.bkg['kmin'],
               kmax    = self.bkg['kmax'],
               kweight = self.bkg['kweight'],
               #pre_edge_kws = self.pre,
               _larch=LARCH)
        xftf(self.group.k, chi=self.group.chi, group=self.group,
             window = self.fft['window'],
             kmin   = self.fft['kmin'],
             kmax   = self.fft['kmax'],
             dk     = self.fft['dk'],
             _larch=LARCH)

    def show(self):
        lus.show(self.group, _larch=LARCH)
        
    def plot_xmu(self, bkg=False, pre=False, post=False, norm=False, flat=False, deriv=False):
        plt.cla()
        plt.xlabel('energy (eV)')
        plt.ylabel('xmu')

        g = self.group

        if flat is True:
            plt.plot(g.energy, g.flat, label=self.name + ' flattened')
            y = numpy.interp(g.e0, g.energy, g.flat)
            plt.scatter(g.e0, y, marker='d', color='orchid')
        elif norm is True:
            plt.plot(g.energy, g.norm, label=self.name + ' normalized')
            y = numpy.interp(g.e0, g.energy, g.norm)
            plt.scatter(g.e0, y, marker='d', color='orchid')
        elif deriv is True:
            plt.plot(g.energy, g.dmude, label=self.name + ' derivative')
            y = numpy.interp(g.e0, g.energy, g.dmude)
            plt.scatter(g.e0, y, marker='d', color='orchid')
        else:
            if bkg is True:
                plt.plot(g.energy, g.bkg, label='background', color='C1')
                y = numpy.interp(g.e0, g.energy, g.mu)
                plt.scatter(g.e0, y, marker='d', color='orchid')
                y = numpy.interp(g.e0+ktoe(g.autobk_details.kmax), g.energy, g.mu)
                plt.scatter(g.e0+ktoe(g.autobk_details.kmax), y, marker=2, color='tan')
                
            plt.plot(g.energy, g.mu, label=self.name, color='C0')
            if pre is True:
                plt.plot(g.energy, g.pre_edge, label='pre-edge', color='C2')
                y = numpy.interp(g.e0+g.pre_edge_details.pre1, g.energy, g.mu)
                plt.scatter(g.e0+g.pre_edge_details.pre1, y, marker='|', color='orchid')
                y = numpy.interp(g.e0+g.pre_edge_details.pre2, g.energy, g.mu)
                plt.scatter(g.e0+g.pre_edge_details.pre2, y, marker='|', color='orchid')
            if post is True:
                plt.plot(g.energy, g.post_edge, label='post-edge', color='C3')
                y = numpy.interp(g.e0+g.pre_edge_details.norm1, g.energy, g.mu)
                plt.scatter(g.e0+g.pre_edge_details.norm1, y, marker='|', color='orchid')
                y = numpy.interp(g.e0+g.pre_edge_details.norm2, g.energy, g.mu)
                plt.scatter(g.e0+g.pre_edge_details.norm2, y, marker='|', color='orchid')
        legend = plt.legend(loc='upper right', shadow=True)


    def plot_chi(self, kw=2, win=True):
        # global color_counter
        # if new:
        #     color_counter=0
        #     plt.cla()
        plt.cla()
        plt.xlabel('wavenumber (Å$^{-1}$)')
        plt.ylabel('$\chi$(k) * k$^%d$  (Å$^%d$)' % (kw, kw))
        y = self.group.chi*self.group.k**kw
        plt.plot(self.group.k, y, label=self.name)
        if win:
            plt.plot(self.group.k, self.group.kwin*y.max()*1.1, label='window', color='C8')
        #color_counter += 1
        legend = plt.legend(loc='upper right', shadow=True)

    def do_xftf(self, kw=2):
        xftf(self.group.k, chi=self.group.chi, group=self.group,
             window = self.fft['window'],
             kmin   = self.fft['kmin'],
             kmax   = self.fft['kmax'],
             dk     = self.fft['dk'],
             kweight = kw,
             _larch=LARCH)
    def plot_chir(self, kw=2, win=True, part='mag'):
        self.do_xftf(kw=kw)
        self.do_xftr()
        plt.cla()
        plt.xlabel('radial distance (Å)')
        plt.ylabel('|$\chi$(R)| (Å$^%d$)' % (kw+1))
        y = self.group.chir_mag
        plt.plot(self.group.r, y, label=self.name, color='C%d'%color_counter)
        if win:
            plt.plot(self.group.r, self.group.rwin*y.max()*1.1, label='window', color='C8')
        legend = plt.legend(loc='upper right', shadow=True)
        
    def do_xftr(self):
        xftr(self.group.r, chir=self.group.chir, group=self.group,
             window = self.bft['window'],
             rmin   = self.bft['rmin'],
             rmax   = self.bft['rmax'],
             dr     = self.bft['dr'],
             _larch=LARCH)
    def plot_chiq(self, part='im'):
        self.do_xftr()
        plt.cla()
        plt.xlabel('wavenumber (Å$^{-1}$)')
        plt.ylabel('|$\chi$(q)|')
        plt.xlim(right=self.group.k.max())
        plt.plot(self.group.q, self.group.chiq_im, label=self.name, color='C%d'%color_counter)


se = Pandrosus()
se.fetch('8e293af3-811c-4e96-a4e5-733d0dc77dad')
seo = Pandrosus()
seo.fetch('69c35332-6c8a-4f43-9eb2-e5e9cbe7f798')


## grouping of Pandrosus objects for purple plots
## class Kekropidai():
