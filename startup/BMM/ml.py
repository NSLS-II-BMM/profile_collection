from databroker import catalog
from databroker.queries import TimeRange

import numpy
import matplotlib.pyplot as plt
#plt.ion()
import h5py
import os

#from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
#from sklearn.neural_network import MLPClassifier

from sklearn.model_selection import train_test_split
from joblib import dump, load

from bluesky_queueserver.manager.profile_tools import set_user_ns

# from IPython import get_ipython
# user_ns = get_ipython().user_ns

class BMMDataEvaluation():
    '''A very simple machine learning model for recognizing when an XAS
    scan goes horribly awry.

    '''
    def __init__(self):
        self.GRIDSIZE = 401
        self.clf      = None
        self.X        = None
        self.y        = None
        self.folder   = os.path.join(os.getenv('HOME'), '.ipython', 'profile_collection', 'startup', 'ML')
        self.model    = os.path.join(self.folder, 'data_evaluation.joblib')
        self.hdf5     = [os.path.join(self.folder, 'fluorescence_training_set.hdf5'),
                         os.path.join(self.folder, 'transmission_training_set.hdf5'),
                         os.path.join(self.folder, 'verygood_training_set.hdf5'),]
        self.good_emoji = ':heavy_check_mark:'
        self.bad_emoji  = ':heavy_multiplication_x:'
        if os.path.isfile(self.model):
            self.clf = load(self.model)
        
    @set_user_ns
    def extract_mu(self, clog=None, uid=None, mode='transmission', fig=None, ax=None, show_plot=True, user_ns=None):
        '''Slurp a record from Databroker, contruct transmission or
        fluorescence XAS, and optionally make a plot.

        Parameters
        ----------
        clog : catalog
            catalog in which to find the record
        uid : str
            identifier string for the record in the catalog
        mode : str
            fluorescence or transmission
        fig, ax : matplotlib fig and ax
            figure and axes iof the plot
        show_plot : bool
            True to show plot
        '''
        try:
            primary = clog[uid].primary.read()
        except:
            print(f'could not read primary of {uid}')
            return None
        try:
            en = numpy.array(primary['dcm_energy'])
            if len(en) < self.GRIDSIZE/2:
                return None
            i0 = numpy.array(primary['I0'])
            if mode == 'transmission' or mode == 'verygood':
                signal = numpy.array(primary['It'])
                mu = numpy.log(abs(i0/signal))
            # elif mode == 'xs':
            #     BMMuser, db = user_ns['BMMuser'], user_ns['db']
            #     t = db[-1].table()
            #     el = BMMuser.element
            #     dtc1 = numpy.array(t[el+'1'])
            #     dtc2 = numpy.array(t[el+'2'])
            #     dtc3 = numpy.array(t[el+'3'])
            #     dtc4 = numpy.array(t[el+'4'])
            #     signal = dtc1+dtc2+dtc3+dtc4
            #     mu = signal/i0
            else:
                # BMMuser = user_ns['BMMuser']
                # dtc1 = numpy.array(primary[BMMuser.dtc1])
                # dtc2 = numpy.array(primary[BMMuser.dtc2])
                # dtc3 = numpy.array(primary[BMMuser.dtc3])
                # dtc4 = numpy.array(primary[BMMuser.dtc4])
                
                if clog[uid].metadata['start']['XDI']['Element']['symbol'] == 'Ti':
                    dtc1 = numpy.array(primary['DTC2_1'])
                    dtc2 = numpy.array(primary['DTC2_2'])
                    dtc3 = numpy.array(primary['DTC2_3'])
                    dtc4 = numpy.array(primary['DTC2_4'])
                elif clog[uid].metadata['start']['XDI']['Element']['symbol'] == 'Ce':
                    dtc1 = numpy.array(primary['DTC3_1'])
                    dtc2 = numpy.array(primary['DTC3_2'])
                    dtc3 = numpy.array(primary['DTC3_3'])
                    dtc4 = numpy.array(primary['DTC3_4'])
                elif clog[uid].metadata['start']['XDI']['Element']['symbol'] == 'Fe':
                    dtc1 = numpy.array(primary['DTC1'])
                    dtc2 = numpy.array(primary['DTC2'])
                    dtc3 = numpy.array(primary['DTC3'])
                    dtc4 = numpy.array(primary['DTC4'])
                signal = dtc1+dtc2+dtc3+dtc4
                mu = signal/i0
            if show_plot:
                plt.cla()
                ax.plot(en, mu)
                fig.canvas.draw()
                fig.canvas.flush_events()
            return(en, mu)
        except Exception as exc:
            print(exc)
            return None


    def rationalize_mu(self, en, mu):
        '''Return energy and mu on a "rationalized" grid of equally spaced points.  See slef.GRIDSIZE
        '''
        ee=list(numpy.arange(float(en[0]), float(en[-1]), (float(en[-1])-float(en[0]))/self.GRIDSIZE))
        mm=numpy.interp(ee, en, mu)
        return(ee, mm)


    def get_uid_list(self, mode='fluorescence'):
        '''Gather a curated list of uids to be used in the training set
        '''
        if mode == 'verygood':
            uidlist = os.path.join(self.folder, 'very_good_data')  ## the "Elements" standards set
            with open(uidlist, "r") as f:
                uidstrings = f.read()
            these = uidstrings.split('\n')
            these = catalog['bmm'].search({"uid": {"$in": these[:-1]}})
        else:
            ## xafs scans use scan_nd, linescans use rel_scan, timescans use count, areascans use grid_scan
            search_results = catalog['bmm'].search({'plan_name': 'scan_nd'})
            ## this is a weekend of measuring decent data with a long stretch of failure for the 0 part of the training set
            timequery = TimeRange(since='2020-07-09', until='2020-07-13', timezone="US/Eastern")
            these=search_results.search(timequery)
        return these

    def process_catalog(self, mode='fluorescence'):
        '''Score each entry in the training set.  This will gather a list of
        uids, plot them one-by-one, and solicit a 1/0 score for each
        one.  The properly interpolated and scored data will be stored
        in an HDF5 file for later use.

        '''
        shplot, fig, ax = False, False, False
        if mode != 'verygood':
            fig, ax = plt.subplots(1,1)
            plt.show(False)
            plt.draw()
            fig.canvas.flush_events()
            shplot = True
        these = self.get_uid_list(mode)
        #list(catalog['bmm'])
        print(f'Scoring {len(these)} records')

        h5file = os.path.join(self.folder, f'{mode}_training_set.hdf5')
        try:
            os.remove(h5file)
        except:
            pass
        f = h5py.File(h5file, 'w')

        count = 0
        for uid in list(these):
            count += 1
            ret = self.extract_mu(clog=these, uid=uid, mode=mode, fig=fig, ax=ax, show_plot=False)
            if ret is None:
                print(f'skipping {uid}, not data or too short')
            else:
                ee, mm = self.rationalize_mu(*ret)
                print(f'{count}  {len(ee)}   {uid}   {mode}')
                if len(ee) < self.GRIDSIZE:
                    continue
                elif len(ee) > self.GRIDSIZE:
                    ee = ee[:-1]
                    mm = mm[:-1]
                grp = f.create_group(uid)
                grp.create_dataset("energy", data=ee)
                grp.create_dataset("mu", data=mm)
                if mode == 'verygood':
                    grp.attrs['score'] = 1
                else:
                    action = input('\n' + bold_msg('1= good  2=bad  q=quit > '))
                    if action.lower() == 'q':
                        plt.close(fig)
                        return()
                    else:
                        grp.attrs['score'] = action
        plt.close(fig)

    def train(self):
        '''Using all the hdf5 files of interpolated, scored data, create the
        evaluation model, saving it to a joblib dump file.

        '''
        scores = list()
        data = list()
        for h5file in self.hdf5:
            if os.path.isfile(h5file):
                print(f'reading data from {h5file}')
                f = h5py.File(h5file,'r')
                for uid in f.keys():
                    score = int(f[uid].attrs['score'])
                    mu = list(f[uid]['mu'])
                    scores.append(score)
                    data.append(mu)

        X_train, X_test, y_train, y_test = train_test_split(data, scores, random_state=0)
        print("training model...")
        #self.clf=KNeighborsClassifier(n_neighbors=1)
        self.clf=RandomForestClassifier(random_state=0)
        #self.clf = MLPClassifier(solver='lbfgs', alpha=1e-5, hidden_layer_sizes=(5, 2), random_state=1)
        
        self.clf.fit(X_train, y_train)
        dump(self.clf, self.model)
        print(f'wrote model to {self.model}')
        self.X = X_test
        self.y = y_test
        return()

    def score(self):
        '''Thin wrapper around the classifier object's score method.'''
        return(self.clf.score(self.X, self.y))

    @set_user_ns
    def evaluate(self, uid, mode=None, user_ns=None):
        '''Perform an evaluation of a measurement.  The data will be
        interpolated onto the same grid used for the training set,
        then get subjected to the model.  This returns a tuple with
        the score (1 or 0) and the Slack-appropriate value (green
        check or red cross).

        Parameters
        ----------
        uid : str
            uid of data to be evaluated
        mode : bool
            when not None, used to specify fluorescence or transmission (for a data set that has both)

        '''
        if mode == 'xs':
            BMMuser, db = user_ns['BMMuser'], user_ns['db']
            t = db[-1].table()
            el = BMMuser.element
            i0 = numpy.array(t['I0'])
            en = numpy.array(t['dcm_energy'])
            dtc1 = numpy.array(t[el+'1'])
            dtc2 = numpy.array(t[el+'2'])
            dtc3 = numpy.array(t[el+'3'])
            dtc4 = numpy.array(t[el+'4'])
            signal = dtc1+dtc2+dtc3+dtc4
            mu = signal/i0
        else:
            db = user_ns['db']
            this = db.v2[uid]
            if mode is None:
                mode = this.metadata['start']['XDI']['_mode'][0]
            element = this.metadata['start']['XDI']['Element']['symbol']
            i0 = this.primary.read()['I0']
            en = this.primary.read()['dcm_energy']
            if mode == 'transmission':
                it = this.primary.read()['It']
                mu = numpy.log(abs(i0/it))
            elif mode == 'reference':
                it = this.primary.read()['It']
                ir = this.primary.read()['Ir']
                mu = numpy.log(abs(it/ir))
            else:
                if element in str(this.primary.read()['vor:vor_names_name3'][0].values):
                    signal = this.primary.read()['DTC1'] + this.primary.read()['DTC2'] + this.primary.read()['DTC3'] + this.primary.read()['DTC4']
                elif element in str(this.primary.read()['vor:vor_names_name15'][0].values):
                    signal = this.primary.read()['DTC2_1'] + this.primary.read()['DTC2_2'] + this.primary.read()['DTC2_3'] + this.primary.read()['DTC2_4']
                elif element in str(this.primary.read()['vor:vor_names_name19'][0].values):
                    signal = this.primary.read()['DTC3_1'] + this.primary.read()['DTC3_2'] + this.primary.read()['DTC3_3'] + this.primary.read()['DTC3_4']
                else:
                    print('cannot figure out fluorescence signal')
                    #print(f'vor:vor_names_name3 {}')
                    return()
                mu = signal/i0
        e,m = self.rationalize_mu(en, mu)
        if len(m) > self.GRIDSIZE:
            m = m[:-1]
        result = self.clf.predict([m])[0]
        if result == 1:
            return(result, self.good_emoji)
        else:
            return(result, self.bad_emoji)
    
    
