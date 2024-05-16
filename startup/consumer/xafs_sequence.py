
import os

from BMM.larch_interface import Pandrosus, Kekropidai, plt

from slack import img_to_slack, post_to_slack

class XAFSSequence():
    '''Class for managing the specific plotting chore required for an
    ongoing sequence of XAFS scans.  The concept is that the xafs()
    plan will issue messages to a kafka topic indicating where in a
    sequence of XAFS repetitions a measurement currently is. The data
    measured thus far will be summed and plotted as Pandrosus triplot.

    The allows the user to view merged data as each scan finishes,
    allowing determination of data quality and informed decision
    making about when a number of scans is enough.

    Future features
    ===============
    (1) Evaluate noise level in data, for instance as epsilon_R, establish 
        a criterion for leaving the repetition loop 
    (2) More & configurable plot types.  Some kind of representation of all 
        the views of the data, a la bluesky-widgets, maybe tabs

    '''
    ongoing  = False
    uidlist  = []
    panlist  = []
    catalog  = None
    element  = None
    edge     = None
    folder   = None
    repetitions  = 0
    mode     = 'transmission'
    tossfile = None
    kek      = None
    fig      = None
    
    def start(self, element=None, edge=None, folder=None, repetitions=0, mode='transmission', tossfile=None):
        self.ongoing = True
        self.uidlist = []
        self.panlist = []
        self.kek = Kekropidai()
        self.element = element
        self.edge = edge
        self.folder = folder
        self.repetitions = repetitions
        self.mode = mode
        self.tossfile = os.path.join(folder, 'snapshots', 'toss.png')
        #if self.fig is not None:
        #    plt.close(self.fig.number)
        
    def add(self, uid):
        if 'test' in self.mode:
            return
        if self.ongoing is not True:
            print('add called, but no sequence started')
            return
        self.uidlist.append(uid)
        this = Pandrosus()
        this.element, this.edge, this.folder, this.db = self.element, self.edge, self.folder, self.catalog
        this.fetch(uid, mode=self.mode)
        self.panlist.append(this)
        self.kek.add(this)
        if len(self.uidlist) != self.repetitions:
            if self.fig is not None:
                plt.close(self.fig.number)
            ok = self.merge()
            if ok == 1:
                if self.repetitions > 5 and len(self.uidlist) % 3 == 0:
                    post_to_slack('(Posting a plot every third scan in a sequence...)')
                    tossfile = os.path.join(this.folder, 'snapshots', 'toss.png')
                    self.fig.savefig(tossfile)
                    name = self.catalog[self.uidlist[0]].metadata['start']['XDI']['Sample']['name']
                    img_to_slack(tossfile, title=name, measurement='xafs')
                

    def merge(self):
        if len(self.uidlist) == 0:
            return 0
        elif len(self.uidlist) == 1:
            toplot = self.panlist[0]
        else:
            toplot = self.kek.merge()
        toplot.facecolor = (0.95, 0.95, 0.95)
        name = self.catalog[self.uidlist[0]].metadata['start']['XDI']['Sample']['name']
        if name == 'None': return 0
        if self.ongoing:
            toplot.title = f"Sequence: {name}  {len(self.uidlist)}/{self.repetitions}"
        else:
            toplot.title = f"Sequence ended: {name}  {len(self.uidlist)} scans"
        if len(toplot.group.energy) > 100:
            self.fig = toplot.triplot()
        else:
            self.fig = toplot.plot_xmu()
        self.fig.canvas.manager.window.setGeometry(1237, 856, 640, 584)
        return 1

    def stop(self, filename):
        self.ongoing = False
        if 'test' in self.mode:
            return
        if self.fig is not None:
            plt.close(self.fig.number)
        #plt.close('all')
        ok = self.merge()
        if ok == 1:
            self.fig.savefig(filename)
            name = self.catalog[self.uidlist[0]].metadata['start']['XDI']['Sample']['name']
            self.logger.info(f'saved XAFS summary figure {filename}')
            img_to_slack(filename, title=name, measurement='xafs')
        

