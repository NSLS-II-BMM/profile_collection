
## Once upon a time Pallas hid a child, Erichthonius, born without a
## human mother, in a box made of Actaean osiers. She gave this to the
## three virgin daughters of two-natured Cecrops, who was part human
## part serpent, and ordered them not to pry into its secret. Hidden
## in the light leaves that grew thickly over an elm-tree I set out to
## watch what they might do. Two of the girls, Pandrosus and Herse,
## obeyed without cheating, but the third Aglauros called her sisters
## cowards and undid the knots with her hand, and inside they found a
## baby boy with a snake stretched out next to him. That act I
## betrayed to the goddess. And this is the reward I got for it, no
## longer consecrated to Minerva’s protection, and ranked below the
## Owl, that night-bird! My punishment should be a warning to all
## birds not to take risks by speaking out.’
##
##                           Ovid, Metamorphosis
##                           Book II:531-565

import numpy
from larch import (Group, Parameter, isParameter, param_value, isNamedClass, Interpreter) 
from larch.xafs import (find_e0, pre_edge, autobk, xftf, xftr)
import larch.utils.show as lus
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from BMM.functions import etok, ktoe

from bluesky_queueserver.manager.profile_tools import set_user_ns

## from IPython import get_ipython
## user_ns = get_ipython().user_ns

LARCH = Interpreter()


class Pandrosus():
    '''A thin wrapper around basic XAS data processing for individual
    data sets as implemented in Larch.

    The plotting capabilities of this class are very similar to the
    orange plot buttons in Athena.

    Attributes
    ----------
    uid : str
        Databroker unique ID of the data set, used to fetch mu(E) from the database
    name : str
        Human-readable name of the data set
    group : str
        Larch group containing the data
    pre : dict
        Dictionary of pre-edge and normalization arguments
    bkg : dict
        Dictionary of background subtraction arguments
    fft : dict   Dictionary of forward Fourier transform arguments
    bft : dict
        Dictionary of backward Fourier transform arguments
    rmax : float
        upper bound of R-space plot

    See http://xraypy.github.io/xraylarch/xafs/preedge.html and
    http://xraypy.github.io/xraylarch/xafs/autobk.html for details
    about these parameters.

    Methods
    ------
    fetch:      
        Get data set and prepare for analysis with Larch
    make_xmu:
        method that actually constructs mu(E) from the data source
    put:
        make a Pandrosus object from ndarrays for energy and mu
    show:
        wrapper around Larch's show command, examine the content of the Larch group
    prep: 
        normalize, background subtract, and forward transform the data
    do_xftf:
        perform the forward (k->R) transform
    do_xftr:
        perform the reverse (R->q) transform

    Plotting methods
    ----------------
    plot_xmu :
        plot data in energy (alias = pe)
    plot_signals : 
        plot mu(E) with I0 and the transmission or fluorescence signal (allias = ps)
    plot_chik :
        plot data in k-space (alias = pk)
    plot_chir :
        plot data in R-space (alias = pr)
    plot_chiq :
        plot data in back-transform k-space (alias = pq)
    plot_chikq :
        plot chi(k) + RE(chi(q)) (alias = pkq)
    triplot :
        plot mu(E), chi(k), and chi(R) in a grid

    '''
    def __init__(self, uid=None, name=None):
        self.uid    = uid
        self.name   = name
        self.group  = None
        ## Larch parameters
        self.pre    = {'e0':None, 'pre1':None, 'pre2':None, 'norm1':None, 'norm2':None, 'nnorm':None, 'nvict':0,}
        self.bkg    = {'rbkg':1, 'e0':None, 'kmin':0, 'kmax':None, 'kweight':2,}
        self.fft    = {'window':'Hanning', 'kmin':3, 'kmax':12, 'dk':2,}
        self.bft    = {'window':'Hanning', 'rmin':1, 'rmax':3, 'dr':0.1,}
        ## plotting parameters
        self.xe     = 'energy (eV)'
        self.xk     = 'wavenumber ($\AA^{-1}$)'
        self.xr     = 'radial distance ($\AA$)'
        self.rmax   = 6

        ## flow control parameters

    @set_user_ns
    def make_xmu(self, uid, mode, *, user_ns):
        '''Load energy and mu(E) arrays into Larch and into this wrapper object.
        
        ***************************************************************
        This should be the only part of this startup script that needs
        beamline-specific configuration.  What is shown below is
        specific to how data are retrieved from Databroker at
        BMM. Other beamlines -- or reading data from files -- will
        need something different.
        ***************************************************************

        Parameters
        ----------
        uid : str
            database identifier (assuming you are using databroker)
        mode : str
            'transmission', 'fluorescence', or 'reference'

        '''
        db, BMMuser = user_ns['db'], user_ns['BMMuser']
        header = db[uid]
        table  = header.table()
        self.group.energy = numpy.array(table['dcm_energy'])
        self.group.i0 = numpy.array(table['I0'])
        if mode == 'flourescence': mode = 'fluorescence'
        if mode == 'reference':
            self.group.mu = numpy.array(numpy.log(table['It']/table['Ir']))
            self.group.i0 = numpy.array(table['It'])
            self.group.signal = numpy.array(table['Ir'])

        #######################################################################################
        # CAUTION!!  This only works when BMMuser is correctly set.  This is unlikely to work #
        # on data in past history.  See new '_dtc' element of start document.  9 Sep 2020     #
        #######################################################################################
        elif mode == 'fluorescence':
            columns = header.start['XDI']['_dtc']
            self.group.mu = numpy.array((table[columns[0]]+table[columns[1]]+table[columns[2]]+table[columns[3]])/table['I0'])
            self.group.i0 = numpy.array(table['I0'])
            self.group.signal = numpy.array(table[columns[0]]+table[columns[1]]+table[columns[2]]+table[columns[3]])

        elif mode == 'xs':
            columns = header.start['XDI']['_dtc']
            self.group.mu = numpy.array((table[columns[0]]+table[columns[1]]+table[columns[2]]+table[columns[3]])/table['I0'])
            self.group.i0 = numpy.array(table['I0'])
            self.group.signal = numpy.array(table[columns[0]]+table[columns[1]]+table[columns[2]]+table[columns[3]])

        else:
            self.group.mu = numpy.array(numpy.log(table['I0']/table['It']))
            self.group.i0 = numpy.array(table['I0'])
            self.group.signal = numpy.array(table['It'])
        
    def fetch(self, uid, name=None, mode='transmission'):
        self.uid = uid
        if name is not None:
            self.name = name
        else:
            self.name = uid[-6:]
        self.group = Group(__name__=self.name)
        self.make_xmu(uid, mode=mode)
        self.prep()

    def put(self, energy, mu, name):
        self.name = name
        self.group = Group(__name__=self.name)
        self.group.energy = energy
        self.group.mu = mu
        self.prep()
        
    def prep(self):
        ## the next several lines seem necessary because the version
        ## of Larch currently at BMM is not correctly resolving
        ## pre1=pre2=None or norm1=norm2=None.  The following
        ## approximates Larch's defaults
        if self.pre['e0'] is None:
            find_e0(self.group.energy, mu=self.group.mu, group=self.group, _larch=LARCH)
            ezero = self.group.e0
        else:
            ezero = self.pre['e0']
        if self.pre['norm2'] is None:
            self.pre['norm2'] = self.group.energy.max() - ezero
        if self.pre['norm1'] is None:
            self.pre['norm1'] = self.pre['norm2'] / 5
        if self.pre['pre1'] is None:
            self.pre['pre1'] = self.group.energy.min() - ezero
        if self.pre['pre2'] is None:
            self.pre['pre2'] = self.pre['pre1'] / 3
        pre_edge(self.group.energy, mu=self.group.mu, group=self.group,
                 e0    = ezero,
                 step  = None,
                 pre1  = self.pre['pre1'],
                 pre2  = self.pre['pre2'],
                 norm1 = self.pre['norm1'],
                 norm2 = self.pre['norm2'],
                 nnorm = self.pre['nnorm'],
                 nvict = self.pre['nvict'],
                 _larch=LARCH)
        autobk(self.group.energy, mu=self.group.mu, group=self.group,
               rbkg    = self.bkg['rbkg'],
               e0      = self.bkg['e0'],
               kmin    = self.bkg['kmin'],
               kmax    = self.bkg['kmax'],
               kweight = self.bkg['kweight'],
               _larch=LARCH)
        xftf(self.group.k, chi=self.group.chi, group=self.group,
             window = self.fft['window'],
             kmin   = self.fft['kmin'],
             kmax   = self.fft['kmax'],
             dk     = self.fft['dk'],
             _larch=LARCH)

    def show(self, which=None):
        if which is None:
            lus.show(self.group, _larch=LARCH)
        elif 'pre' in which:
            lus.show(self.group.pre_edge_details, _larch=LARCH)
        elif which == 'autobk':
            lus.show(self.group.autobk_details, _larch=LARCH)
        elif which == 'fft' or which == 'xftf':
            lus.show(self.group.xftf_details, _larch=LARCH)
        elif which == 'bft' or which == 'xftr':
            lus.show(self.group.xftr_details, _larch=LARCH)
        else:
            lus.show(self.group, _larch=LARCH)
        
    def plot_xmu(self, bkg=False, pre=False, post=False, norm=False, flat=False, deriv=False):
        '''Make a plot of mu(E) for a single data set.

        All arguments default to plot, so you must explicitly turn on
        each additional modification or trace beyond the raw data.

        Parameters
        ----------
        bkg : bool
            True to plot the background function
        pre : bool
            True to plot the pre-edge line
        post : bool
            True to plot the post-edge line
        norm : bool
            True to plot normalized mu(E)
        flat : bool
            True to plot "flattened" mu(E)
        deriv : bool
            True to plot the derivative of mu(E)

        Setting norm, flat, or deriv to True, forces bkg, pre, and post to False.

        Setting flat to True forces norm to False.

        Setting deriv to True forces all other arguments to false.
        '''
        plt.cla()
        plt.xlabel(self.xe)
        plt.title(self.name + ' in energy')
        plt.grid(which='major', axis='both')
        
        g = self.group

        if deriv is True:
            plt.ylabel('$d[\mu(E)] / dE$')
            plt.plot(g.energy, g.dmude, label=self.name + ' derivative')
            y = numpy.interp(g.e0, g.energy, g.dmude)
            plt.scatter(g.e0, y, marker='d', color='orchid')
        elif flat is True:
            plt.ylabel('flattened $\mu(E)$')
            plt.plot(g.energy, g.flat, label=self.name + ' flattened')
            y = numpy.interp(g.e0, g.energy, g.flat)
            plt.scatter(g.e0, y, marker='d', color='orchid')
        elif norm is True:
            plt.ylabel('normalized $\mu(E)$')
            plt.plot(g.energy, g.norm, label=self.name + ' normalized')
            y = numpy.interp(g.e0, g.energy, g.norm)
            plt.scatter(g.e0, y, marker='d', color='orchid')
        else:
            plt.ylabel('$\mu(E)$')
            if bkg is True:
                plt.plot(g.energy, g.bkg, label='background', color='C1')
                y = numpy.interp(g.e0, g.energy, g.mu)
                plt.scatter(g.e0, y, marker='d', color='orchid')
                y = numpy.interp(g.e0+ktoe(g.autobk_details.kmax), g.energy, g.mu)
                plt.scatter(g.e0+ktoe(g.autobk_details.kmax), y, marker=2, color='tan')
                
            plt.plot(g.energy, g.mu, label='$\mu(E)$', color='C0')
            if pre is True:
                plt.plot(g.energy, g.pre_edge, label='pre-edge', color='C2')
                y = numpy.interp(g.e0+g.pre_edge_details.pre1, g.energy, g.mu)
                plt.scatter(g.e0+g.pre_edge_details.pre1, y, marker='|', color='orchid')
                y = numpy.interp(g.e0+g.pre_edge_details.pre2, g.energy, g.mu)
                plt.scatter(g.e0+g.pre_edge_details.pre2, y, marker='|', color='orchid')
            if post is True:
                plt.plot(g.energy, g.post_edge, label='post-edge', color='C4')
                y = numpy.interp(g.e0+g.pre_edge_details.norm1, g.energy, g.mu)
                plt.scatter(g.e0+g.pre_edge_details.norm1, y, marker='|', color='orchid')
                y = numpy.interp(g.e0+g.pre_edge_details.norm2, g.energy, g.mu)
                plt.scatter(g.e0+g.pre_edge_details.norm2, y, marker='|', color='orchid')
        plt.legend(loc='best', shadow=True)

    def plot_signals(self):
        '''Make a plot of mu(E) for a single data set with I0 and the signal
        (i.e. either If or It) both scaled to plot on the same y-axis.

        This allows you to investigate the effect of monochromator
        glitches and other experimental artifacts.

        '''
        plt.cla()
        plt.xlabel(self.xe)
        plt.title(self.name + ' in energy')
        plt.grid(which='major', axis='both')

        g = self.group

        max_xmu    = g.mu.max()
        max_i0     = g.i0.max()
        max_signal = g.signal.max()

        plt.plot(g.energy, g.mu, label='$\mu(E)$')
        plt.plot(g.energy, g.i0*max_xmu/max_i0, label='$I_0$')
        plt.plot(g.energy, g.signal*max_xmu/max_signal, label='signal')
        plt.legend(loc='best', shadow=True)

        
    def plot_chi(self, kw=2, win=True):
        '''
        Make a plot in k-space of a single data set.

        Arguments:
          kw:   specify the k-weight used in the plot [2]
          win:  plot FT window if True [True]
        '''
        plt.cla()
        plt.xlabel(self.xk)
        plt.ylabel(f"$k^{kw}\cdot\chi(k)$  ($\AA^{{-{kw}}}$)")
        plt.title(self.name + ' in k-space')
        plt.grid(which='major', axis='both')
        y = self.group.chi*self.group.k**kw
        plt.plot(self.group.k, y, label='$\chi(k)$')
        if win:
            plt.plot(self.group.k, self.group.kwin*y.max()*1.1, label='window', color='C8')
        #color_counter += 1
        legend = plt.legend(loc='best', shadow=True)
    plot_chik = plot_chi
        
    def do_xftf(self, kw=2):
        xftf(self.group.k, chi=self.group.chi, group=self.group,
             window  = self.fft['window'],
             kmin    = self.fft['kmin'],
             kmax    = self.fft['kmax'],
             dk      = self.fft['dk'],
             kweight = kw,
             with_phase=True, _larch=LARCH)
    def plot_chir(self, kw=2, win=True, parts='m'):
        '''Make a plot in R-space of a single data set.

        Parameters
        ----------
        kw : int
            specify the k-weight used in the plot [2]
        win : bool
            plot backtransform/fitting window if True [True]
        parts : str
            specify the parts of the complex transform to plot ['m']

        The argument to parts is a string that can contain the letters
        'm', 'r', 'i', 'p', or 'e', indicating the magnitude, real part,
        imaginary part, phase, or envelope of the complex transform. Examples:

        Examples
        --------
        plot the magnitude and imaginary parts:

        >>> data.plot_chir(parts='mi')

        plot the envelope, real, and imaginary parts:

        >>> data.plot_chir(parts='eri')

        The order of the letters in the parts argument does not matter.

        '''
        self.do_xftf(kw=kw)
        self.do_xftr()
        plt.cla()
        plt.xlabel(self.xr)
        plt.title(self.name + ' in R-space')
        plt.grid(which='major', axis='both')
        y = self.group.chir_mag
        color_counter = 0
        ylabel = False
        if 'e' in parts.lower():
            plt.ylabel(f"$|\chi(R)|$  ($\AA^{{-{kw+1}}}$)")
            ylabel = True
            plt.plot(self.group.r, self.group.chir_mag, label='Env[$\chi(R)$]', color='C%d'%color_counter)
            plt.plot(self.group.r, -1*self.group.chir_mag, color='C%d'%color_counter)
            color_counter += 1
        if 'm' in parts.lower():
            plt.ylabel(f"$|\chi(R)|$  ($\AA^{{-{kw+1}}}$)")
            ylabel = True
            plt.plot(self.group.r, self.group.chir_mag, label='$|\chi(R)|$', color='C%d'%color_counter)
            color_counter += 1
        if 'r' in parts.lower():
            if not ylabel:
                plt.ylabel(f"RE[$\chi$(R)]  ($\AA^{{-{kw+1}}}$)")
                ylabel = True
            plt.plot(self.group.r, self.group.chir_re, label='RE[$\chi(R)$]', color='C%d'%color_counter)
            color_counter += 1
        if 'i' in parts.lower():
            if not ylabel:
                plt.ylabel(f"IM[$\chi$(R)]  ($\AA^{{-{kw+1}}}$)")
                ylabel = True
            plt.plot(self.group.r, self.group.chir_im, label='IM[$\chi(R)$]', color='C%d'%color_counter)
            color_counter += 1
        if 'p' in parts.lower():
            if not ylabel:
                plt.ylabel('Phase($\chi$(R))')
                ylabel = True
            plt.plot(self.group.r, self.group.chir_pha, label='Phase[$\chi(R)$]', color='C%d'%color_counter)
            color_counter += 1
        if win and parts.lower() != 'p':
            plt.plot(self.group.r, self.group.rwin*y.max()*1.1, label='window', color='C8')
        plt.xlim(right=self.rmax)
        plt.legend(loc='best', shadow=True)
        
    def do_xftr(self):
        xftr(self.group.r, chir=self.group.chir, group=self.group,
             window = self.bft['window'],
             rmin   = self.bft['rmin'],
             rmax   = self.bft['rmax'],
             dr     = self.bft['dr'],
             with_phase=True, _larch=LARCH)
    def plot_chiq(self, kw=2, parts='r', win=True):
        '''Make a plot in back-transformed k-space of a single data set.

        Parameters
        ----------
        kw : int
            specify the k-weight used in the plot [2]
        win : bool
            plot FT window if True [True]
        parts : str 
            specify the parts of the complex transform to plot ['r']

        The argument to parts is a string that can contain the letters
        'm', 'r', 'i', 'p', or 'e', indicating the magnitude, real part,
        imaginary part, phase, or envelope of the complex transform. Examples:

        Examples
        --------
        plot the real parts (the part most like chi(k):
        
        >>> data.plot_chiq(parts='r')

        plot the envelope, real, and imaginary parts:

        >>> data.plot_chir(parts='eri')

        The order of the letters in the parts argument does not matter.

        '''
        self.prep()
        self.do_xftf(kw=kw)
        self.do_xftr()
        plt.cla()
        plt.xlabel(self.xk)
        plt.title(self.name + ' in back-transformed k-space')
        plt.xlim(right=self.group.k.max())
        plt.grid(which='major', axis='both')
        y = self.group.chiq_mag
        color_counter = 0
        ylabel = False
        if 'e' in parts.lower():
            plt.ylabel(f"|$\chi$(q)|  ($\AA^{{-{kw}}}$)")
            ylabel = True
            plt.plot(self.group.q, self.group.chiq_mag, label='Env[$\chi(R)$]', color='C%d'%color_counter)
            plt.plot(self.group.q, -1*self.group.chiq_mag, color='C%d'%color_counter)
            color_counter += 1
        if 'm' in parts.lower():
            plt.ylabel(f"|$\chi$(q)|  ($\AA^{{-{kw}}}$)")
            ylabel = True
            plt.plot(self.group.q, self.group.chiq_mag, label='$|\chi(R)|$', color='C%d'%color_counter)
            color_counter += 1
        if 'r' in parts.lower():
            if not ylabel:
                plt.ylabel(f"RE[$\chi$(q)]  ($\AA^{{-{kw}}}$)")
                ylabel = True
            plt.plot(self.group.q, self.group.chiq_re, label='RE[$\chi(R)$]', color='C%d'%color_counter)
            color_counter += 1
        if 'i' in parts.lower():
            if not ylabel:
                plt.ylabel(f"IM[$\chi$(q)]  ($\AA^{{-{kw}}}$)")
                ylabel = True
            plt.plot(self.group.q, self.group.chiq_im, label='IM[$\chi(R)$]', color='C%d'%color_counter)
            color_counter += 1
        if 'p' in parts.lower():
            if not ylabel:
                plt.ylabel('Phase($\chi$(q))')
                ylabel = True
            plt.plot(self.group.q, self.group.chiq_pha, label='Phase[$\chi(R)$]', color='C%d'%color_counter)
            color_counter += 1
        if win and parts.lower() != 'p':
            plt.plot(self.group.k, self.group.kwin*y.max()*1.1, label='window', color='C8')
        plt.legend(loc='best', shadow=True)

    def plot_chikq(self, kw=2, win=True):
        '''Make a plot in k-space with the real part of the Fourier filtered
        data of a single data set.

        Parameters
        ----------
        kw : int
            specify the k-weight used in the plot [2]
        win : bool
            plot FT window if True [True]
        '''
        self.do_xftf(kw=kw)
        self.do_xftr()
        plt.cla()
        plt.xlabel('wavenumber ($\AA^{-1}$)')
        plt.ylabel('$\chi$(k)')
        plt.title(self.name + ' in k-space and q-space')
        plt.xlim(right=self.group.k.max())
        plt.grid(which='major', axis='both')
        y = self.group.chi*self.group.k**kw
        plt.plot(self.group.k, y, label=self.name, color='C0')
        plt.plot(self.group.q, self.group.chiq_re, label='backtransform', color='C1')
        if win:
            plt.plot(self.group.k, self.group.kwin*y.max()*1.1, label='window', color='C8')
        plt.legend(loc='best', shadow=True)


    def triplot(self, kw=2):
        fig = plt.figure(tight_layout=True)
        gs = gridspec.GridSpec(2,2)

        self.prep()
        self.do_xftf(kw=kw)

        mu = fig.add_subplot(gs[0, :])
        mu.plot(self.group.energy, self.group.mu, label='$\mu(E)$', color='C0')
        mu.set_ylabel('$\mu(E)$')
        mu.set_xlabel('energy (eV)')

        chik = fig.add_subplot(gs[1, 0])
        #chik.set_xlim(left=0)
        y = self.group.chi*self.group.k**kw
        chik.plot(self.group.k, y, label='$\chi(k)$', color='C0')
        chik.set_ylabel(f'$\chi(k)$  ($\AA^{{-{kw}}}$)')
        chik.set_xlabel('wavenumber ($\AA^{-1}$)')

        chir = fig.add_subplot(gs[1, 1])
        chir.set_xlim(0,6)
        chir.plot(self.group.r, self.group.chir_mag, label='$|\chi(R)|$', color='C0')
        chir.set_ylabel(f"$|\chi(R)|$  ($\AA^{{-{kw+1}}}$)")
        chir.set_xlabel('wavenumber ($\AA^{-1}$)')

        fig.align_labels()
        plt.show()
        
    pe  = plot_xmu
    ps  = plot_signals
    pk  = plot_chi
    pr  = plot_chir
    pq  = plot_chiq
    pkq = plot_chikq


from collections.abc import Iterable
## grouping of Pandrosus objects for making purple plots
class Kekropidai():
    '''Simple wrapper around a group of Pandrosus objects to facilitate
    multiple data set plots in the manner of Athena's purple plot
    buttons.

    Attributes
    ----------
    groups : list of str
        list of Pandrosus groups for plotting
    name : str
        name of this collection
    rmax : float
        upper bound of R-space plot
      

    Methods
    -------
    add :
        add a single group or a list of groups to the Kekropidai object
    plot_xmu : 
        (alias = pe) overplot all the groups in energy
    plot_i0 :
        (alias = p0) overplot I0 for all the groups
    plot_chi :
        (alias = pk) overplot all the groups in k-space
    plot_chir :
        (alias = pr) overplot all the groups in R-space
    plot_chiq : 
        (alias = pq) overplot all the groups in q-space

    Examples
    --------

    >>> bunch = Kekropidai(name='My data')
    >>> bunch.add(data_set1)
    >>> bunch.add(data_set2)
    >>> bunch.add(data_set3)
    >>> bunch.plot_xmu()
    '''
    def __init__(self, name=None):
        self.groups = list()
        self.name   = name
        self.rmax   = 6

    def put(self, uidlist):
        for u in uidlist:
            this = Pandrosus()
            this.fetch(u)
            self.add(this)

    def merge(self):
        base = self.groups[0]
        ee = base.group.energy
        mm = base.group.mu
        for spectrum in self.groups[1:]:
            mu = numpy.interp(ee, spectrum.group.energy, spectrum.group.mu)
            mm = mm + mu
        mm = mm / len(self.groups)
        merge = Pandrosus()
        merge.put(ee, mm, 'merge')
        return(merge)
        
            
    def add(self, groups):
        if 'Pandrosus' in str(type(groups)):
            # this is a single group
            self.groups.append(groups)
            return()
        if isinstance(groups, Iterable):
            for item in groups:
                if 'Pandrosus' in str(type(item)):
                    self.groups.append(item)

    def plot_xmu(self, norm=False, flat=False, deriv=False):
        '''Overplot multiple data sets in energy.

        The default is to plot all data as raw mu(E).

        Parameters
        ----------
        norm :  bool
            plot normalized data [False]
        flat :  bool
            plot flattened data [False]
        deriv : bool
            plot derivative data [False]

        Setting deriv to True turns off flat and norm.

        Setting flat to True turns off norm.

        '''
        plt.cla()
        plt.xlabel(self.groups[0].xe)
        plt.ylabel('$\mu(E)$')
        plt.grid(which='major', axis='both')
        title = '$\mu$(E)'
        if self.name is not None:
            title = self.name
        if deriv is True:
            plt.title(f"Derivative of {title}")
        elif flat is True:
            plt.title(f"Flattened {title}")
        elif flat is True:
            plt.title(f"Normalized {title}")
        else:
            plt.title(f"{title}")
        for g in self.groups:
            g.prep()
            if deriv is True:
                plt.plot(g.group.energy, g.group.dmude, label=g.name)
            elif flat is True:
                plt.plot(g.group.energy, g.group.flat, label=g.name)
            elif norm is True:
                plt.plot(g.group.energy, g.group.norm, label=g.name)
            else:
                plt.plot(g.group.energy, g.group.mu, label=g.name)
        plt.legend(loc='best', shadow=True)

    def plot_i0(self):
        '''Overplot I0 in energy.
        '''
        plt.cla()
        plt.xlabel(self.groups[0].xe)
        plt.ylabel('$I_0$  (nA)')
        plt.grid(which='major', axis='both')
        plt.title('$I_0$')
        for g in self.groups:
            plt.plot(g.group.energy, g.group.i0, label=g.name)

        
        
    def plot_chi(self, kw=2, part=None):
        '''Overplot multiple data sets in k-space.

        Parameters
        ----------
        kw : int
            the k-weight to use for all plots [2]

        (The "part" argument is ignored.  It is there as a command
        line convenience.)

        '''
        plt.cla()
        plt.xlabel(self.groups[0].xk)
        plt.ylabel(f"$k^{{{kw}}}\cdot\chi(k)$  ($\AA^{{-{kw}}}$)")
        plt.grid(which='major', axis='both')
        title = 'EXAFS data'
        if self.name is not None:
            title = self.name + ' in k-space'
        plt.title(f"{title}")
        for g in self.groups:
            g.prep()
            y = g.group.chi*g.group.k**kw
            plt.plot(g.group.k, y, label=g.name)
        plt.legend(loc='best', shadow=True)
    plot_chik = plot_chi

    def plot_chir(self, kw=2, part='m'):
        '''Overplot multiple data sets in R-space.

        Parameters
        ----------
        kw : int
            the k-weight to use in all Fourier transforms [2]
        part : str
            the part of the complex FT to plot ['m']
            
        m = magnitude
        r = real part
        m = imaginary part
        p = phase
        '''
        plt.cla()
        plt.xlabel(self.groups[0].xr)
        plt.grid(which='major', axis='both')
        title = 'FT data'
        if self.name is not None:
            title = self.name + ' in R-space'
        if part.lower() == 'r':
            plt.title(f"Real part of {title}")
            plt.ylabel(f"RE[$\chi$(R)]  ($\AA^{{-{kw+1}}}$)")
        elif part.lower() == 'i':
            plt.title(f"Imaginary part of {title}")
            plt.ylabel(f"Im[$\chi$(R)]  ($\AA^{{-{kw+1}}}$)")
        elif part.lower() == 'p':
            plt.title(f"Phase of {title}")
            plt.ylabel(f"Phase[$\chi$(R)]")
        else:
            plt.title(f"Magnitude of {title}")
            plt.ylabel(f"|$\chi$(R)|  ($\AA^{{-{kw+1}}}$)")
            
        for g in self.groups:
            g.prep()
            g.do_xftf(kw=kw)
            if part.lower() == 'r':
                plt.plot(g.group.r, g.group.chir_re,  label=g.name)
            elif part.lower() == 'i':
                plt.plot(g.group.r, g.group.chir_im,  label=g.name)
            elif part.lower() == 'p':
                plt.plot(g.group.r, g.group.chir_pha, label=g.name)
            else:
                plt.plot(g.group.r, g.group.chir_mag, label=g.name)

        plt.xlim(right=self.rmax)
        plt.legend(loc='best', shadow=True)

    def plot_chiq(self, kw=2, part='r'):
        '''Overplot multiple data sets in backtransformed k-space.

        Parameters
        ----------
        kw : int
            the k-weight to use in all Fourier transforms [2]
        part : str
            the part of the complex FT to plot ['m']
            
        m = magnitude
        r = real part
        m = imaginary part
        p = phase

        '''
        plt.cla()
        plt.xlabel(self.groups[0].xk)
        plt.grid(which='major', axis='both')
        maxk = 0
        title = 'back-transformed data'
        if self.name is not None:
            title = self.name + ' in q-space'
        if part.lower() == 'r':
            plt.title(f"Real part of {title}")
            plt.ylabel(f"RE[$\chi$(q)]  ($\AA^{{-{kw}}}$)")
        elif part.lower() == 'i':
            plt.title(f"Imaginary part of {title}")
            plt.ylabel(f"Im[$\chi$(q)]  ($\AA^{{-{kw}}}$)")
        elif part.lower() == 'p':
            plt.title(f"Phase of {title}")
            plt.ylabel('Phase[$\chi$(q)]')
        else:
            plt.title(f"Magnitude of {title}")
            plt.ylabel(f"|$\chi$(q)|  ($\AA^{{-{kw}}}$)")
            
        for g in self.groups:
            g.prep()
            g.do_xftf(kw=kw)
            g.do_xftr()
            maxk = max([maxk, g.group.k.max()])
            if part.lower() == 'r':
                plt.plot(g.group.q, g.group.chiq_re,  label=g.name)
            elif part.lower() == 'i':
                plt.plot(g.group.q, g.group.chiq_im,  label=g.name)
            elif part.lower() == 'p':
                plt.plot(g.group.q, g.group.chiq_pha, label=g.name)
            else:
                plt.plot(g.group.q, g.group.chiq_mag, label=g.name)

        plt.xlim(right=maxk*1.1)
        plt.legend(loc='best', shadow=True)

    pe = plot_xmu
    p0 = plot_i0
    pk = plot_chi
    pr = plot_chir
    pq = plot_chiq

    
