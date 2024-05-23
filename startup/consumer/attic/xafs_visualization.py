import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

from BMM.larch_interface import Pandrosus, Kekropidai #, plt

#plt.rcParams['figure.figsize'] = [12.8, 9.6]
plt.rcParams["figure.titlesize"] = 'x-large'

def tabbed_plot(pw=None, uid=None, element=None, edge=None, folder=None, mode='transmission', catalog=None):
    '''Tabbed plots using https://github.com/superjax/plotWindow

    This is exactly what I want, but seems to re-introduce threads confusion ... ¯\_(ツ)_/¯
    '''
    this = Pandrosus()
    this.element, this.edge, this.folder, this.db = element, edge, folder, catalog
    this.name = catalog[uid].metadata['start']['XDI']['Sample']['name']
    this.reuse = False
    this.fetch(uid, mode=mode)
    # fig, ax = plt.subplots()
    # unit_mue(ax, this)
    # plt.close()
    # pw.addPlot('mu(E)', fig)
    # fig, ax = plt.subplots()
    # unit_mue(ax, this)
    # plt.close()
    # pw.addPlot('signals', fig)
    pw.addPlot('mu(E)',     this.plot_xmu())
    pw.addPlot('reference', this.plot_reference())
    pw.addPlot('signals',   this.plot_signals())
    pw.addPlot('chi(k)',    this.plot_chi())
    pw.addPlot('chi(R)',    this.plot_chir(win=False))
    
    pw.show()


def unit_mue(ax, this):
    g = this.group
    ax.plot(g.energy, g.mu, label='$\mu(E)$', color='C0')
    ax.set_ylabel('$\mu(E)$')
    ax.set_xlabel('energy (eV)')
    ax.grid(which='major', axis='both')
    ax.legend(loc='best', shadow=True)

def unit_signals(ax, this):
    g = this.group
    max_xmu    = g.mu.max()
    max_i0     = g.i0.max()
    max_signal = this.signal.max()
    ax.plot(g.energy, g.mu, label='$\mu(E)$')
    ax.plot(g.energy, g.i0*max_xmu/max_i0, label='$I_0$')
    ax.plot(g.energy, this.signal*max_xmu/max_signal, label='signal')
    ax.set_ylabel('$\mu(E)$')
    ax.set_xlabel('energy (eV)')
    ax.grid(which='major', axis='both')
    ax.legend(loc='best', shadow=True)

def unit_reference(ax, this):
    g = this.group
    ax.plot(g.energy, g.flat, label='norm. $\mu(E)$')
    b=Pandrosus()
    b.put(g.energy, g.reference, 'reference')
    b.prep()
    ax.plot(b.group.energy, b.group.flat, label='reference')
    ax.set_ylabel('normalized $\mu(E)$')
    ax.set_xlabel('energy (eV)')
    ax.grid(which='major', axis='both')
    ax.legend(loc='best', shadow=True)
    

def unit_chik(ax, this, kw):
    g = this.group
    ax.set_xlabel(this.xk)
    ax.set_ylabel(f"$k^{kw}\cdot\chi(k)$  ($\AA^{{-{kw}}}$)")
    ax.grid(which='major', axis='both')
    y = g.chi*g.k**kw
    ax.plot(g.k, y, label='$\chi(k)$')
    ax.plot(g.k, g.kwin*y.max()*1.1, label='window', color='C8')
    ax.legend(loc='best', shadow=True)

def unit_chir(ax, this, kw):
    g = this.group
    ax.set_xlabel(this.xr)
    ax.set_ylabel(f"$|\chi(R)|$  ($\AA^{{-{kw+1}}}$)")
    ax.grid(which='major', axis='both')
    ax.plot(g.r, g.chir_mag, label='$|\chi(R)|$')
    ax.legend(loc='best', shadow=True)
    ax.set_xlim(right=7)
    
    
def gridded_plot(uid=None, element=None, edge=None, folder=None, mode='transmission', catalog=None):
    '''
    Make a plot of an XAFS scan that looks like this:

      +----------------+----------------+
      |                |                |
      |    mu(E)       |    mu(E) + IO  |
      |                |    + signal    |
      |                |                |
      +----------------+----------------+
      |                |                |
      |    chi(k)      |    mu(E) +     |
      |                |    reference   |
      |                |                |
      +----------------+----------------+
      |                |                |
      |    chi(R)      |                |
      |                |                |
      |                |                |
      +----------------+----------------+
    '''
    this = Pandrosus()
    this.element, this.edge, this.folder, this.db = element, edge, folder, catalog
    this.reuse = False
    this.fetch(uid, mode=mode)
    this.name = catalog[uid].metadata['start']['XDI']['Sample']['name']
    n = catalog[uid].metadata['start']['BMM_kafka']['count']
    repetitions = catalog[uid].metadata['start']['BMM_kafka']['repetitions']
    count = f'-- scan {n} of {repetitions}'
    this.name = this.name + count
    g = this.group

    plt.close('XAFS grid')
    
    fig = plt.figure(num='XAFS grid', tight_layout=True)
    fig.canvas.manager.window.setGeometry(1877, 378, 1200, 1062)
    fig.suptitle(this.name)
    gs = gridspec.GridSpec(3,2)

    mu = fig.add_subplot(gs[0, 0])
    unit_mue(mu, this)

    sig = fig.add_subplot(gs[0, 1])
    unit_signals(sig, this)

    kw = 2
    chik = fig.add_subplot(gs[1, 0])
    unit_chik(chik, this, kw)

    ref = fig.add_subplot(gs[1, 1])
    unit_reference(ref, this)

    chir = fig.add_subplot(gs[2, 0])
    unit_chir(chir, this, kw)

    fig.align_labels()
    fig.canvas.manager.show()
    #plt.show()
    fig.canvas.manager.window.raise_()
    fig.canvas.flush_events()
    
