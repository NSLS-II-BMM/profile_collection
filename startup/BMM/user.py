import sys, os, re, shutil, socket, datetime
from distutils.dir_util import copy_tree
import json, pprint, copy
from subprocess import run

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

import BMM.functions
from BMM.functions import BMM_STAFF, LUSTRE_XAS
from BMM.functions import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.gdrive    import make_gdrive_folder
from BMM.logging   import BMM_user_log, BMM_unset_user_log, report
from BMM.periodictable import edge_energy
from BMM.workspace import rkvs

from BMM.user_ns.base import startup_dir

TEMPLATES_FOLDER = 'templates'


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
    motor_fault : str or None
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
    syns : bool 
        True is any MCS8 axes are disconnected and defined as SynAxis
    display_img : None or PIL object
        Carries the most recently displayed PIL object

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
        data folder on Lustre
    folder_link : str
        local link to Lustre data folder
    filename : str
        output data file stub
    experimenters : str
        names of experimenters
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
    shutter : bool 
        True to close and open shutter to minimize beam exposure

    Methods for public use
    ----------------------
    start_experiment(self, name=None, date=None, gup=0, saf=0)

    end_experiment(self, force=False)

    show_experiment(self)
    '''
    def __init__(self):
        ## experiment attributes
        self.DATA            = os.path.join(os.getenv('HOME'), 'Data', 'bucket') + '/'
        self.gdrive          = None
        self.prompt          = True
        self.final_log_entry = True
        self.date            = ''
        self.gup             = 0
        self.saf             = 0
        # e.g. self.cycle = '2022-2'
        cnum = (0,1,1,1,1,2,2,2,2,3,3,3,3)[int(datetime.datetime.now().strftime("%m"))]
        self.cycle           = f'{datetime.datetime.now().strftime("%Y")}-{cnum}'
        self.host            = socket.gethostname()
        self.use_pilatus     = False
        self.name            = None
        self.staff           = False
        #self.read_foils      = None
        #self.read_rois       = None
        self.user_is_defined = False
        self.motor_fault     = None
        self.detector        = 4
        self.echem           = False
        self.echem_remote    = None
        self.use_slack       = True
        self.slack_channel   = None
        self.trigger         = False
        self.instrument      = ''
        self.running_macro   = False
        self.suspenders_engaged = False
        self.display_img     = None
        
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
        self.folder        = os.path.join(os.getenv('HOME'), 'Data', 'bucket')
        self.folder_link   = None
        self.filename      = 'data.dat'
        self.experimenters = ''
        self.element       = None
        self.e0            = None
        self.energy        = None
        self.edge          = 'K'
        self.sample        = ''
        self.prep          = ''
        self.comment       = ''
        self.nscans        = 1
        self.start         = 0
        self.inttime       = 1
        self.snapshots     = True
        self.usbstick      = False
        self.rockingcurve  = False
        self.htmlpage      = True
        self.bothways      = False
        self.channelcut    = True
        self.ththth        = False
        self.lims          = True
        self.mode          = 'transmission'
        self.url           = False
        self.doi           = False
        self.cif           = False
        self.npoints       = 0     ###########################################################################
        self.dwell         = 1.0   ## parameters for single energy absorption detection, see 72-timescans.py #
        self.delay         = 0.1   ###########################################################################
        self.shutter       = False
        
        ## mono acceleration control
        self.acc_fast      = 0.2   ###########################################################################
        self.acc_slow      = 0.5   # after decreasing Bragg acceleration time, Bragg axis would occasionally #
                                   # freeze. these are used to try to mitigate this problem                  #
                                   ###########################################################################
        
        self.bender_xas    = 212225  #####################################################################
        self.bender_xrd    = 107240  # approximate values for M2 bender for focusing at XAS & XRD tables #
        self.bender_margin = 30000   #####################################################################

        self.filter_state  = 0

        self.extra_metadata = None
        self.syns           = False

        self.post_webcam    = False  ########################################################
        self.post_usbcam1   = False  # parameters for controlling what gets posted to Slack #
        self.post_usbcam2   = False  ########################################################
        self.post_anacam    = False
        self.post_xrf       = False

        self.tweak_xas_time = 24.0
        
        self.bmm_strings  = ("DATA", "gdrive", "date", "host", "name", "instrument",
                             "readout_mode", "folder", "folder_link", "filename",
                             "experimenters", "element", "edge", "sample", "prep", "comment",
                             "xs1", "xs2", "xs3", "xs4", "xs8", "pds_mode", "mode", "roi1",
                             "roi2", "roi3", "roi4", "dtc1", "dtc2", "dtc3", "dtc4")
        self.bmm_ints     = ("gup", "saf", "detector", "npoints", "bender_xas", "bender_xrd",
                             "bender_margin", "filter_state", "nscans", "start")
        self.bmm_floats   = ("macro_sleep", "dwell", "delay", "acc_fast", "acc_slow",
                             "inttime", "tweak_xas_time") #, "edge_energy")
        self.bmm_booleans = ("prompt", "final_log_entry", "use_pilatus", "staff", "echem",
                             "use_slack", "trigger", "running_macro", "suspenders_engaged",
                             "macro_dryrun", "snapshots", "usbstick", "rockingcurve",
                             "htmlpage", "bothways", "channelcut", "ththth", "lims", "url",
                             "doi", "cif", "syns",
                             "post_webcam", "post_anacam", "post_usbcam1", "post_usbcam2", "post_xrf")
        self.bmm_none     = ("echem_remote", "slack_channel", "extra_metadata")
        self.bmm_ignore   = ("motor_fault", "bounds", "steps", "times", "motor", "motor2",
                             "fig", "ax", "x", "y", "prev_fig", "prev_ax", 'display_img')
        self.bmm_obsolete = ("read_rois", "e0", "rois", "roi_channel")


    def state_to_redis(self, filename=None, prefix='', verbose=False):

        all_keys = list(self.__dict__.keys())
        almost_all_keys = [n for n in all_keys
                           if n not in ('fig', 'ax', 'prev_fig', 'prev_ax', 'display_img',
                                        'motor', 'cycle', 'user_is_defined') and
                           'xschannel' not in n]
        d = dict()
        for k in self.bmm_strings:
            d[k] = getattr(self, k)
            if verbose: print(f'string: {k} = >{getattr(self, k)}<')
            if getattr(self, k) is None:
                rkvs.set(f'BMM:user:{k}', 'None')
            else:
                rkvs.set(f'BMM:user:{k}', getattr(self, k))
        for k in self.bmm_ints:
            d[k] = getattr(self, k)
            if verbose: print(f'int: {k} = >{getattr(self, k)}<')
            if getattr(self, k) is None:
                rkvs.set(f'BMM:user:{k}', 0)
            else:
                rkvs.set(f'BMM:user:{k}', getattr(self, k))
        for k in self.bmm_floats:
            d[k] = getattr(self, k)
            if verbose: print(f'float: {k} = >{getattr(self, k)}<')
            if getattr(self, k) is None:
                rkvs.set(f'BMM:user:{k}', 0.0)
            else:
                rkvs.set(f'BMM:user:{k}', getattr(self, k))
        for k in self.bmm_booleans:
            d[k] = getattr(self, k)
            if verbose: print(f'bool: {k} = >{getattr(self, k)}<')
            if getattr(self, k) is None:
                rkvs.set(f'BMM:user:{k}', 'False')
            else:
                rkvs.set(f'BMM:user:{k}', str(getattr(self, k)))
        for k in self.bmm_none:
            d[k] = getattr(self, k)
            if verbose: print(f'none: {k} = >{getattr(self, k)}<')
            setattr(self, k, '')
        
        #for k in almost_all_keys:
        #    d[k] = getattr(self, k)
        #    rkvs.set(f'BMM:user:{k}', str(d[k]))
        print(f'\n{prefix}wrote BMMuser state to redis')
        
        if filename is None:
            print(json.dumps(d, indent=4))
        else:
            with open(filename, 'w') as outfile:
                json.dump(d, outfile, indent=4)
            print(f'\n{prefix}wrote BMMuser state to {filename}')

    def set_element(self, element, edge=None):
        if edge is None:
            energy = edge_energy(element,'K')
            self.element = element
            if energy > 23500:
                self.edge = 'L3'
            else:
                self.edge = 'K'
        else:
            self.element = element
            self.edge    = edge
        for i in (1,2,3,4,8):
            setattr(self, f'xs{i}', f'{element}{i}')
        for key in ('element', 'edge', 'xs1', 'xs2', 'xs3', 'xs4', 'xs8'):
            rkvs.set(f'BMM:user:{key}', getattr(self, key))

    def verify_roi(self, xs, el, edge, tab=''):
        print(bold_msg(f'{tab}Attempting to set ROIs on {xs.name} for {el} {edge} edge'))
        try:
            ## if el is not one of the "standard" 12 ROI sets, insert it into xs.slots[12]/index 13
            if xs.check_element(el, edge):
                forceit = False
                if el.capitalize() in ('Pb', 'Pt') and edge.capitalize() in ('L2', 'L1'):
                    forceit = True # Pb and Pt L3 edges are "standard" ROIs
                if el not in xs.slots or forceit:
                    with open(os.path.join(startup_dir, 'rois.json'), 'r') as fl:
                        js = fl.read()
                    allrois = json.loads(js)
                    xs.slots[14] = el
                    for channel in xs.iterate_channels():
                        xs.set_roi_channel(channel, index=15, name=f'{el.capitalize()}',
                                           low =allrois[el.capitalize()][edge.lower()]['low'],
                                           high=allrois[el.capitalize()][edge.lower()]['high'])
                    xs.set_rois()
                    # xs1.slots[14] = el
                    # for channel in xs1.iterate_channels():
                    #     xs1.set_roi_channel(channel, index=15, name=f'{el.capitalize()}',
                    #                         low =allrois[el.capitalize()][edge.lower()]['low'],
                    #                         high=allrois[el.capitalize()][edge.lower()]['high'])
                    # xs1.set_rois()

                xs.measure_roi()
                #xs1.measure_roi()
            else:
                report(f'{tab}No tabulated ROIs for the {el.capitalize()} {edge.capitalize()} edge.  Not setting ROIs for mesaurement.',
                       level='bold', slack=True)
            xs.reset_rois(tab=tab, quiet=True)
        except Exception as E:
            print(error_msg(E))

            
    def state_from_redis(self): #, filename):
        # if os.path.isfile(filename):
        #     with open(filename, 'r') as jsonfile:
        #         config = json.load(jsonfile)
        #     for k in config.keys():
        #         ## deal with things that may be floating around in a
        #         ## .BMMuser, but which need not be initialized
        #         if k in ('cycle', 'read_rois', 'e0', 'bounds', 'steps', 'times',
        #                  'motor', 'motor2', 'fig', 'ax', 'x', 'y', 'prev_fig', 'prev_ax',
        #                  'bmm_strings', 'bmm_ints', 'bmm_floats', 'bmm_booleans', 'bmm_none'):
        #             continue
        #         setattr(self, k, config[k])
        #     #rois.trigger = True
        from BMM.workspace import rkvs
        verbose = False
        for k in self.bmm_strings:
            if verbose: print("string:", k)
            try:
                setattr(self, k, rkvs.get(f'BMM:user:{k}').decode('utf-8'))
            except AttributeError:
                setattr(self, k, '')
        for k in self.bmm_ints:
            if verbose: print("int:", k)
            if rkvs.get(f'BMM:user:{k}').decode('utf-8').strip() == '':
                setattr(self, k, 0)
            else:
                setattr(self, k, int(rkvs.get(f'BMM:user:{k}').decode('utf-8')))
        for k in self.bmm_floats:
            if verbose: print("float:", k)
            try:
                setattr(self, k, float(rkvs.get(f'BMM:user:{k}').decode('utf-8')))
            except AttributeError:
                setattr(self, k, 0.0)
        for k in self.bmm_booleans:
            this = rkvs.get(f'BMM:user:{k}').decode('utf-8')
            if verbose: print("bool:", k, this)
            if this.lower() in ('false', 'no', '0', 'f', 'n'):
                setattr(self, k, False)
            else:
                setattr(self, k, True)
        for k in self.bmm_none:
            if verbose: print("none:", k)
            setattr(self, k, None)
        
        rkvs.set('BMM:pds:element',     self.element)
        rkvs.set('BMM:pds:edge',        self.edge)
        rkvs.set('BMM:pds:edge_energy', edge_energy(self.element, self.edge))
            
    def show(self, scan=False):
        '''
        Show the current contents of the BMMuser object
        '''
        print('Experiment attributes:')
        for att in ('DATA', 'prompt', 'final_log_entry', 'date', 'gup', 'saf', 'name', 'staff', 
                    'user_is_defined', 'pds_mode', 'macro_dryrun', 'macro_sleep', 'motor_fault',
                    'detector', 'use_pilatus', 'echem', 'echem_remote'):
            print('\t%-15s = %s' % (att, str(getattr(self, att))))

        print('\nROI control attributes:')
        for att in (#'roi_channel', 'roi1', 'roi2', 'roi3', 'roi4', 'dtc1', 'dtc2', 'dtc3', 'dtc4',
                    'xs1', 'xs2', 'xs3', 'xs4',
                    'xschannel1', 'xschannel2', 'xschannel3', 'xschannel4'):
            print('\t%-15s = %s' % (att, str(getattr(self, att))))

        print('\nCurrent plot attributes:')
        for att in ('motor', 'motor2', 'fig', 'ax', 'x', 'y'):
            print('\t%-15s = %s' % (att, str(getattr(self, att))))

        print('\nMono acceleration and M2 bender attributes:')
        for att in ('acc_fast', 'acc_slow', 'bender_xas', 'bender_xrd', 'bender_margin'):
            print('\t%-15s = %s' % (att, str(getattr(self, att))))

        if scan:
            print('\nScan control attributes:')
            for att in ('pds_mode', 'bounds', 'steps', 'times', 'folder', 'filename',
                        'experimenters', 'element', 'edge', 'sample', 'prep', 'comment', 'nscans', 'start', 'inttime',
                        'snapshots', 'usbstick', 'rockingcurve', 'htmlpage', 'bothways', 'channelcut', 'ththth', 'mode', 'npoints',
                        'dwell', 'delay'):
                print('\t%-15s = %s' % (att, str(getattr(self, att))))


    def establish_folder(self, i, text, folder):
        '''Locate or create the folders we need for this user.
        '''
        if not os.path.isdir(folder):
            os.makedirs(folder)
            verb, pad = 'Created', ''
        else:
            verb, pad = 'Found', '  '
        self.print_verb_message(i, verb, text, pad, folder)
        return(verb)

    def find_or_copy_file(self, i, text, fname):
        src     = os.path.join(startup_dir, fname)
        dst     = os.path.join(self.folder, fname)
        if 'xlsx' in fname:
            src = os.path.join(startup_dir, 'xlsx', fname)
            dst     = os.path.join(self.folder, TEMPLATES_FOLDER, fname)
        if not os.path.isfile(dst):
            shutil.copyfile(src,  dst)
            verb, pad = 'Copied', ' '
        else:
            verb, pad = 'Found', '  '
        self.print_verb_message(i, verb, text, pad, dst)
        
    def print_verb_message(self, i, verb, text, pad, result):
        if i == 0:
            print(f'    {verb} {text:28}{pad}   {result:65}')
        else:
            print(f'{i:2d}. {verb} {text:28}{pad}   {result:65}')


    def new_experiment(self, folder, gup=0, saf=0, name='Betty Cooper', use_pilatus=False, echem=False):
        '''
        Do the work of prepping for a new experiment.  This will:
          * Create a data folder and it's subfolders, if needed, and set the DATA variable
          * Set up the experimental log, creating an experiment.log file, if needed
          * Write templates for scan.ini and macro.py + xlsx templates, if needed
          * Make folders for XRF, HDF5, Pilatus, and electrochemistry
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
        use_pilatus : bool
            true if this experiment uses the Pilatus
        echem : bool
            true if this experiment uses the BioLogic potentiostat
        '''

        step = 1
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## Main folders, point BMMuser and wmb objects at data folder
        data_folder = os.path.join(folder, self.date)
        user_ns['DATA'] = self.DATA = self.folder = data_folder + '/'
        try:
            hdf5folder = os.path.join('/nsls2', 'data', 'bmm', 'assets', 'xspress3', *self.date.split('-'))
            user_ns['xs'].hdf5.read_path_template = hdf5folder
            user_ns['xs'].hdf5.write_path_template = hdf5folder
            user_ns['xs'].hdf5.file_path.put(hdf5folder)
        except:
            # if we are starting up bsui, the xs folder will get set
            # later.  the try block is needed when running
            # start_experiment from a running bsui instance.
            pass
        try:
            user_ns['wmb'].folder = data_folder + '/'
        except:
            pass
        
        imagefolder    = os.path.join(data_folder, 'snapshots')
        prjfolder      = os.path.join(data_folder, 'prj')
        htmlfolder     = os.path.join(data_folder, 'dossier')
        templatefolder = os.path.join(data_folder, TEMPLATES_FOLDER)
        self.establish_folder(step, 'Lustre folder', folder)
        self.establish_folder(0,    'data folder', data_folder)
        self.establish_folder(0,    'snapshot folder', imagefolder)
        self.establish_folder(0,    'Athena prj folder', prjfolder)
        if self.establish_folder(0, 'dossier folder', htmlfolder) == 'Created':
            # 'sample.tmpl', 'sample_xs.tmpl', 'sample_ga.tmpl'
            for f in ('manifest.tmpl', 'logo.png', 'style.css', 'trac.css'):
                shutil.copyfile(os.path.join(startup_dir, 'dossier', f),  os.path.join(htmlfolder, f))
            manifest = open(os.path.join(self.DATA, 'dossier', 'MANIFEST'), 'a')
            manifest.close()
            print('    copied html generation files, touched MANIFEST')
        self.establish_folder(0,    'templates folder', templatefolder)
     
        step += 1

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## setup logger
        BMM_user_log(os.path.join(data_folder, 'experiment.log'))
        print('%2d. Set up experimental log file:          %-75s' % (step, os.path.join(data_folder, 'experiment.log')))
        step += 1

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## scan.ini template, macro template & wheel/ga spreadsheets
        initmpl = os.path.join(startup_dir, 'tmpl', 'xafs.tmpl')
        scanini = os.path.join(data_folder, TEMPLATES_FOLDER, 'xafs.ini')
        if not os.path.isfile(scanini):
            with open(initmpl) as f:
                content = f.readlines()
            o = open(scanini, 'w')
            o.write(''.join(content).format(folder=data_folder, name=name))
            o.close()
            verb, pad = 'Copied', ' '
        else:
            verb, pad = 'Found', '  '
        self.print_verb_message(step, verb, 'XAFS INI file', pad, scanini)

        initmpl = os.path.join(startup_dir, 'tmpl', 'rasterscan.tmpl')
        scanini = os.path.join(data_folder, TEMPLATES_FOLDER, 'raster.ini')
        if not os.path.isfile(scanini):
            with open(initmpl) as f:
                content = f.readlines()
            o = open(scanini, 'w')
            o.write(''.join(content).format(folder=data_folder, name=name))
            o.close()
            verb, pad = 'Copied', ' '
        else:
            verb, pad = 'Found', '  '
        self.print_verb_message(0, verb, 'raster INI file', pad, scanini)

        initmpl = os.path.join(startup_dir, 'tmpl', 'sead.tmpl')
        scanini = os.path.join(data_folder, TEMPLATES_FOLDER, 'sead.ini')
        if not os.path.isfile(scanini):
            with open(initmpl) as f:
                content = f.readlines()
            o = open(scanini, 'w')
            o.write(''.join(content).format(folder=data_folder, name=name))
            o.close()
            verb, pad = 'Copied', ' '
        else:
            verb, pad = 'Found', '  '
        self.print_verb_message(0, verb, 'sead INI file', pad, scanini)

        
        macrotmpl = os.path.join(startup_dir, 'tmpl', 'macro.tmpl')
        macropy = os.path.join(data_folder, TEMPLATES_FOLDER, 'sample_macro.py')
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
            o.write(''.join(content).format(folder=data_folder,
                                            base='sample',
                                            content=commands,
                                            description='(example...)',
                                            instrument='',
                                            cleanup='',
                                            initialize='' ))
            o.close()
            verb, pad = 'Copied', ' '
        else:
            verb, pad = 'Found', '  '
        self.print_verb_message(0, verb, 'macro template', pad, macropy)

        self.find_or_copy_file(0, 'wheel macro spreadsheet',    'wheel.xlsx')
        self.find_or_copy_file(0, 'glancing angle spreadsheet', 'glancing_angle.xlsx')
        self.find_or_copy_file(0, 'double wheel spreadsheet',   'doublewheel.xlsx')
        self.find_or_copy_file(0, 'Linkam stage spreadsheet',   'linkam.xlsx')
        self.find_or_copy_file(0, 'Lakeshore spreadsheet',      'lakeshore.xlsx')
        self.find_or_copy_file(0, 'motor grid spreadsheet',     'grid.xlsx')
        step += 1            
        
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## XRF & HDF5folders
        xrffolder = os.path.join(data_folder, 'XRF')
        self.establish_folder(step, 'XRF spectra folder', xrffolder)
        #hdf5folder = os.path.join(data_folder, 'raw', 'HDF5')
        #hdf5folder = os.path.join('/nsls2', 'data', 'bmm', 'assets', 'xspress3', *self.date.split('-'))
        #self.establish_folder(0, 'Xspress3 HDF5 folder', hdf5folder)
        #xs.hdf5.file_path.put(hdf5folder)
        
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## Pilatus folder
        if use_pilatus:
            pilfolder = os.path.join(data_folder, 'raw', 'Pilatus')
            self.establish_folder(0, 'Pilatus folder', pilfolder)

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## echem folder
        if echem:
            self.echem = True
            ecfolder = os.path.join(data_folder, 'raw', 'electrochemistry')
            self.establish_folder(0, 'electrochemistry folder', ecfolder)
            #self.echem_remote = os.path.join('/mnt/nfs/ws3', name, self.date)
            #if not os.path.isdir(self.echem_remote):
            #    os.makedirs(self.echem_remote)
            #    print('   Created remote echem folder:       %-75s' % (self.echem_remote))
            #else:
            #    print('   Found remote echem folder:         %-75s' % (self.echem_remote))
            
        step += 1

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## GDrive folder
        user_folder = make_gdrive_folder(prefix='    ', update=False)
        for f in ('logo.png', 'style.css', 'trac.css'):
            shutil.copyfile(os.path.join(startup_dir, 'dossier', f),  os.path.join(user_folder, 'dossier', f))
        print('%2d. Established Google Drive folder:       %-75s' % (step, user_folder))
        print(whisper(f'    Don\'t foget to share Google Drive folder and Slack channel with {name}'))
        step += 1
            
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## SAF and GUP
        self.gup = gup
        self.saf = saf
        print(f'{step:2d}. Set GUP and SAF numbers as metadata    GUP: {gup}   SAF: {saf}')
        shipping_folder = os.path.join(os.getenv('HOME'), 'SDS', self.cycle, f'{saf}')
        self.establish_folder(0, 'shipping docs folder', shipping_folder)
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
        use_pilatus : bool
            true if this experiment uses the Pilatus
        echem : bool
            true if this experiment uses the BioLogic potentiostat
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
        if not pattern.fullmatch(date) is not None:
            print(error_msg('The start date must be in the form YYYY-MM-DD'))
            return()
        if gup == 0:
            print(error_msg('You did not supply the GUP number'))
            return()
        if saf == 0:
            print(error_msg('You did not supply the SAF number'))
            return()
        
        lustre_root = os.path.join(LUSTRE_XAS, f'{self.cycle}', f'{saf}')
        if not os.path.isdir(lustre_root):
            os.makedirs(lustre_root)
        if name in BMM_STAFF:
            self.staff = True
            local_folder = os.path.join(os.getenv('HOME'), 'Data', 'Staff', name, date)
            #if '' in name:
            #    self.lims = False
        else:
            self.staff = False
            local_folder = os.path.join(os.getenv('HOME'), 'Data', 'Visitors', name, date)
        self.name = name
        self.date = date
        
        self.new_experiment(lustre_root, saf=saf, gup=gup, name=name, use_pilatus=use_pilatus, echem=echem)

        # preserve BMMuser state to a json string #
        self.prev_fig = None
        self.prev_ax  = None
        self.state_to_redis(filename=os.path.join(self.DATA, '.BMMuser'), prefix='    ')
        slink = os.path.join(os.environ['HOME'], 'Data', '.BMMuser')
        if os.path.isfile(slink):
            os.remove(slink)
        os.symlink(os.path.join(self.DATA, '.BMMuser'), slink)

        jsonfile = os.path.join(os.environ['HOME'], 'Data', '.user.json')
        if os.path.isfile(jsonfile):
            os.chmod(jsonfile, 0o644)
        with open(jsonfile, 'w') as outfile:
            json.dump({'name': name, 'date': date, 'gup' : gup, 'saf' : saf}, outfile)
        os.chmod(jsonfile, 0o444)

        if name in BMM_STAFF:
            user_folder = os.path.join(os.getenv('HOME'), 'Data', 'Staff', name)
        else:
            user_folder = os.path.join(os.getenv('HOME'), 'Data', 'Visitors', name)
        if not os.path.isdir(user_folder):
            os.makedirs(user_folder)
        if not os.path.islink(local_folder):
            os.symlink(self.DATA, local_folder, target_is_directory=True)
        print(f'    Made symbolic link to data folder at {local_folder}')
        self.folder_link = local_folder
        
        # if 'xf06bm-ws1' in self.host:
        #     mkdir_command = ['ssh', '-q', 'xf06bm@xf06bm-ws3', f"mkdir -p '{user_folder}'"]
        #     symlink_command = ['ssh', '-q', 'xf06bm@xf06bm-ws3', f"ln -s {lustre_root}/{date} '{local_folder}'"]
        #     other_machine = 'xf06bm-ws3'
        # elif 'xf06bm-ws3' in self.host:
        #     mkdir_command = ['ssh', '-q', 'xf06bm@xf06bm-ws1', f"mkdir -p '{user_folder}'"]
        #     symlink_command = ['ssh', '-q', 'xf06bm@xf06bm-ws1', f"ln -s {lustre_root}/{date} '{local_folder}'"]
        #     other_machine = 'xf06bm-ws1'

        # #print(mkdir_command)
        # #print(symlink_command)
        # run(mkdir_command)
        # run(symlink_command)
        # print(whisper(f'    Made symbolic link to data folder on {other_machine}'))
        
        try:
            xascam._root = os.path.join(self.folder, 'snapshots')
            xrdcam._root = os.path.join(self.folder, 'snapshots')
            anacam._root = os.path.join(self.folder, 'snapshots')
            usb1.tiff1.file_path.put(self.folder, 'snapshots')
            usb2.tiff1.file_path.put(self.folder, 'snapshots')
        except:
            pass

            

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
        self.state_from_redis()
        #if os.path.isfile(jsonfile):
        #    self.state_from_redis(jsonfile)
        self.suspenders_engaged = False
        self.trigger = True
            #user = json.load(open(jsonfile))
            # try:
            #     self.element    = rkvs.get('BMM:pds:element').decode('utf-8')
            #     self.edge       = rkvs.get('BMM:pds:edge').decode('utf-8')
            #     self.instrument = rkvs.get('BMM:automation:type').decode('utf-8')
            # except:
            #     self.element, self.edge, self.instrument = None, 'K', ''
        if self.name is not None:
            self.start_experiment(name=self.name, date=self.date, gup=self.gup, saf=self.saf)

    def show_experiment(self):
        '''Show serialized configuration parameters'''
        print('Name          = %s' % self.name)
        print('Date          = %s' % self.date)
        print('Lustre folder = %s' % self.folder)
        print('Local folder  = %s' % self.folder_link)
        print('GUP           = %s' % self.gup)
        print('SAF           = %s' % self.saf)
        #print('foils = %s' % ' '.join(map(str, user_ns['foils'].slots)))
        #if user_ns['with_xspress3'] is False:
        #    print('ROIs   = %s' % ' '.join(map(str, user_ns['rois'].slots)))

    def fetch_echem(self):
        dest = os.path.join(self.folder, 'electrochemistry')
        copy_tree(self.echem_remote, dest)
        report('Copied electrochemistry data from: "%s" to "%s"' % (self.echem_remote, dest), 'bold')

    def end_experiment(self, force=False):
        '''
        Copy data from the experiment that just finished to the NAS, then
        unset the logger and the DATA variable at the end of an experiment.
        '''

        self.echem = False
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
            if False:
                destination = os.path.join(user_ns['nas_mount_point'], 'xf06bm', 'user', self.name, self.date)
                if not os.path.isdir(destination):
                    os.makedirs(destination)
                for d in ('dossier', 'prj', 'snapshots'):
                    if not os.path.isdir(os.path.join(destination, d)):
                        os.makedirs(os.path.join(destination, d))
                try:
                    copy_tree(self.DATA, destination)
                    report('NAS data store: "%s"' % destination, 'bold')
                except Exception as E:
                    print(E)
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
        for thing in ('name', 'gup', 'saf', 'folder', 'folder_link', 'date'):
            rkvs.set(f'BMM:user:{thing}', '')

        
        return None

    def set_instrument(self):
        instruments = ('Single wheel', 'Double wheel', 'Linkam stage', 'Displex + LakeShore', 'Glancing angle stage', 'Motor grid')
        print('Select an instrument:\n')
        for i, inst in enumerate(instruments):
            print(f'  {i+1}: {inst}')
        
        print('  u: unset')
        print('\n  r: return')
        choice = input("\nSelect a file > ")
        try:
            if str(choice.lower()) == 'u':
                print('Unsetting instrument')
                self.instrument = ''
                rkvs.set('BMM:user:instrument', '')
                rkvs.set('BMM:automation:type', '')
            elif int(choice) > 0 and int(choice) <= len(instruments):
                this = instruments[int(choice)-1]
                print(f'You selected "{this}"')
                self.instrument = this
                rkvs.set('BMM:user:instrument', this)
                rkvs.set('BMM:automation:type', this)
            else:
                print('No instrument selected')
                return None
        except Exception as e:
            print(e)
            print('No instrument selected')
            return None
        
    def fix(self):
        '''Using the wrong version of a spreadsheet can set booleans
        incorrectly.  This restores them to their defaults.
        '''
        self.snapshots = True
        self.htmlpage = True
        self.usbstick = False
        self.bothways = False
        self.channelcut = True
        self.ththth = False
        self.lims = True
