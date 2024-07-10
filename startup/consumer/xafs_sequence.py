
import os
from matplotlib import get_backend

from BMM.larch_interface import Pandrosus, Kekropidai, plt

from slack import img_to_slack, post_to_slack
from tools import experiment_folder

import redis
rkvs = redis.Redis(host='xf06bm-ioc2', port=6379, db=0)

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
    
    def start(self, element=None, edge=None, folder=None, workspace=None, repetitions=0, mode='transmission', tossfile=None):
        self.ongoing = True
        self.uidlist = []
        self.panlist = []
        self.kek = Kekropidai()
        self.element = element
        self.edge = edge
        self.folder = folder
        self.workspace = workspace
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
        this.element, this.edge, this.db = self.element, self.edge, self.catalog
        if get_backend().lower() == 'agg':
            this.folder = experiment_folder(self.catalog, uid)
        else:
            this.folder = self.workspace
        this.fetch(uid, mode=self.mode)
        self.panlist.append(this)
        self.kek.add(this)
        if len(self.uidlist) != self.repetitions:
            if self.fig is not None:
                plt.close(self.fig.number)
            ok = self.merge()
            if ok == 1:
                if self.repetitions > 5 and len(self.uidlist) % 3 == 0:
                    if get_backend().lower() == 'agg':
                        post_to_slack('(Posting a plot every third scan in a sequence...)')
                        #tossfile = os.path.join(this.folder, 'snapshots', 'toss.png')
                        tossfile = os.path.join(experiment_folder(self.catalog, self.uidlist[0]), 'snapshots', 'toss.png')
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
        if get_backend().lower() != 'agg':
            self.fig.canvas.manager.window.setGeometry(2040, 865, 640, 552)
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
            if get_backend().lower() == 'agg':
                ## dossier should have already been written, thus the
                ## sequence number (i.e. the number of times a
                ## sequence of repetitions using the same file) should
                ## already be known.  This will align the sequence
                ## numbering of the live plot and triplot images with
                ## the sequence numbering of the dossier itself
                sequnumber = rkvs.get('BMM:dossier:seqnumber').decode('utf-8')
                if seqnumber is not None:
                    filename = filename.replace('.png', f'-{seqnumber:02d}.png')
                fname = os.path.join(experiment_folder(self.catalog, self.uidlist[0]), filename)
                self.fig.savefig(fname)
                name = self.catalog[self.uidlist[0]].metadata['start']['XDI']['Sample']['name']
                self.logger.info(f'saved XAFS summary figure {fname}')
                img_to_slack(fname, title=name, measurement='xafs')
        

