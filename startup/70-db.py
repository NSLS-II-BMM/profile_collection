from databroker import catalog
from databroker.queries import TimeRange

import numpy
import matplotlib.pyplot as plt
plt.ion()
import h5py

run_report(__file__, text='machine learning prototype')


## "these" has a list of 158 db records, need:
##
##  1. extract mu(E) v E       numpy.array(these['49e22093-2911-4047-8313-0062ff11cb72'].primary.read()['I0']) 
##  2. (mu(E) interpolate onto a fixed grid)
##  3. trans/fluor/ref         these['49e22093-2911-4047-8313-0062ff11cb72'].metadata['start']['XDI']['_mode']
##  4. tag mu(E) as good or bad
##  5. save to an hdf5 file


## persistance: https://scikit-learn.org/stable/modules/model_persistence.html#persistence-example


GRIDSIZE = 401

def extract_mu(clog=None, uid=None, mode='transmission', fig=None, ax=None, show_plot=True):
    try:
        primary = clog[uid].primary.read()
    except:
        print(f'could not read primary of {uid}')
        return None
    try:
        en = numpy.array(primary['dcm_energy'])
        if len(en) < GRIDSIZE/2:
            return None
        i0 = numpy.array(primary['I0'])
        if mode == 'transmission':
            signal = numpy.array(primary['It'])
            mu = numpy.log(abs(i0/signal))
        else:
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


def rationalize_mu(en, mu):
    '''Return energy and mu on a "rationalized" grid of 1000 equally spaced points
    '''
    ee=list(numpy.arange(float(en[0]), float(en[-1]), (float(en[-1])-float(en[0]))/GRIDSIZE))
    mm=numpy.interp(ee, en, mu)
    return(ee, mm)


def get_uid_list(mode='fluorescence'):
    if mode == 'verygood':
        startup = os.path.join(os.getenv('HOME'), '.ipython', 'profile_collection', 'startup')
        uidlist = os.path.join(startup, 'very_good_data')
        with open(uidlist, "r") as f:
            uidstrings = f.read()
        these = uidstrings.split('\n')
        these = catalog.search({"uid": {"$in": these}})
    else:
        allbmm = catalog['bmm']
        ## xafs scans use scan_nd, linescans use rel_scan
        query = {'plan_name': 'scan_nd'}
        search_results = allbmm.search(query)
        ## this is a weekend of measuring decent data with a long stretch of failure for the 0 part of training set
        timequery = TimeRange(since='2020-07-09', until='2020-13-09')
        these=search_results.search(timequery)
    return these

def process_catalog(mode='fluorescence'):

    #fig = plt.figure()
    #ax = fig.add_subplot(1,1,1)
    fig, ax = plt.subplots(1,1)
    plt.show(False)
    plt.draw()
    fig.canvas.flush_events()
    these = get_uid_list(mode)
    #list(catalog['bmm'])
    print(f'Scoring {len(these)} records')

    h5file = f'/home/xf06bm/{mode}_training_set.hdf5'
    try:
        os.remove(h5file)
    except:
        pass
    f = h5py.File(h5file, 'w')

    count = 0
    for uid in list(these):
        count += 1
        ret = extract_mu(clog=these, uid=uid, mode=mode, fig=fig, ax=ax, show_plot=True)
        if ret is None:
            print(f'skipping {uid}, not data or too short')
        else:
            ee, mm = rationalize_mu(*ret)
            print(f'{count}  {len(ee)}   {uid}   {mode}')
            if len(ee) < GRIDSIZE:
                continue
            elif len(ee) > GRIDSIZE:
                ee = ee[:-1]
                mm = mm[:-1]
            grp = f.create_group(uid)
            grp.create_dataset("energy", data=ee)
            grp.create_dataset("mu", data=mm)
            action = input('\n' + bold_msg('1= good  2=bad  q=quit > '))
            if action.lower() == 'q':
                plt.close(fig)
                return()
            else:
                grp.attrs['score'] = action.lower()
    plt.close(fig)
    
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

from sklearn.model_selection import train_test_split
from joblib import dump, load

def do_training():
    scores = list()
    data = list()
    for h5file in ('/home/xf06bm/fluorescence_training_set.hdf5', '/home/xf06bm/transmission_training_set.hdf5'):
        f = h5py.File(h5file,'r')
        for uid in f.keys():
            score = int(f[uid].attrs['score'])
            mu = list(f[uid]['mu'])
            scores.append(score)
            data.append(mu)

    X_train, X_test, y_train, y_test = train_test_split(data, scores, random_state=0)
    #clf=KNeighborsClassifier(n_neighbors=1)
    clf=RandomForestClassifier(random_state=0)
    #clf = MLPClassifier(solver='lbfgs', alpha=1e-5, hidden_layer_sizes=(5, 2), random_state=1)
    
    clf.fit(X_train, y_train)
    dump(clf, '/home/xf06bm/data_recognition_model.joblib')
    return(clf, X_test, y_test)


def test_data(uid, clf):
    this = db.v2[uid]
    mode = this.metadata['start']['XDI']['_mode'][0]
    element = this.metadata['start']['XDI']['Element']['symbol']
    i0 = this.primary.read()['I0']
    en = this.primary.read()['dcm_energy']
    if mode == 'transmission':
        it = this.primary.read()['It']
        mu = numpy.log(abs(i0/it))
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
    e,m = rationalize_mu(en, mu)
    if len(m) > GRIDSIZE:
        m = m[:-1]
    #print(clf.predict([m]))
    return(clf.predict([m])[0])
    
try:
    clf = load('/home/xf06bm/data_recognition_model.joblib')
except:
    pass
