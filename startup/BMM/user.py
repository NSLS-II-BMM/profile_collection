import sys, os, re, shutil, socket, datetime
from distutils.dir_util import copy_tree
import json, pprint, copy

from bluesky_queueserver.manager.profile_tools import set_user_ns

# from IPython import get_ipython
# user_ns = get_ipython().user_ns

from BMM.functions import BMM_STAFF
from BMM.functions import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.gdrive    import make_gdrive_folder
from BMM.logging   import BMM_user_log, BMM_unset_user_log, report
from BMM.periodictable import edge_energy

#run_report(__file__, text='user definitions and start/stop an experiment')

## sort of a singleton, see http://code.activestate.com/recipes/66531/
class Borg:
    __shared_state = {}
    def __init__(self):
        self.__dict__ = self.__shared_state      

class BMM_User(Borg):
    '''A class for managing the user interaction at BMM.

    Experiment attributes
    ---------------------
    DATA : str
        path to folder containing data
    prompt : bool
        True prompt at beginning of plans
    final_log_entry : bool
        True write log entries during plan cleanup
    date : str
        start date of experiment as YYYY-MM-DD
    gup : str
        GUP number
    saf : str
        SAF number
    cycle : str
        NSLS-II ops cycle (e.g. '2020-1')
    name : str
        full name of PI
    staff : bool
        True if a staff experiment
    macro_dryrun : bool
        True will replace a call to xafs() with a sleep
    macro_sleep : float
        the length of that sleep
    motor_fault : str of None
        normally None, set to a string when motors are found in a fault state
    detector : int
        4=4-element detector, 1=1-element detector
    use_pilatus : bool
        True make a folder for Pilatus images
    echem : bool
        True is doing electrochemistry with the BioLogic
    echem_remote : str
        mounted path to cifs share on ws3
    instrument : str
        name of sample instrument, e.g. "sample wheel" or "glancing angle stage"

    Current plot attributes
    -----------------------
    motor : str
        fast motor in current plot
    motor2 : str
        slow motor in current plot
    fig : matplotlib.figure.Figure
        figure object of current plot
    ax : matplotlib.axes._subplots.AxisSubplot
        axis object of current plot
    x : int
        plucked-upon X coordinate
    y : int
        plucked-upon Y coordinate


    Energy scan control attributes, default values
    ----------------------------------------------
    pds_mode : str
        photon delivery system mode (A, B, C, D, E, F, XRD)
    bounds : list of float or str
        list of energy or k scan boundaries
    steps : list of float or str
        list of energy ot k steps
    times : list of float or str
        list of integration times
    folder : str
        data folder
    filename : str
        output data file stub
    experimenters : str
        names of experimenters
    e0 : float
        edge energy, reference for bounds
    element : str
        absorbing element
    edge : str
        absorption edge
    sample : str
        sample composition or stoichiometry
    prep : str
        how sample was prepared for measurement
    comment : str
        anything else of interest about the sample
    nscans : int
        number of scan repititions
    start : int
        starting scan number
    lims : bool
        perform LIMS chores (snapshots, XRF spectra, dossier)
    snapshots : bool
        take snapshots
    usbstick : bool
        rewrite USB-stick-safe filenames
    rockingcurve : bool
        do a rocking curve scan at the pseudo-channel-cut energy
    htmlpage : bool
        write dossier
    bothways : bool
        measuring in both directions on mono
    channelcut : bool
        measuring in pseudo-channel-cut mode
    ththth : bool
        measuring with the Si(333) reflection
    mode : str
        in-scan plotting mode

    Single energy time scan attributes, default values
    --------------------------------------------------
    npoints : int
        number of time points
    dwell : float
        dwell time at each time step
    delay : float
        delay between time steps

    Methods for public use
    ----------------------
    start_experiment(self, name=None, date=None, gup=0, saf=0)

    end_experiment(self, force=False)

    show_experiment(self)
    '''
    def __init__(self):
        ## experiment attributes
        self.DATA            = os.path.join(os.getenv('HOME'), 'Data', 'bucket') + '/'
        self.prompt          = True
        self.final_log_entry = True
        self.date            = ''
        self.gup             = 0
        self.saf             = 0
        cnum = (0,1,1,1,1,2,2,2,2,3,3,3,3)[int(datetime.datetime.now().strftime("%m"))]
        self.cycle           = f'{datetime.datetime.now().strftime("%Y")}-{cnum}'
        self.host            = socket.gethostname()
        self.use_pilatus     = False
        self.name            = None
        self.staff           = False
        #self.read_foils      = None
        self.read_rois       = None
        self.user_is_defined = False
        self.motor_fault     = None
        self.detector        = 4
        self.echem           = False
        self.echem_remote    = None
        self.use_slack       = True
        self.slack_channel   = None
        self.trigger         = False
        self.instrument      = ''
        self.url             = False
        self.doi             = False
        self.cif             = False
        
        self.macro_dryrun    = False  ############################################################################
        self.macro_sleep     = 2      # These are used to help macro writers test motor motions in their macros. #
                                      # When true, this will turn xafs scans, line scans, change_edge, etc into  #
                                      # a sleep.  This allows visual inspection of motor movement between scans. #
                                      ############################################################################

        self.readout_mode    = 'struck' ## 'analog'  'xspress3'  'digital'
        self.rois            = list(),
        self.roi_channel     = None   ##################################################################
        self.roi1            = 'ROI1' # in 76-edge.py, the ROI class is defined for managing changes   #
        self.roi2            = 'ROI2' # of configured detector channels. the names of the channels are #
        self.roi3            = 'ROI3' # are stored here for use in the various calls to DerivedPlot    #
        self.roi4            = 'ROI4' # and for writing column labels to output files                  #
        self.dtc1            = 'DTC1' ##################################################################
        self.dtc2            = 'DTC2'
        self.dtc3            = 'DTC3'
        self.dtc4            = 'DTC4'

        self.xs1             = None
        self.xs2             = None
        self.xs3             = None
        self.xs4             = None
        self.xs8             = None
        self.xschannel1      = None
        self.xschannel2      = None
        self.xschannel3      = None
        self.xschannel4      = None
        self.xschannel8      = None
                
        ## current plot attributes    #######################################################################
        self.motor    = None          # these are used to keep track of mouse events on the plotting window #
        self.motor2   = None          # see 70-linescans.py, and 71-areascan.py                             #
        self.fig      = None          #######################################################################
        self.ax       = None
        self.x        = None
        self.y        = None
        self.prev_fig = None
        self.prev_ax  = None
        #self.all_figs = []

        ## scan control attributes
        self.pds_mode      = None
        self.bounds        = [-200, -30, 15.3, '14k']  ## scan grid parameters
        self.steps         = [10, 0.5, '0.05k']
        self.times         = [0.5, 0.5, '0.25k']
        self.folder        = os.environ.get('HOME')+'/Data/'
        self.filename      = 'data.dat'
        self.experimenters = ''
        self.e0            = None
        self.element       = None
        self.edge          = 'K'
        self.sample        = ''
        self.prep          = ''
        self.comment       = ''
        self.nscans        = 1
        self.start         = 0
        self.inttime       = 1
        self.snapshots     = True
        self.usbstick      = True
        self.rockingcurve  = False
        self.htmlpage      = True
        self.bothways      = False
        self.channelcut    = True
        self.ththth        = False
        self.lims          = True
        self.mode          = 'transmission'
        self.npoints       = 0     ###########################################################################
        self.dwell         = 1.0   ## parameters for single energy absorption detection, see 72-timescans.py #
        self.delay         = 0.1   ###########################################################################
        
        ## mono acceleration control
        self.acc_fast      = 0.25  ###########################################################################
        self.acc_slow      = 0.5   # after decreasing Bragg acceleration time, Bragg axis would occasionally #
                                   # freeze. these are used to try to mitigate this problem                  #
                                   ###########################################################################
        
        self.bender_xas    = 212225  #####################################################################
        self.bender_xrd    = 112239  # approximate values for M2 bender for focusing at XAS & XRD tables #
        self.bender_margin = 30000   #####################################################################

        self.filter_state  = 0

    def to_json(self, filename=None):
        ## avoid this: TypeError: can't pickle _thread.RLock objects
        save = [self.xschannel1, self.xschannel2, self.xschannel3, self.xschannel4, self.xschannel8, self.ax, self.fig, self.motor]
        self.xschannel1, self.xschannel2, self.xschannel3, self.xschannel4, self.xschannel8, self.ax, self.fig, self.motor = [None, ] * 8
        d = copy.deepcopy(self.__dict__)
        self.xschannel1, self.xschannel2, self.xschannel3, self.xschannel4, self.xschannel8, self.ax, self.fig, self.motor = save
        for k in ('prev_fig', 'prev_ax', 'user_is_defined',
                  'xschannel1', 'xschannel2', 'xschannel3', 'xschannel4', 'xschannel8',
                  'motor', 'motor2'):
            del d[k]
        if filename is None:
            print(json.dumps(d, indent=4))
        else:
            with open(filename, 'w') as outfile:
                json.dump(d, outfile, indent=4)
            print(f'wrote BMMuser state to {filename}')

    def verify_roi(self, xs, el, edge):
        print(bold_msg(f'Attempting to set ROIs for {el} {edge} edge'))
        try:
            ## if el is not one of the "standard" 12 ROI sets, insert it into xs.slots[12]/index 13
            if xs.check_element(el, edge):
                forceit = False
                if el.capitalize() in ('Pb', 'Pt') and edge.capitalize() in ('L2', 'L1'):
                    forceit = True # Pb and Pt L3 edges are "standard" ROIs
                if el not in xs.slots or forceit:
                    startup_dir = get_ipython().profile_dir.startup_dir
                    with open(os.path.join(startup_dir, 'rois.json'), 'r') as fl:
                        js = fl.read()
                    allrois = json.loads(js)
                    xs.set_rois()
                    xs.slots[14] = el
                    for ch in range(1,5):
                        xs.set_roi_channel(channel=ch, index=15, name=f'{el.capitalize()}{ch}',
                                           low =allrois[el.capitalize()][edge.lower()]['low'],
                                           high=allrois[el.capitalize()][edge.lower()]['high'])

                xs.measure_roi()
            else:
                report(f'No tabulated ROIs for the {el.capitalize()} {edge.capitalize()} edge.  Not setting ROIs for mesaurement.',
                       level='bold', slack=True)
        except Exception as E:
            print(error_msg(E))

            
    @set_user_ns
    def from_json(self, filename, *, user_ns):
        rkvs = user_ns['rkvs']
        if os.path.isfile(filename):
            with open(filename, 'r') as jsonfile:
                config = json.load(jsonfile)
            for k in config.keys():
                setattr(self, k, config[k])
            user_ns['rois'].trigger = True
        rkvs.set('BMM:pds:edge',        str(config['edge']))
        rkvs.set('BMM:pds:element',     str(config['element']))
        rkvs.set('BMM:pds:edge_energy', edge_energy(config['element'], config['edge']))
            
            
    def show(self, scan=False):
        '''
        Show the current contents of the BMMuser object
        '''
        print('Experiment attributes:')
        for att in ('DATA', 'prompt', 'final_log_entry', 'date', 'gup', 'saf', 'name', 'staff', 
                    'read_rois', 'user_is_defined', 'pds_mode', 'macro_dryrun', 'macro_sleep', 'motor_fault',
                    'detector', 'use_pilatus', 'echem', 'echem_remote'):
            print('\t%-15s = %s' % (att, str(getattr(self, att))))

        print('\nROI control attributes:')
        for att in ('roi_channel', 'roi1', 'roi2', 'roi3', 'roi4', 'dtc1', 'dtc2', 'dtc3', 'dtc4', 'xs1', 'xs2', 'xs3', 'xs4',
                    'xschannel1', 'xschannel2', 'xschannel3', 'xschannel4'):
            print('\t%-15s = %s' % (att, str(getattr(self, att))))

        print('\nCurrent plot attributes:')
        for att in ('motor', 'motor2', 'fig', 'ax', 'x', 'y'):
            print('\t%-15s = %s' % (att, str(getattr(self, att))))

        print('\nMono acceleration and bender attributes:')
        for att in ('acc_fast', 'acc_slow', 'bender_xas', 'bender_xrd', 'bender_margin'):
            print('\t%-15s = %s' % (att, str(getattr(self, att))))

        if scan:
            print('\nScan control attributes:')
            for att in ('pds_mode', 'bounds', 'steps', 'times', 'folder', 'filename',
                        'experimenters', 'e0', 'element', 'edge', 'sample', 'prep', 'comment', 'nscans', 'start', 'inttime',
                        'snapshots', 'usbstick', 'rockingcurve', 'htmlpage', 'bothways', 'channelcut', 'ththth', 'mode', 'npoints',
                        'dwell', 'delay'):
                print('\t%-15s = %s' % (att, str(getattr(self, att))))

    @set_user_ns
    def new_experiment(self, folder, gup=0, saf=0, name='Betty Cooper', use_pilatus=False, echem=False, *, user_ns=None):
        '''
        Do the work of prepping for a new experiment.  This will:
          * Create a folder, if needed, and set the DATA variable
          * Set up the experimental log, creating an experiment.log file, if needed
          * Write templates for scan.ini and macro.py, if needed
          * Make the snapshots, dossier, and prj folders
          * Set the GUP and SAF numbers as metadata

        Parameters
        ----------
        folder : str
            data destination
        gup : str
            GUP number
        saf : str
            SAF number
        name : str
            name of PI
        '''

        step = 1
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## make folder
        if not os.path.isdir(folder):
            os.makedirs(folder)
            print('%2d. Created data folder:               %-75s' % (step, folder))
        else:
            print('%2d. Found data folder:                 %-75s' % (step, folder))
        imagefolder = os.path.join(folder, 'snapshots')
        if not os.path.isdir(imagefolder):
            os.mkdir(imagefolder)
            print('    Created snapshot folder:           %-75s' % imagefolder)
        else:
            print('    Found snapshot folder:             %-75s' % imagefolder)

        user_ns['DATA'] = folder + '/'
        self.DATA = folder + '/'
        self.folder = folder + '/'
        try:
            user_ns['wmb'].folder = folder + '/'
        except:
            pass
        try:
            wmb.folder = self.folder
        except:
            pass
        step += 1

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## setup logger
        BMM_user_log(os.path.join(folder, 'experiment.log'))
        print('%2d. Set up experimental log file:      %-75s' % (step, os.path.join(folder, 'experiment.log')))
        step += 1

        startup = os.path.join(os.getenv('HOME'), '.ipython', 'profile_collection', 'startup')

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## write scan.ini template
        initmpl = os.path.join(startup, 'scan.tmpl')
        scanini = os.path.join(folder, 'scan.ini')
        if not os.path.isfile(scanini):
            with open(initmpl) as f:
                content = f.readlines()
            o = open(scanini, 'w')
            o.write(''.join(content).format(folder=folder, name=name))
            o.close()
            print('%2d. Created INI template:              %-75s' % (step, scanini))
        else:
            print('%2d. Found INI template:                %-75s' % (step, scanini))
        step += 1

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## write macro template & wheel spreadsheet
        macrotmpl = os.path.join(startup, 'wheelmacro.tmpl')
        macropy = os.path.join(folder, 'sample_macro.py')
        commands = '''
        ## sample 1
        yield from slot(1)
        yield from xafs('scan.ini', filename='samp1', sample='first sample')
        close_last_plot()
    
        ## sample 2
        yield from slot(2)
        ## yield from mvr(xafs_x, 0.5)
        yield from xafs('scan.ini', filename='samp2', sample='another sample', comment='my comment')
        close_last_plot()

        ## sample 3
        yield from slot(3)
        yield from xafs('scan.ini', filename='samp3', sample='a different sample', prep='this sample prep', nscans=4)
        close_last_plot()'''
        if not os.path.isfile(macropy):
            with open(macrotmpl) as f:
                content = f.readlines()
            o = open(macropy, 'w')
            o.write(''.join(content).format(folder=folder, base='sample', content=commands))
            o.close()
            print('%2d. Created macro template:            %-75s' % (step, macropy))
        else:
            print('%2d. Found macro template:              %-75s' % (step, macropy))
        step += 1

        xlsxtmpl = os.path.join(startup, 'wheel_template.xlsx')
        xlsxfile = os.path.join(folder, 'wheel_template.xlsx')
        if not os.path.isfile(xlsxfile):
            shutil.copyfile(os.path.join(startup, 'wheel_template.xlsx'),  xlsxfile)
            print('%2d. Copied wheel macro spreadsheet:    %-75s' % (step, xlsxfile))

        else:
            print('%2d. Found wheel macro spreadsheet:     %-75s' % (step, xlsxfile))
        step += 1            
        
        xlsxtmpl = os.path.join(startup, 'pinwheel_template.xlsx')
        xlsxfile = os.path.join(folder, 'pinwheel_template.xlsx')
        if not os.path.isfile(xlsxfile):
            shutil.copyfile(os.path.join(startup, 'wheel_template.xlsx'),  xlsxfile)
            print('%2d. Copied pinwheel macro spreadsheet: %-75s' % (step, xlsxfile))

        else:
            print('%2d. Found pinwheel macro spreadsheet:  %-75s' % (step, xlsxfile))
        step += 1            
        
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## make html folder, copy static html generation files
        htmlfolder = os.path.join(folder, 'dossier')
        if not os.path.isdir(htmlfolder):
            os.mkdir(htmlfolder)
            for f in ('sample.tmpl', 'sample_xs.tmpl', 'sample_ga.tmpl', 'manifest.tmpl', 'logo.png', 'style.css', 'trac.css'):
                shutil.copyfile(os.path.join(startup, f),  os.path.join(htmlfolder, f))
            manifest = open(os.path.join(self.DATA, 'dossier', 'MANIFEST'), 'a')
            manifest.close()
            print('%2d. Created dossier folder:            %-75s' % (step,htmlfolder))
            print('   copied html generation files, touched MANIFEST')
        else:
            print('%2d. Found dossier folder:              %-75s' % (step,htmlfolder))
        step += 1
     
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## make prj folder
        prjfolder = os.path.join(folder, 'prj')
        if not os.path.isdir(prjfolder):
            os.mkdir(prjfolder)
            print('%2d. Created Athena prj folder:         %-75s' % (step,prjfolder))
        else:
            print('%2d. Found Athena prj folder:           %-75s' % (step,prjfolder))
        step += 1

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## make XRF folder
        xrffolder = os.path.join(folder, 'XRF')
        if not os.path.isdir(xrffolder):
            os.mkdir(xrffolder)
            print('%2d. Created folder for XRF spectra:    %-75s' % (step,xrffolder))
        else:
            print('%2d. Found folder for XRF spectra:      %-75s' % (step,xrffolder))
        step += 1
        
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## make prj folder
        if use_pilatus:
            pilfolder = os.path.join(folder, 'Pilatus')
            if not os.path.isdir(pilfolder):
                os.mkdir(pilfolder)
                print('%2d. Created folder for Pilatus images: %-75s' % (step,pilfolder))
            else:
                print('%2d. Found folder for Pilatus images:   %-75s' % (step,pilfolder))
            step += 1

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## make echem folder
        if echem:
            self.echem = True
            ecfolder = os.path.join(folder, 'electrochemistry')
            if not os.path.isdir(ecfolder):
                os.mkdir(ecfolder)
                print('%2d. Created folder for echem data:  %-75s' % (step,ecfolder))
            else:
                print('%2d. Found folder for echem data:    %-75s' % (step,ecfolder))
            self.echem_remote = os.path.join('/mnt/nfs/ws3', name, self.date)
            if not os.path.isdir(self.echem_remote):
                os.makedirs(self.echem_remote)
                print('   Created remote echem folder:       %-75s' % (self.echem_remote))
            else:
                print('   Found remote echem folder:         %-75s' % (self.echem_remote))
            
            step += 1

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## make gdrive folder
        user_folder = make_gdrive_folder(prefix='    ', update=False)
        for f in ('logo.png', 'style.css', 'trac.css'):
            shutil.copyfile(os.path.join(startup, f),  os.path.join(user_folder, 'dossier', f))
        print('%2d. Established Google Drive folder:   %-75s' % (step, user_folder))
        print(whisper(f'    Don\'t foget to share Google Drive folder and Slack channel with {name}'))
        step += 1
            
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## SAF and GUP
        self.gup = gup
        self.saf = saf
        print('%2d. Set GUP and SAF numbers as metadata' % step)
        step += 1

        self.user_is_defined = True
    
        return None

    def start_experiment(self, name=None, date=None, gup=0, saf=0, use_pilatus=False, echem=False):
        '''
        Get ready for a new experiment.  Run this first thing when a user
        sits down to start their beamtime.  This will:
          * Create a folder, if needed, and set the DATA variable
          * Set up the experimental log, creating an experiment.log file, if needed
          * Write templates for scan.ini and macro.py, if needed
          * Copy some other useful files
          * Make snapshots, dossier, and prj folders
          * Set the GUP and SAF numbers as metadata

        Parameters
        ---------
        name : str
            name of PI
        date : str
            YYYY-MM-DD start date of experiment (e.g. 2018-11-29)
        gup : str
            GUP number
        saf : str
            SAF number
        '''
        if self.user_is_defined:
            print(error_msg('An experiment is already started.'))
            return()
        if name is None:
            print(error_msg('You did not supply the user\'s name'))
            return()
        if date is None:
            print(error_msg('You did not supply the start date'))
            return()
        pattern=re.compile('\d{4}\-\d{2}\-\d{2}')
        if not pattern.search(date):
            print(error_msg('The start date must be in the form YYYY-MM-DD'))
            return()
        if gup == 0:
            print(error_msg('You did not supply the GUP number'))
            return()
        if saf == 0:
            print(error_msg('You did not supply the SAF number'))
            return()
        if name in BMM_STAFF:
            self.staff = True
            folder = os.path.join(os.getenv('HOME'), 'Data', 'Staff', name, date)
            #if '' in name:
            #    self.lims = False
        else:
            self.staff = False
            folder = os.path.join(os.getenv('HOME'), 'Data', 'Visitors', name, date)
        self.name = name
        self.date = date
        self.new_experiment(folder, saf=saf, gup=gup, name=name, use_pilatus=use_pilatus, echem=echem)

        # preserve BMMuser state to a json string #
        self.prev_fig = None
        self.prev_ax  = None
        self.to_json(os.path.join(self.DATA, '.BMMuser'))
        if not os.path.isfile(os.path.join(os.environ['HOME'], 'Data', '.BMMuser')):
            os.symlink(os.path.join(self.DATA, '.BMMuser'), os.path.join(os.environ['HOME'], 'Data', '.BMMuser'))

        jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
        if os.path.isfile(jsonfile):
            os.chmod(jsonfile, 0o644)
        with open(jsonfile, 'w') as outfile:
            json.dump({'name': name, 'date': date, 'gup' : gup, 'saf' : saf}, outfile)
        os.chmod(jsonfile, 0o444)


    def start_experiment_from_serialization(self):
        '''In the situation where bsui needs to be stopped (or crashes) before
        an experiment is properly ended using the end_experiment()
        command, this function will read a json serialization of the
        arguments to the start_experiment() command.

        If that serialization file is found at bsui start-up, this function
        is run. Thus, the session is immediately ready for the current user.

        In the situation where this start-up script is "%run -i"-ed,
        the fact that self.user_is_defined is True will be recognized.
        '''
        if self.user_is_defined:
            return()
        
        jsonfile = os.path.join(os.environ['HOME'], 'Data', '.BMMuser')
        #jsonfile = os.path.join(self.DATA, '.BMMuser')
        if os.path.isfile(jsonfile):
            self.from_json(jsonfile)
            self.trigger = True
            #user = json.load(open(jsonfile))
            if self.name is not None:
                self.start_experiment(name=self.name, date=self.date, gup=self.gup, saf=self.saf)
            #if 'foils' in user:
            #    self.read_foils = user['foils'] # see 76-edge.py, line 114, need to delay configuring foils until 76-edge is read
            #if 'rois' in user:
            #    self.read_rois  = user['rois']  # see 76-edge.py, line 189, need to delay configuring ROIs until 76-edge is read

    @set_user_ns
    def show_experiment(self, *, user_ns):
        '''Show serialized configuration parameters'''
        print('DATA  = %s' % self.DATA)
        print('GUP   = %s' % self.gup)
        print('SAF   = %s' % self.saf)
        #print('foils = %s' % ' '.join(map(str, user_ns['foils'].slots)))
        if user_ns['with_xspress3'] is False:
            print('ROIs  = %s' % ' '.join(map(str, user_ns['rois'].slots)))

    def fetch_echem(self):
        dest = os.path.join(self.folder, 'electrochemistry')
        copy_tree(self.echem_remote, dest)
        report('Copied electrochemistry data from: "%s" to "%s"' % (self.echem_remote, dest), 'bold')

    @set_user_ns
    def end_experiment(self, force=False, *, user_ns=None):
        '''
        Copy data from the experiment that just finished to the NAS, then
        unset the logger and the DATA variable at the end of an experiment.
        '''
        #global DATA

        if self.echem and not os.path.ismount('/mnt/nfs/ws3'):
            print(error_msg('''
**************************************************************************
   This is an electrochemistry experiment and /mnt/nfs/ws3 is not mounted
   Electrochemistry data is not being backed up!
**************************************************************************
            '''))

        if not force:
            if not self.user_is_defined:
                print(error_msg('There is not a current experiment!'))
                return(None)

            ######################################################################
            #copy the electrochemistry data, if this was that sort of experiment #
            ######################################################################
            if self.echem and os.path.ismount('/mnt/nfs/ws3'):
                try:
                    self.fetch_echem()
                except:
                    print(error_msg('Unable to copy electrochemistry data from ws3'))
                    if not os.path.ismount('/mnt/nfs/ws3'):
                        print(error_msg('\t/mnt/nfs/ws3 seems not to be mounted...'))
            
            #######################################################################################
            # create folder and sub-folders on NAS server for this user & experimental start date #
            #######################################################################################
            destination = os.path.join(user_ns['nas_mount_point'], 'xf06bm', 'user', self.name, self.date)
            if not os.path.isdir(destination):
                os.makedirs(destination)
            for d in ('dossier', 'prj', 'snapshots'):
                if not os.path.isdir(os.path.join(destination, d)):
                    os.makedirs(os.path.join(destination, d))
            try:
                copy_tree(self.DATA, destination)
                report('NAS data store: "%s"' % destination, 'bold')
            except:
                print(error_msg('Unable to write data to NAS server'))

        #####################################################################
        # remove the json serialization of the start_experiment() arguments #
        #####################################################################

        if os.path.isfile(os.path.join(os.environ['HOME'], 'Data', '.BMMuser')):
            os.remove(os.path.join(os.environ['HOME'], 'Data', '.BMMuser'))
        jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
        if os.path.isfile(jsonfile):    
            os.chmod(jsonfile, 0o644)
            os.remove(jsonfile)

            
        ###############################################################
        # unset self attributes, DATA, and experiment specific logger #
        ###############################################################
        BMM_unset_user_log()
        DATA = os.path.join(os.environ['HOME'], 'Data', 'bucket') + '/'
        self.DATA = os.path.join(os.environ['HOME'], 'Data', 'bucket') + '/'
        self.folder = self.DATA
        user_ns["wmb"].folder = self.folder
        self.date = ''
        self.gup = 0
        self.saf = 0
        self.name = None
        self.staff = False
        self.user_is_defined = False
        self.echem = False
        self.echem_remote = None
        
        return None
