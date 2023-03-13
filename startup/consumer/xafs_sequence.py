
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
    (1) Post figure to Slack on some interval, for example when 
        scan_number % 3 == 1
    (2) Evaluate noise level in data, for instance as epsilon_R, establish 
        a criterion for leaving the repetition loop 
    (3) More & configurable plot types.  Some kind of representation of all 
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
            self.merge()
            if self.repetitions > 5 and len(self.uidlist) % 3 == 0:
                post_to_slack('(Posting a plot every third scan in a sequence...)')
                tossfile = os.path.join(this.folder, 'snapshots', 'toss.png')
                self.fig.savefig(tossfile)
                img_to_slack(tossfile)
                

    def merge(self):
        if len(self.uidlist) == 0:
            return
        elif len(self.uidlist) == 1:
            toplot = self.panlist[0]
        else:
            toplot = self.kek.merge()
        toplot.facecolor = (0.95, 0.95, 0.95)
        name = self.catalog[self.uidlist[0]].metadata['start']['XDI']['Sample']['name']
        if self.ongoing:
            toplot.title = f"Sequence: {name}  {len(self.uidlist)}/{self.repetitions}"
        else:
            toplot.title = f"Sequence ended: {name}  {len(self.uidlist)} scans"
        self.fig = toplot.triplot()
        self.fig.canvas.manager.window.setGeometry(1237, 856, 640, 584)


    def stop(self, filename):
        self.ongoing = False
        if self.fig is not None:
            plt.close(self.fig.number)
        #plt.close('all')
        self.merge()
        self.fig.savefig(filename)
        img_to_slack(filename)
        

