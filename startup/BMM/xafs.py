from bluesky.plans import rel_scan, scan_nd, count
from bluesky.plan_stubs import sleep, mv, null
from bluesky.preprocessors import subs_decorator, finalize_wrapper
#from databroker.core import SingleRunCache

import numpy, os, re, shutil
import textwrap, configparser, datetime
from cycler import cycler
import matplotlib
import matplotlib.pyplot as plt

from urllib.parse import quote

from BMM.db              import file_resource
from BMM.demeter         import toprj
from BMM.derivedplot     import DerivedPlot, interpret_click, close_all_plots, close_last_plot
from BMM.dossier         import BMMDossier
from BMM.functions       import countdown, boxedtext, now, isfloat, inflect, e2l, etok, ktoe, present_options, plotting_mode
from BMM.functions       import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.gdrive          import copy_to_gdrive, synch_gdrive_folder, rsync_to_gdrive
from BMM.linescans       import rocking_curve
from BMM.logging         import BMM_log_info, BMM_msg_hook, report, img_to_slack, post_to_slack
from BMM.metadata        import bmm_metadata, display_XDI_metadata, metadata_at_this_moment
from BMM.modes           import get_mode, describe_mode
from BMM.motor_status    import motor_sidebar, motor_status
from BMM.periodictable   import edge_energy, Z_number, element_name
from BMM.resting_state   import resting_state_plan
from BMM.suspenders      import BMM_suspenders, BMM_clear_to_start, BMM_clear_suspenders
from BMM.xdi             import write_XDI
from BMM.xafs_functions  import conventional_grid, sanitize_step_scan_parameters

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

#from __main__ import db
from BMM.user_ns.base      import db, startup_dir
from BMM.user_ns.dwelltime import _locked_dwell_time
from BMM.user_ns.detectors import quadem1, vor, xs, xs1, use_4element, use_1element

try:
    from bluesky_queueserver import is_re_worker_active
except ImportError:
    # TODO: delete this when 'bluesky_queueserver' is distributed as part of collection environment
    def is_re_worker_active():
        return False



# p = scan_metadata(inifile='/home/bravel/commissioning/scan.ini', filename='humbleblat.flarg', start=10)
# (energy_grid, time_grid, approx_time) = conventional_grid(p['bounds'],p['steps'],p['times'],e0=p['e0'])
# then call bmm_metadata() to get metadata in an XDI-ready format



def next_index(folder, stub):
    '''Find the next numeric filename extension for a filename stub in folder.'''
    listing = os.listdir(folder)
    r = re.compile(re.escape(stub) + '\.\d+')
    results = sorted(list(filter(r.match, listing)))
    if len(results) == 0:
        return 1
    return int(results[-1][-3:]) + 1

## need more error checking:
##   * k^2 times
##   * switch back to energy units after a k-valued boundary?
##   * pre-edge k-values steps & times


    


def scan_metadata(inifile=None, **kwargs):
    """Typical use is to specify an INI file, which contains all the
    metadata relevant to a set of scans.  This function is called with
    one argument:

      parameters = scan_metadata(inifile='/path/to/inifile')

      inifile:  fully resolved path to INI file describing the measurement.

    A dictionary of metadata is returned.

    As part of a multi-scan plan (i.e. a macro), individual metadata
    can be specified as kwargs to override values in the INI file.
    The kwarg keys are the same as the keys in the dictionary which is
    returned:

    Parameters
    ----------
    folder : str
        folder for saved XDI files
    filename : str
        filename stub for saved XDI files
    experimenters [str] 
        names of people involved in this measurements
    e0 : float
        edge energy, reference value for energy grid
    element : str
        one- or two-letter element symbol
    edge : str
        K, L3, L2, or L1
    sample : str
        description of sample, perhaps stoichiometry
    prep : str
        a short statement about sample preparation
    comment : str
        user-supplied comment about the data
    nscan : int
        number of repetitions
    start : int
        starting scan number, XDI file will be filename.###
    snapshots : bool
        True = capture analog and XAS cameras before scan sequence
    usbstick : bool
        True = munge filenames so they can be written to a VFAT USB stick
    rockingcurve  [bool] 
        True = measure rocking curve at pseudo channel cut energy
    lims : bool
        False = force both htmlpage and snapshot to be false
    htmlpage : bool
        True = capture dossier of a scan sequence as a static html page
    bothways : bool
        True = measure in both monochromator directions
    channelcut : bool
        True = measure in pseudo-channel-cut mode
    ththth : bool
        True = measure using the Si(333) reflection
    mode : str
        transmission, fluorescence, or reference -- how to display the data
    bounds : list
        scan grid boundaries (not kwarg-able at this time)
    steps : list
        scan grid step sizes (not kwarg-able at this time)
    times : list
        scan grid dwell times (not kwarg-able at this time)

    Any or all of these can be specified.  Values from the INI file
    are read first, then overridden with specified values.  If values
    are specified neither in the INI file nor in the function call,
    (possibly) sensible defaults are used.

    """
    #frame = inspect.currentframe()          # see https://stackoverflow.com/a/582206 and
    #args  = inspect.getargvalues(frame)[3]  # https://docs.python.org/3/library/inspect.html#inspect.getargvalues

    BMMuser, dcm = user_ns['BMMuser'], user_ns['dcm']
    parameters = dict()

    if inifile is None:
        print(error_msg('\nNo inifile specified\n'))
        return {}, {}
    if not os.path.isfile(inifile):
        print(error_msg('\ninifile does not exist\n'))
        return {}, {}

    config = configparser.ConfigParser(interpolation=None)
    config.read_file(open(inifile))

    found = dict()

    ## ----- scan regions (what about kwargs???)
    for a in ('bounds', 'steps', 'times'):
        found[a] = False
        parameters[a] = []
        if a not in kwargs:
            try:
                #for f in config.get('scan', a).split():
                for f in re.split('[ \t,]+', config.get('scan', a).strip()):
                    try:
                        parameters[a].append(float(f))
                    except:
                        parameters[a].append(f)
                    found[a] = True
            except:
                parameters[a] = getattr(BMMuser, a)
        else:
            this = str(kwargs[a])
            for f in this.split():
                try:
                    parameters[a].append(float(f))
                except:
                    parameters[a].append(f)
            found[a] = True
        parameters['bounds_given'] = parameters['bounds'].copy()

    (problem, text, reference) = sanitize_step_scan_parameters(parameters['bounds'], parameters['steps'], parameters['times'])
    print(text)
    print(f'\nsee: {reference}')
    if problem:
        return {}, {}

    ## ----- strings
    for a in ('folder', 'experimenters', 'element', 'edge', 'filename', 'comment',
              'mode', 'sample', 'prep', 'url', 'doi', 'cif'):
        found[a] = False
        if a not in kwargs:
            try:
                parameters[a] = config.get('scan', a)
                found[a] = True
            except configparser.NoOptionError:
                parameters[a] = getattr(BMMuser, a)
        else:
            parameters[a] = str(kwargs[a])
            found[a] = True

    if not os.path.isdir(parameters['folder']):
        print(error_msg('\nfolder %s does not exist\n' % parameters['folder']))
        return {}, {}
    parameters['mode'] = parameters['mode'].lower()
    
    ## ----- start value
    if 'start' not in kwargs:
        try:
            parameters['start'] = str(config.get('scan', 'start'))
            found['start'] = True
        except configparser.NoOptionError:
            parameters[a] = getattr(BMMuser, a)
    else:
        parameters['start'] = str(kwargs['start'])
        found['start'] = True
    try:
        if parameters['start'] == 'next':
            parameters['start'] = next_index(parameters['folder'],parameters['filename'])
        else:
            parameters['start'] = int(parameters['start'])
    except ValueError:
        print(error_msg('\nstart value must be a positive integer or "next"'))
        parameters['start'] = -1
        found['start'] = False

    ## ----- integers
    for a in ('nscans', 'npoints'):
        found[a] = False
        if a not in kwargs:
            try:
                parameters[a] = int(config.get('scan', a))
                found[a] = True
            except configparser.NoOptionError:
                parameters[a] = getattr(BMMuser, a)
        else:
            parameters[a] = int(kwargs[a])
            found[a] = True

    ## ----- floats
    for a in ('e0', 'inttime', 'dwell', 'delay'):
        found[a] = False
        if a not in kwargs:
            try:
                parameters[a] = float(config.get('scan', a))
                found[a] = True
            except configparser.NoOptionError:
                parameters[a] = getattr(BMMuser, a)
        else:
            parameters[a] = float(kwargs[a])
            found[a] = True

    ## ----- booleans
    for a in ('snapshots', 'htmlpage', 'lims', 'bothways', 'channelcut', 'usbstick', 'rockingcurve', 'ththth'):
        found[a] = False
        if a not in kwargs:
            try:
                parameters[a] = config.getboolean('scan', a)
                found[a] = True
            except configparser.NoOptionError:
                parameters[a] = getattr(BMMuser, a)
        else:
            parameters[a] = bool(kwargs[a])
            found[a] = True
    if parameters['lims'] is False:
        parameters['htmlpage'] = False
        parameters['snapshots'] = False
            
    if dcm._crystal != '111' and parameters['ththth']:
        print(error_msg('\nYou must be using the Si(111) crystal to make a Si(333) measurement\n'))
        return {}, {}

    if not found['e0'] and found['element'] and found['edge']:
        parameters['e0'] = edge_energy(parameters['element'], parameters['edge'])
        if parameters['e0'] is None:
            print(error_msg('\nCannot figure out edge energy from element = %s and edge = %s\n' % (parameters['element'], parameters['edge'])))
            return {}, {}
        else:
            found['e0'] = True
            #print('\nUsing tabulated value of %.1f for the %s %s edge\n' % (parameters['e0'], parameters['element'], parameters['edge']))
        if parameters['e0'] > 23500:
            print(error_msg('\nThe %s %s edge is at %.1f, which is ABOVE the measurement range for BMM\n' %
                            (parameters['element'], parameters['edge'], parameters['e0'])))
            return {}, {}
        if parameters['e0'] < 4000:
            print(error_msg('\nThe %s %s edge is at %.1f, which is BELOW the measurement range for BMM\n' %
                            (parameters['element'], parameters['edge'], parameters['e0'])))
            return {}, {}

            
    return parameters, found



def channelcut_energy(e0, bounds, ththth):
    '''From the scan parameters, find the energy at the center of the angular range of the scan.'''
    dcm = user_ns['dcm']
    for i,s in enumerate(bounds):
        if type(s) is str:
            this = float(s[:-1])
            bounds[i] = ktoe(this)
    amin = dcm.e2a(e0+bounds[0])
    amax = dcm.e2a(e0+bounds[-1])
    if ththth:
        amin = dcm.e2a((e0+bounds[0])/3.0)
        amax = dcm.e2a((e0+bounds[-1])/3.0)
    aave = amin + 1.0*(amax - amin) / 2.0
    wavelength = dcm.wavelength(aave)
    eave = e2l(wavelength)
    return eave


def ini_sanity(found):
    '''Very simple sanity checking of the scan control file.'''
    ok = True
    missing = []
    for a in ('bounds', 'steps', 'times', 'e0', 'element', 'edge', 'filename', 'nscans', 'start'):
        if found[a] is False:
            ok = False
            missing.append(a)
    return (ok, missing)



##########################################################
# --- export a database energy scan entry to an XDI file #
##########################################################
def db2xdi(datafile, key):
    '''
    Export a database entry for an XAFS scan to an XDI file.

    Parameters
    ----------
    datafile : str
        output file name
    key : str
        UID in database


    Examples
    --------

    >>> db2xdi('/path/to/myfile.xdi', 1533)

    >>> db2xdi('/path/to/myfile.xdi', '0783ac3a-658b-44b0-bba5-ed4e0c4e7216')

    '''
    BMMuser = user_ns['BMMuser']
    dfile = datafile
    if BMMuser.DATA not in dfile:
        if 'bucket' not in BMMuser.DATA:
            dfile = os.path.join(BMMuser.DATA, datafile)
    if os.path.isfile(dfile):
        print(error_msg('%s already exists!  Bailing out....' % dfile))
        return
    header = db[key]
    ## sanity check, make sure that db returned a header AND that the header was an xafs scan
    write_XDI(dfile, header)
    print(bold_msg('wrote %s' % dfile))



#########################
# -- the main XAFS scan #
#########################
def xafs(inifile=None, **kwargs):
    '''
    Read an INI file for scan matadata, then perform an XAFS scan sequence.
    '''
    def main_plan(inifile, **kwargs):
        if '311' in dcm._crystal and dcm_x.user_readback.get() < 10:
            BMMuser.final_log_entry = False
            print(error_msg('The DCM is in the 111 position, configured as 311'))
            print(error_msg('\tdcm.x: %.2f mm\t dcm._crystal: %s' % (dcm_x.user_readback.get(), dcm._crystal)))
            yield from null()
            return
        if '111' in dcm._crystal and dcm_x.user_readback.get() > 10:
            BMMuser.final_log_entry = False
            print(error_msg('The DCM is in the 311 position, configured as 111'))
            print(error_msg('\tdcm_x: %.2f mm\t dcm._crystal: %s' % (dcm_x.user_readback.get(), dcm._crystal)))
            yield from null()
            return

        
        verbose = False
        if 'verbose' in kwargs and kwargs['verbose'] is True:
            verbose = True
            
        supplied_metadata = dict()
        if 'md' in kwargs and type(kwargs['md']) == dict:
            supplied_metadata = kwargs['md']
        #if 'purpose' not in supplied_metadata:
        #    this_purpose = purpose('xafs', 'scan_nd', )
        #    supplied_metadata['purpose'] = 'xafs'

        if is_re_worker_active():
            BMMuser.prompt = False
            kwargs['force'] = True

        if verbose: print(verbosebold_msg('checking clear to start (unless force=True)')) 
        if 'force' in kwargs and kwargs['force'] is True:
            (ok, text) = (True, '')
        else:
            (ok, text) = BMM_clear_to_start()
            if ok is False:
                BMMuser.final_log_entry = False
                print(error_msg('\n'+text))
                print(bold_msg('Quitting scan sequence....\n'))
                yield from null()
                return

        ## make sure we are ready to scan
        #yield from mv(_locked_dwell_time.quadem_dwell_time.settle_time, 0)
        #yield from mv(_locked_dwell_time.struck_dwell_time.settle_time, 0)
        _locked_dwell_time.quadem_dwell_time.settle_time = 0
        #_locked_dwell_time.struck_dwell_time.settle_time = 0


        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## user input, find and parse the INI file
        if verbose: print(verbosebold_msg('time estimate')) 
        inifile, estimate = howlong(inifile, interactive=False, **kwargs)
        if estimate == -1:
            BMMuser.final_log_entry = False
            yield from null()
            return
        (p, f) = scan_metadata(inifile=inifile, **kwargs)
        p['channelcut'] = True
        if p['lims'] is False:
            BMMuser.lims = False
        if not any(p):          # scan_metadata returned having printed an error message
            return(yield from null())

        
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## if in xs mode, make sure we are configured correctly
        if plotting_mode(p['mode']) == 'xs' and use_4element is True:
            if (any(getattr(BMMuser, x) is None for x in ('element', 'xs1', 'xs2', 'xs3', 'xs4',
                                                          'xschannel1', 'xschannel2', 'xschannel3', 'xschannel4'))):
                print(error_msg('BMMuser is not configured to measure correctly with the Xspress3 and the 4-element detector'))
                print(error_msg('Likely solution:'))
                print(error_msg('Set element symbol:  BMMuser.element = Fe  # (or whatever...)'))
                print(error_msg('then do:             xs.measure_roi()'))
                return(yield from null())
        if plotting_mode(p['mode']) == 'xs1' and use_1element is True:
            if (any(getattr(BMMuser, x) is None for x in ('element', 'xs8', 'xschannel8'))):
                print(error_msg('BMMuser is not configured to measure correctly with the Xspress3 and the 1-element detector'))
                print(error_msg('Likely solution:'))
                print(error_msg('Set element symbol:  BMMuser.element = Fe  # (or whatever...)'))
                print(error_msg('then do:             xs.measure_roi()'))
                return(yield from null())

        sub_dict = {'*' : '_STAR_',
                    '/' : '_SLASH_',
                    '\\': '_BACKSLASH_',
                    '?' : '_QM_',
                    '%' : '_PERCENT_',
                    ':' : '_COLON_',
                    '|' : '_VERBAR_',
                    '"' : '_QUOTE_',
                    '<' : '_LT_',
                    '>' : '_GT_',
                }
        vfatify = lambda m: sub_dict[m.group()]
        if p['usbstick']:
            new_filename = re.sub(r'[*:?"<>|/\\]', vfatify, p['filename'])
            if new_filename != p['filename']: 
                report('\nChanging filename from "%s" to %s"' % (p['filename'], new_filename), 'error')
                print(error_msg('\nThese characters cannot be in file names copied onto most memory sticks:'))
                print(error_msg('\n\t* : ? % " < > | / \\'))
                print(error_msg('\nSee ')+url_msg('https://en.wikipedia.org/wiki/Filename#Reserved_characters_and_words'))
                p['filename'] = new_filename

            ## 255 character limit for filenames on VFAT
            # if len(p['filename']) > 250:
            #     BMMuser.final_log_entry = False
            #     print(error_msg('\nYour filename is too long,'))
            #     print(error_msg('\nFilenames longer than 255 characters cannot be copied onto most memory sticks,'))
            #     yield from null()
            #     return


        bail = False
        cnt = 0
        for i in range(p['start'], p['start']+p['nscans'], 1):
            cnt += 1
            fname = "%s.%3.3d" % (p['filename'], i)
            if p['usbstick']:
                fname = re.sub(r'[*:?"<>|/\\]', vfatify, fname)
            datafile = os.path.join(p['folder'], fname)
            if os.path.isfile(datafile):
                report('%s already exists!' % (datafile), 'error')
                bail = True
        if bail:
            report('\nOne or more output files already exist!  Quitting scan sequence....\n', 'error')
            BMMuser.final_log_entry = False
            yield from null()
            return

            
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## user verification (disabled by BMMuser.prompt)
        if verbose: print(verbosebold_msg('computing pseudo-channelcut energy'))
        print(p['e0'], p['bounds'], p['ththth'])
        eave = channelcut_energy(p['e0'], p['bounds'], p['ththth'])
        length = 0
        if BMMuser.prompt:
            text = '\n'
            for k in ('bounds', 'bounds_given', 'steps', 'times'):
                addition = '      %-13s : %-50s\n' % (k,p[k])
                text = text + addition.rstrip() + '\n'
                if len(addition) > length: length = len(addition)
            for (k,v) in p.items():
                if k in ('bounds', 'bounds_given', 'steps', 'times'):
                    continue
                if k in ('npoints', 'dwell', 'delay', 'inttime', 'channelcut', 'bothways'):
                    continue
                addition = '      %-13s : %-50s\n' % (k,v)
                text = text + addition.rstrip() + '\n'
                if len(addition) > length: length = len(addition)
                if length < 75: length = 75
            boxedtext('How does this look?', text, 'green', width=length+4) # see 05-functions

            outfile = os.path.join(p['folder'], "%s.%3.3d" % (p['filename'], p['start']))
            print('\nFirst data file to be written to "%s"' % outfile)

            print(estimate)

            if not dcm.suppress_channel_cut:
                if p['ththth']:
                    print('\nSi(111) pseudo-channel-cut energy = %.1f ; %.1f on the Si(333)' % (eave,eave*3))
                else:
                    print('\nPseudo-channel-cut energy = %.1f' % eave)

            action = input("\nBegin scan sequence? [Y/n then Enter] ")
            if action.lower() == 'q' or action.lower() == 'n':
                BMMuser.final_log_entry = False
                yield from null()
                return

        
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## gather up input data into a format suitable for the dossier
        with open(inifile, 'r') as fd: content = fd.read()
        output = re.sub(r'\n+', '\n', re.sub(r'\#.*\n', '\n', content)) # remove comment and blank lines
        clargs = textwrap.fill(str(kwargs), width=50) # .replace('\n', '<br>')
        BMM_log_info('starting XAFS scan using %s:\n%s\ncommand line arguments = %s' % (inifile, output, str(kwargs)))
        BMM_log_info(motor_status())

        ## perhaps enter pseudo-channel-cut mode
        ## need to do this define defining the plotting lambda otherwise
        ## BlueSky gets confused about the plotting window
        #if not dcm.suppress_channel_cut:
        if p['channelcut'] is True:
            report('entering pseudo-channel-cut mode at %.1f eV' % eave, 'bold')
        dcm.mode = 'fixed'
        #dcm_bragg.clear_encoder_loss()
        #if 'noreturn' in kwargs and kwargs['noreturn'] is not True:
        yield from mv(dcm.energy, eave)
        if p['rockingcurve']:
            report('running rocking curve at pseudo-channel-cut energy %.1f eV' % eave, 'bold')
            yield from rocking_curve()
            #RE.msg_hook = None
            close_last_plot()
        if p['channelcut'] is True:
            dcm.mode = 'channelcut'



        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## organize metadata for injection into database and XDI output
        print(bold_msg('gathering metadata'))
        md = bmm_metadata(measurement   = p['mode'],
                          experimenters = p['experimenters'],
                          edge          = p['edge'],
                          element       = p['element'],
                          edge_energy   = p['e0'],
                          direction     = 1,
                          scantype      = 'step',
                          channelcut    = True, # p['channelcut'],
                          mono          = 'Si(%s)' % dcm._crystal,
                          i0_gas        = 'N2', #\
                          it_gas        = 'N2', # > these three need to go into INI file
                          ir_gas        = 'N2', #/
                          sample        = p['sample'],
                          prep          = p['prep'],
                          stoichiometry = None,
                          mode          = p['mode'],
                          comment       = p['comment'],
                          ththth        = p['ththth'],
        )

        
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## measure XRF spectrum at Eave
        xrfuid, xrffile, xrfimage = None, None, None
        image_web, xascam_uid, image_ana, anacam_uid = None, None, None, None
        usbcam1_uid, usbcam2_uid = None, None
        usb1cam_uid, usb2cam_uid = None, None
        image_usb1, image_usb2 = None, None

        dossier.xrffile, dossier.xrfsnap = None, None
        dossier.ocrs = ''
        dossier.rois = ''
        if 'xs' in plotting_mode(p['mode']) and BMMuser.lims is True:
            thisagg = matplotlib.get_backend()
            matplotlib.use('Agg') # produce a plot without screen display
            ahora = now()
            dossier.xrffile = "%s_%s.xrf" % (p['filename'], ahora)
            dossier.xrfsnap = "%s_XRF_%s.png" % (p['filename'], ahora)
            xrffile  = os.path.join(p['folder'], 'XRF', dossier.xrffile)
            xrfimage = os.path.join(p['folder'], 'XRF', dossier.xrfsnap)
            if use_4element and plotting_mode(p['mode']) == 'xs':
                report(f'measuring an XRF spectrum at {eave:.1f} (4-element detector)', 'bold')
                yield from mv(xs.total_points, 1)
                yield from mv(xs.cam.acquire_time, 1)
                xrfuid = yield from count([xs], 1, md = {'XDI':md, 'plan_name' : 'count xafs_metadata XRF'})
                ocrs = [int(xs.get_channel(channel_number=1).get_mcaroi(mcaroi_number=16).total_rbv.get()),
                        int(xs.get_channel(channel_number=2).get_mcaroi(mcaroi_number=16).total_rbv.get()),
                        int(xs.get_channel(channel_number=3).get_mcaroi(mcaroi_number=16).total_rbv.get()),
                        int(xs.get_channel(channel_number=4).get_mcaroi(mcaroi_number=16).total_rbv.get()),]
                rois = [int(BMMuser.xschannel1.get()),
                        int(BMMuser.xschannel2.get()),
                        int(BMMuser.xschannel3.get()),
                        int(BMMuser.xschannel4.get()),]
                xs.plot(uid=xrfuid)
                xs.to_xdi(xrffile)
            if use_1element and plotting_mode(p['mode']) == 'xs1':
                report(f'measuring an XRF spectrum at {eave:.1f} (1-element detector)', 'bold')
                yield from mv(xs1.total_points, 1)
                yield from mv(xs1.cam.acquire_time, 1)
                xrfuid = yield from count([xs1], 1, md = {'XDI':md, 'plan_name' : 'count xafs_metadata XRF'})
                ocrs = [int(xs1.get_channel(channel_number=8).get_mcaroi(mcaroi_number=16).total_rbv.get()),]
                rois = [int(BMMuser.xschannel1.get()),]
                xs1.plot(uid=xrfuid)
                xs1.to_xdi(xrffile)

            ## capture OCR and target ROI values at Eave to report in dossier
            dossier.ocrs = ", ".join(map(str,ocrs))
            dossier.rois = ", ".join(map(str,rois))

            ## save XRF plot
            plt.savefig(xrfimage)
            matplotlib.use(thisagg) # return to screen display

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## snap photos
        #print(disconnected_msg(f"snapshots = {p['snapshots']}"))
        if p['snapshots']:
            ahora = now()

            ### --- XAS webcam ---------------------------------------------------------------
            annotation = p['filename']
            dossier.websnap = "%s_XASwebcam_%s.jpg" % (p['filename'], ahora)
            image_web = os.path.join(p['folder'], 'snapshots', dossier.websnap)
            xascam._annotation_string = annotation
            print(bold_msg('XAS webcam snapshot'))
            xascam_uid = yield from count([xascam], 1, md = {'XDI':md, 'plan_name' : 'count xafs_metadata snapshot'})
            os.symlink(file_resource(db.v2[xascam_uid]), image_web)

            ### --- analog camera using redgo dongle ------------------------------------------
            dossier.anasnap = "%s_analog_%s.jpg" % (p['filename'], ahora)
            image_ana = os.path.join(p['folder'], 'snapshots', dossier.anasnap)
            anacam._annotation_string = p['filename']
            print(bold_msg('analog camera snapshot'))
            anacam_uid = yield from count([anacam], 1, md = {'XDI':md, 'plan_name' : 'count xafs_metadata snapshot'})
            try:
                os.symlink(file_resource(db.v2[anacam_uid]), image_ana)
            except:
                print(error_msg('Could not copy analog snapshot, probably because it\'s capture failed.'))
                pass

            ### --- USB camera #1 --------------------------------------------------------------
            dossier.usb1snap = "%s_usb1_%s.jpg" % (p['filename'], ahora)
            image_usb1 = os.path.join(p['folder'], 'snapshots', dossier.usb1snap)
            usbcam1._annotation_string = p['filename']
            print(bold_msg('USB camera #1 snapshot'))
            usbcam1_uid = yield from count([usbcam1], 1, md = {'XDI':md, 'plan_name' : 'count xafs_metadata snapshot'})
            os.symlink(file_resource(db.v2[usbcam1_uid]), image_usb1)

            ### --- USB camera #2 --------------------------------------------------------------
            dossier.usb2snap = "%s_usb2_%s.jpg" % (p['filename'], ahora)
            image_usb2 = os.path.join(p['folder'], 'snapshots', dossier.usb2snap)
            usbcam2._annotation_string = p['filename']
            print(bold_msg('USB camera #2 snapshot'))
            usbcam2_uid = yield from count([usbcam2], 1, md = {'XDI':md, 'plan_name' : 'count xafs_metadata snapshot'})
            os.symlink(file_resource(db.v2[usbcam2_uid]), image_usb2)

            
        md['_snapshots'] = {'xrf_uid':     xrfuid,     'xrf_image': xrfimage,
                            'webcam_file': image_web,  'webcam_uid': xascam_uid,
                            'analog_file': image_ana,  'anacam_uid': anacam_uid,
                            'usb1_file':   image_usb1, 'usbcam1_uid': usbcam1_uid,
                            'usb2_file':   image_usb1, 'usbcam2_uid': usbcam2_uid, }
            

        #legends = []
        #for i in range(p['start'], p['start']+p['nscans'], 1):
        #    legends.append("%s.%3.3d" % (p['filename'], i))
        
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## set up a plotting subscription, anonymous functions for plotting various forms of XAFS
        test  = lambda doc: (doc['data']['dcm_energy'], doc['data']['I0'])
        trans = lambda doc: (doc['data']['dcm_energy'], numpy.log(doc['data']['I0'] / doc['data']['It']))
        ref   = lambda doc: (doc['data']['dcm_energy'], numpy.log(doc['data']['It'] / doc['data']['Ir']))
        Yield = lambda doc: (doc['data']['dcm_energy'], doc['data']['Iy'] / doc['data']['I0'])
        if user_ns['with_xspress3'] and plotting_mode(p['mode']) == 'xs':
            xspress3_4 = lambda doc: (doc['data']['dcm_energy'], (doc['data'][BMMuser.xs1] +
                                                                  doc['data'][BMMuser.xs2] +
                                                                  doc['data'][BMMuser.xs3] +
                                                                  doc['data'][BMMuser.xs4] ) / doc['data']['I0'])
        if user_ns['with_xspress3'] and plotting_mode(p['mode']) == 'xs1':
            xspress3_1 = lambda doc: (doc['data']['dcm_energy'], doc['data'][BMMuser.xs8] / doc['data']['I0'])
            
        if BMMuser.detector == 1:
            fluo  = lambda doc: (doc['data']['dcm_energy'], doc['data'][BMMuser.dtc1] / doc['data']['I0'])
        else:
            fluo  = lambda doc: (doc['data']['dcm_energy'], (doc['data'][BMMuser.dtc1] +
                                                             doc['data'][BMMuser.dtc2] + # removed doc['data'][BMMuser.dtc3] +
                                                             doc['data'][BMMuser.dtc4]) / doc['data']['I0'])
        if 'fluo'    in p['mode'] or 'flou' in p['mode']:
            if user_ns['with_xspress3']:
                yield from mv(xs.cam.acquire_time, 0.5)
                plot =  DerivedPlot(xspress3_4, xlabel='energy (eV)', ylabel='If / I0 (Xspress3)',        title=p['filename'])
            else:
                plot =  DerivedPlot(fluo,  xlabel='energy (eV)', ylabel='absorption (fluorescence)',    title=p['filename'])
        elif 'trans' in p['mode']:
            plot =  DerivedPlot(trans, xlabel='energy (eV)', ylabel='absorption (transmission)',    title=p['filename'])
        elif 'ref'   in p['mode']:
            plot =  DerivedPlot(ref,   xlabel='energy (eV)', ylabel='absorption (reference)',       title=p['filename'])
        elif 'yield' in p['mode']:
            quadem1.Iy.kind = 'hinted'
            plot = [DerivedPlot(Yield, xlabel='energy (eV)', ylabel='absorption (electron yield)',  title=p['filename']),
                    DerivedPlot(trans, xlabel='energy (eV)', ylabel='absorption (transmission)',    title=p['filename'])]
        elif 'test'  in p['mode']:
            plot =  DerivedPlot(test,  xlabel='energy (eV)', ylabel='I0 (test)',                    title=p['filename'])
        elif 'both'  in p['mode']:
            if user_ns['with_xspress3']:
                yield from mv(xs.cam.acquire_time, 0.5)
                plot = [DerivedPlot(trans, xlabel='energy (eV)', ylabel='absorption (transmission)',      title=p['filename']),
                        DerivedPlot(xspress3_4,  xlabel='energy (eV)', ylabel='absorption (Xspress3)',    title=p['filename'])]
            else:
                plot = [DerivedPlot(trans, xlabel='energy (eV)', ylabel='absorption (transmission)',      title=p['filename']),
                        DerivedPlot(fluo,  xlabel='energy (eV)', ylabel='absorption (fluorescence)',      title=p['filename'])]
        elif 'xs1'   in p['mode']:
            yield from mv(xs1.cam.acquire_time, 0.5)
            plot =  DerivedPlot(xspress3_1, xlabel='energy (eV)', ylabel='If / I0 (Xspress3, 1-element)', title=p['filename'])
        elif 'xs'    in p['mode']:
            yield from mv(xs.cam.acquire_time, 0.5)
            plot =  DerivedPlot(xspress3_4, xlabel='energy (eV)', ylabel='If / I0 (Xspress3, 4-element)', title=p['filename'])
        else:
            print(error_msg('Plotting mode not specified, falling back to a transmission plot'))
            plot =  DerivedPlot(trans, xlabel='energy (eV)', ylabel='absorption (transmission)',          title=p['filename'])


        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## SingleRunCache -- manage data as it comes out
        #src = SingleRunCache()

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## engage suspenders right before starting scan sequence
        if 'force' in kwargs and kwargs['force'] is True:
            pass
        else:
            BMM_suspenders()
            
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## begin the scan sequence with the plotting subscription
        @subs_decorator(plot)
        #@subs_decorator(src.callback)
        def scan_sequence(clargs): #, noreturn=False):
            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## compute energy and dwell grids
            print(bold_msg('computing energy and dwell time grids'))
            (energy_grid, time_grid, approx_time, delta) = conventional_grid(p['bounds'], p['steps'], p['times'], e0=p['e0'], element=p['element'], edge=p['edge'], ththth=p['ththth'])
            if plotting_mode(p['mode']) == 'xs':
                yield from mv(xs.total_points, len(energy_grid))
            if plotting_mode(p['mode']) == 'xs1':
                yield from mv(xs1.total_points, len(energy_grid))
            if energy_grid is None or time_grid is None or approx_time is None:
                print(error_msg('Cannot interpret scan grid parameters!  Bailing out....'))
                BMMuser.final_log_entry = False
                yield from null()
                return
            if any(y > 23500 for y in energy_grid):
                print(error_msg('Your scan goes above 23500 eV, the maximum energy available at BMM.  Bailing out....'))
                BMMuser.final_log_entry = False
                yield from null()
                return
            if dcm._crystal == '111' and any(y > 21200 for y in energy_grid):
                print(error_msg('Your scan goes above 21200 eV, the maximum energy value on the Si(111) mono.  Bailing out....'))
                BMMuser.final_log_entry = False
                yield from null()
                return
            if dcm._crystal == '111' and any(y < 2900 for y in energy_grid): # IS THIS CORRECT???
                print(error_msg('Your scan goes below 2900 eV, the minimum energy value on the Si(111) mono.  Bailing out....'))
                BMMuser.final_log_entry = False
                yield from null()
                return
            if dcm._crystal == '311' and any(y < 5500 for y in energy_grid):
                print(error_msg('Your scan goes below 5500 eV, the minimum energy value on the Si(311) mono.  Bailing out....'))
                BMMuser.final_log_entry = False
                yield from null()
                return



            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## show the metadata to the user
            display_XDI_metadata(md)
                
            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## this dictionary is used to populate the static html page for this scan sequence
            dossier.filename      = p['filename']
            dossier.experimenters = p['experimenters']
            dossier.start         = p['start']
            dossier.end           = p['start']+p['nscans']-1
            dossier.seqstart      = now('%A, %B %d, %Y %I:%M %p')
            dossier.e0            = p['e0']
            dossier.element       = p['element']
            dossier.edge          = p['edge']
            dossier.motors        = motor_sidebar() # this could be motor_sidebar(uid=uid)
            dossier.sample        = p['sample']
            dossier.prep          = p['prep']
            dossier.comment       = p['comment']
            dossier.mode          = p['mode']
            dossier.pccenergy     = eave
            # see https://stackoverflow.com/a/5445983 for list o string idiom
            dossier.bounds        = ' '.join(map(str, p['bounds_given'])) 
            dossier.steps         = ' '.join(map(str, p['steps']))
            dossier.times         = ' '.join(map(str, p['times']))
            dossier.clargs        = clargs
            dossier.htmlpage      = p['htmlpage']
            dossier.ththth        = p['ththth']
            dossier.xrfuid        = xrfuid
            dossier.webuid        = xascam_uid
            dossier.anauid        = anacam_uid
            dossier.usb1uid       = usbcam1_uid
            dossier.usb2uid       = usbcam2_uid
            ## https://www.codespeedy.com/check-if-a-string-is-a-valid-url-or-not-in-python/
            dossier.url           = p['url']
            dossier.doi           = p['doi']
            dossier.cif           = p['cif']
            dossier.temperature   = ''
            with open(os.path.join(BMMuser.DATA, inifile)) as f:
                dossier.initext = ''.join(f.readlines())

                
            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## store data in redis, used by cadashboard
            rkvs.set('BMM:scan:type',      'xafs')
            rkvs.set('BMM:scan:starttime', str(datetime.datetime.timestamp(datetime.datetime.now())))
            rkvs.set('BMM:scan:estimated', (approx_time * int(p['nscans']) * 60))
                
            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## loop over scan count
            close_last_plot()
            report(f'Beginning measurement of "{p["filename"]}", {p["element"]} {p["edge"]} edge, {inflect("scans", p["nscans"])}',
                   level='bold', slack=True)
            cnt = 0
            uidlist = []
            for i in range(p['start'], p['start']+p['nscans'], 1):
                cnt += 1
                fname = "%s.%3.3d" % (p['filename'], i)
                datafile = os.path.join(p['folder'], fname)
                if os.path.isfile(datafile):
                    ## shouldn't be able to get here, unless a file
                    ## was written since the scan sequence began....
                    report('%s already exists! (How did that happen?) Bailing out....' % (datafile), 'error')
                    yield from null()
                    return

                slotno, ring = '', ''
                if 'wheel' in BMMuser.instrument.lower():
                    slotno = f', slot {xafs_wheel.current_slot()}'
                    ring = f' {xafs_wheel.slot_ring()} ring'
                    dossier.instrument = xafs_wheel.dossier_entry();
                elif 'glancing angle' in BMMuser.instrument.lower():
                    slotno = f', spinner {ga.current()}'
                    dossier.instrument = ga.dossier_entry();
                elif 'lakeshore' in BMMuser.instrument.lower():
                    slotno = f', temperature {lakeshore.readback.get():.1f}'
                    dossier.instrument = lakeshore.dossier_entry();
                elif 'linkam' in BMMuser.instrument.lower():
                    slotno = f', temperature {linkam.readback.get():.1f}'
                    dossier.instrument = linkam.dossier_entry();
                # this one is a bit different, get dossier entry from gmb object,
                # there is no grid object....
                elif 'grid' in BMMuser.instrument.lower():
                    slotno = f', motor grid {gmb.motor1.name}, {gmb.motor2.name} = {gmb.position1:.1f}, {gmb.position2:.1f}'
                    dossier.instrument = gmb.dossier_entry();

                    
                report(f'starting repetition {cnt} of {p["nscans"]} -- {fname} -- {len(energy_grid)} energy points{slotno}{ring}', level='bold', slack=True)
                md['_filename'] = fname

                if plotting_mode(p['mode']) == 'xs':
                    yield from mv(xs.spectra_per_point, 1) 
                    yield from mv(xs.total_points, len(energy_grid))
                    hdf5_uid = xs.hdf5.file_name.value
                if plotting_mode(p['mode']) == 'xs1':
                    yield from mv(xs1.spectra_per_point, 1) 
                    yield from mv(xs1.total_points, len(energy_grid))
                    hdf5_uid = xs1.hdf5.file_name.value
                
                ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
                ## compute trajectory
                energy_trajectory    = cycler(dcm.energy, energy_grid)
                dwelltime_trajectory = cycler(dwell_time, time_grid)

                ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
                ## need to set certain metadata items on a per-scan basis... temperatures, ring stats
                ## mono direction, ... things that can change during or between scan sequences
                
                md['Mono']['direction'] = 'forward'
                if p['bothways'] and cnt%2 == 0:
                    energy_trajectory    = cycler(dcm.energy, energy_grid[::-1])
                    dwelltime_trajectory = cycler(dwell_time, time_grid[::-1])
                    md['Mono']['direction'] = 'backward'
                    #dcm_bragg.clear_encoder_loss()
                    yield from mv(dcm.energy, energy_grid[-1]+5)
                else:
                    ## if not measuring in both direction, lower acceleration of the mono
                    ## for the rewind, explicitly rewind, then reset for measurement
                    yield from mv(dcm_bragg.acceleration, BMMuser.acc_slow)
                    print(whisper('  Rewinding DCM to %.1f eV with acceleration time = %.2f sec' % (energy_grid[0]-5, dcm_bragg.acceleration.get())))
                    #dcm_bragg.clear_encoder_loss()
                    yield from mv(dcm.energy, energy_grid[0]-5)
                    yield from mv(dcm_bragg.acceleration, BMMuser.acc_fast)
                    print(whisper('  Resetting DCM acceleration time to %.2f sec' % dcm_bragg.acceleration.get()))
                    
                rightnow = metadata_at_this_moment() # see metadata.py
                for family in rightnow.keys():       # transfer rightnow to md
                    if type(rightnow[family]) is dict:
                        if family not in md:
                            md[family] = dict()
                        for k in rightnow[family].keys():
                            md[family][k] = rightnow[family][k]
                
                md['_kind'] = 'xafs'
                if p['ththth']: md['_kind'] = '333'
                if plotting_mode(p['mode']) == 'xs1':
                    md['_dtc'] = (BMMuser.xs8,)
                elif plotting_mode(p['mode']) == 'xs':
                    md['_dtc'] = (BMMuser.xs1, BMMuser.xs2, BMMuser.xs3, BMMuser.xs4)
                else:
                    md['_dtc'] = (BMMuser.dtc1, BMMuser.dtc2, BMMuser.dtc3, BMMuser.dtc4)
                
                xdi = {'XDI': md}
                #mtr = {'BMM_motors' : motor_metadata()}
                
                ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
                ## call the stock scan_nd plan with the correct detectors
                uid = None
                if any(md in p['mode'] for md in ('trans', 'ref', 'yield', 'test')):
                    uid = yield from scan_nd([quadem1], energy_trajectory + dwelltime_trajectory,
                                             md={**xdi, **supplied_metadata, 'plan_name' : f'scan_nd xafs {p["mode"]}'})
                elif user_ns['with_xspress3'] is True and plotting_mode(p['mode']) == 'xs':
                    uid = yield from scan_nd([quadem1, xs], energy_trajectory + dwelltime_trajectory,
                                             md={**xdi, **supplied_metadata, 'plan_name' : 'scan_nd xafs fluorescence'})
                elif user_ns['with_xspress3'] is True and plotting_mode(p['mode']) == 'xs1':
                    uid = yield from scan_nd([quadem1, xs1], energy_trajectory + dwelltime_trajectory,
                                             md={**xdi, **supplied_metadata, 'plan_name' : 'scan_nd xafs fluorescence'})
                else:
                    uid = yield from scan_nd([quadem1, vor], energy_trajectory + dwelltime_trajectory,
                                             md={**xdi, **supplied_metadata, 'plan_name' : 'scan_nd xafs fluorescence'})
                ## here is where we would use the new SingleRunCache solution in databroker v1.0.3
                ## see #64 at https://github.com/bluesky/tutorials

                if 'xs' in plotting_mode(p['mode']):
                    hdf5_uid = xs.hdf5.file_name.value
                
                uidlist.append(uid)
                header = db[uid]
                write_XDI(datafile, header)
                print(bold_msg('wrote %s' % datafile))
                BMM_log_info(f'energy scan finished, uid = {uid}, scan_id = {header.start["scan_id"]}\ndata file written to {datafile}')

                ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
                ## data evaluation + message to Slack
                ## also sync data with Google Drive
                if any(md in p['mode'] for md in ('trans', 'fluo', 'flou', 'both', 'ref', 'xs', 'xs1', 'yield')):
                    try:
                        score, emoji = user_ns['clf'].evaluate(uid, mode=plotting_mode(p['mode']))
                        report(f"ML data evaluation model: {emoji}", level='bold', slack=True)
                        if score == 0:
                            report('A failed data evaluation does not necessarily mean that there is anything wrong with your data. These data will be investigated and used to refine the data evaluation model.', level='whisper', slack=True)
                            with open('/home/xf06bm/Data/bucket/failed_data_evaluation.txt', 'a') as f:
                                f.write(f'{now()}\n\tmode = {p["mode"]}/{plotting_mode(p["mode"])}\n\t{uid}\n\n')
                    except:
                        pass
                    if p['lims'] is True:
                        try:
                            rsync_to_gdrive()
                            synch_gdrive_folder()
                        except Exception as e:
                            print(error_msg(e))
                            report(f'Failed to push {fname} to Google drive...', level='bold', slack=True)
                        
                ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
                ## generate left sidebar text for the static html page for this scan sequence
                js_text = f'<a href="javascript:void(0)" onclick="toggle_visibility(\'{fname}\');" title="This is the scan number for {fname}, click to show/hide its UID">#{header.start["scan_id"]}</a><div id="{fname}" style="display:none;"><small>{uid}</small></div>'
                ##% (fname, fname, header.start['scan_id'], fname, uid)
                printedname = fname
                if len(p['filename']) > 11:
                    printedname = fname[0:6] + '&middot;&middot;&middot;' + fname[-5:]
                dossier.scanlist += f'<li><a href="../{quote(fname)}" title="Click to see the text of {fname}">{printedname}</a>&nbsp;&nbsp;&nbsp;&nbsp;{js_text}</li>\n' 
                #                  % (quote(fname), fname, printedname, js_text)


            ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
            ## finish up, close out
            dossier.uidlist = uidlist
            dossier.seqend = now('%A, %B %d, %Y %I:%M %p')
            print('Returning to fixed exit mode') #  and returning DCM to %1.f' % eave)
            dcm.mode = 'fixed'
            #yield from mv(dcm_bragg.acceleration, BMMuser.acc_slow)
            #dcm_bragg.clear_encoder_loss()
            #yield from mv(dcm.energy, eave)
            #yield from mv(dcm_bragg.acceleration, BMMuser.acc_fast)

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## execute this scan sequence plan
        yield from scan_sequence(clargs) #, noreturn)

    def cleanup_plan(inifile):
        print('Finishing up after an XAFS scan sequence')
        BMM_clear_suspenders()

        #db = user_ns['db']
        ## db[-1].stop['num_events']['primary'] should equal db[-1].start['num_points'] for a complete scan
        how = 'finished  :tada:'
        try:
            if 'primary' not in db[-1].stop['num_events']:
                how = '*stopped*'
            elif db[-1].stop['num_events']['primary'] != db[-1].start['num_points']:
                how = '*stopped*'
        except:
            how = '*stopped*'
        if BMMuser.final_log_entry is True:
            report(f'== XAFS scan sequence {how}', level='bold', slack=True)
            BMM_log_info(f'most recent uid = {db[-1].start["uid"]}, scan_id = {db[-1].start["scan_id"]}')
            ## FYI: db.v2[-1].metadata['start']['scan_id']
            #if dossier.htmlpage:
            try:
                htmlout = dossier.write_dossier()
            except Exception as E:
                print(error_msg('Failed to write dossier.  Here is the exception message:'))
                print(E)
                htmlout, prjout, pngout = None, None, None
            if htmlout is not None:
                report('wrote dossier %s' % htmlout, 'bold')
        rsync_to_gdrive()
        synch_gdrive_folder()
                    
        dcm.mode = 'fixed'
        yield from resting_state_plan()
        yield from sleep(2.0)
        yield from mv(dcm_pitch.kill_cmd, 1)
        yield from mv(dcm_roll.kill_cmd, 1)

    RE, BMMuser, dcm, dwell_time = user_ns['RE'], user_ns['BMMuser'], user_ns['dcm'], user_ns['dwell_time']
    dcm_bragg, dcm_pitch, dcm_roll, dcm_x = user_ns['dcm_bragg'], user_ns['dcm_pitch'], user_ns['dcm_roll'], user_ns['dcm_x']
    #quadem1, vor = user_ns['quadem1'], user_ns['vor']
    xafs_wheel, ga, linkam, gmb, lakeshore = user_ns['xafs_wheel'], user_ns['ga'], user_ns['linkam'], user_ns['gmb'], user_ns['lakeshore']
    xascam, anacam = user_ns['xascam'], user_ns['anacam']
    usbcam1, usbcam2 = user_ns['usbcam1'], user_ns['usbcam2']
    rkvs = user_ns['rkvs']

    try:
        dualio = user_ns['dualio']
    except:
        pass
    ######################################################################
    # this is a tool for verifying a macro.  this replaces an xafs scan  #
    # with a sleep, allowing the user to easily map out motor motions in #
    # a macro                                                            #
    if BMMuser.macro_dryrun:
        inifile, estimate = howlong(inifile, interactive=False, **kwargs)
        (p, f) = scan_metadata(inifile=inifile, **kwargs)
        if 'filename' in p:
            print(info_msg('\nBMMuser.macro_dryrun is True.  Sleeping for %.1f seconds at sample "%s".\n' %
                           (BMMuser.macro_sleep, p['filename'])))
        else:
            print(info_msg('\nBMMuser.macro_dryrun is True.  Sleeping for %.1f seconds.\nAlso there seems to be a problem with "%s".\n' %
                           (BMMuser.macro_sleep, inifile)))
        countdown(BMMuser.macro_sleep)
        return(yield from null())
    ######################################################################
    dossier = BMMDossier()
    BMMuser.final_log_entry = True
    RE.msg_hook = None
    if BMMuser.lims is False:
        BMMuser.snapshot = False
        BMMuser.htmlout  = False

    if is_re_worker_active():
        inifile = '/home/xf06bm/Data/bucket/scan.ini'
    if inifile is None:
        inifile = present_options('ini')
    if inifile is None:
        return(yield from null())
    if inifile[-4:] != '.ini':
        inifile = inifile+'.ini'
    yield from finalize_wrapper(main_plan(inifile, **kwargs), cleanup_plan(inifile))
    RE.msg_hook = BMM_msg_hook


def howlong(inifile=None, interactive=True, **kwargs):
    '''
    Estimate how long the scan sequence in an XAFS control file will take.
    Parameters from control file are composable via kwargs.

    Examples
    --------
    Interactive (command line) use:
        
    >>> howlong('scan.ini')

    Non-interactive use (for instance, to display the control file contents and a time estimate):
        
    >>> howlong('scan.ini', interactive=False)

    '''

    ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
    ## user input, find and parse the INI file
    ## try inifile as given then DATA + inifile
    ## this allows something like RE(xafs('myscan.ini')) -- short 'n' sweet
    if is_re_worker_active():
        inifile = '/home/xf06bm/Data/bucket/scan.ini'
    BMMuser = user_ns['BMMuser']
    if inifile is None:
        inifile = present_options('ini')
    if inifile is None:
        return('', -1)
    if inifile[-4:] != '.ini':
        inifile = inifile+'.ini'
    orig = inifile
    if not os.path.isfile(inifile):
        inifile = os.path.join(BMMuser.DATA, inifile)
        if not os.path.isfile(inifile):
            print(warning_msg('\n%s does not exist!  Bailing out....\n' % orig))
            return(orig, -1)
    print(bold_msg('reading ini file: %s' % inifile))
    (p, f) = scan_metadata(inifile=inifile, **kwargs)
    if not p:
        print(error_msg('%s could not be read as an XAFS control file\n' % inifile))
        return(orig, -1)
    (ok, missing) = ini_sanity(f)
    if not ok:
        print(error_msg('\nThe following keywords are missing from your INI file: '), '%s\n' % str.join(', ', missing))
        return(orig, -1)
    (energy_grid, time_grid, approx_time, delta) = conventional_grid(p['bounds'], p['steps'], p['times'], e0=p['e0'], element=p['element'], edge=p['edge'], ththth=p['ththth'])
    if delta == 0:
        text = f'One scan of {len(energy_grid)} points will take about {approx_time} minutes\n'
        text +=f'The sequence of {inflect("scan", p["nscans"])} will take about {approx_time * int(p["nscans"])/60:.1f} hours'
    else:
        text = f'One scan of {len(energy_grid)} points will take {approx_time} minutes +/- {delta} minutes \n'
        text +=f'The sequence of {inflect("scan", p["nscans"])} will take about {approx_time * int(p["nscans"])/60:.1f} hours +/- {delta*numpy.sqrt(int(p["nscans"])):.1f} minutes'


    if interactive:
        length = 0
        bt = '\n'
        for k in ('bounds', 'bounds_given', 'steps', 'times'):
            addition = '      %-13s : %-50s\n' % (k,p[k])
            bt = bt + addition.rstrip() + '\n'
            if len(addition) > length: length = len(addition)
        for (k,v) in p.items():
            if k in ('bounds', 'bounds_given', 'steps', 'times'):
                continue
            if k in ('npoints', 'dwell', 'delay', 'inttime', 'channelcut', 'bothways'):
                continue
            addition = '      %-13s : %-50s\n' % (k,v)
            bt = bt + addition.rstrip() + '\n'
            if len(addition) > length: length = len(addition)
            if length < 75: length = 75
        boxedtext('Control file contents', bt, 'cyan', width=length+4) # see 05-functions
        print(text)
    else:
        return(inifile, text)


def xafs_grid(inifile=None, **kwargs):
    '''
    Return the energy and time grids specified in an INI file.

    '''

    ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
    ## user input, find and parse the INI file
    ## try inifile as given then DATA + inifile
    ## this allows something like RE(xafs('myscan.ini')) -- short 'n' sweet
    BMMuser = user_ns['BMMuser']
    if inifile is None:
        inifile = present_options('ini')
    if inifile is None:
        return('', -1)
    if inifile[-4:] != '.ini':
        inifile = inifile+'.ini'
    orig = inifile
    if not os.path.isfile(inifile):
        inifile = os.path.join(BMMuser.DATA, inifile)
        if not os.path.isfile(inifile):
            print(warning_msg('\n%s does not exist!  Bailing out....\n' % orig))
            return(orig, -1)
    print(bold_msg('reading ini file: %s' % inifile))
    (p, f) = scan_metadata(inifile=inifile, **kwargs)
    if not p:
        print(error_msg('%s could not be read as an XAFS control file\n' % inifile))
        return(orig, -1)
    (ok, missing) = ini_sanity(f)
    if not ok:
        print(error_msg('\nThe following keywords are missing from your INI file: '), '%s\n' % str.join(', ', missing))
        return(orig, -1)
    (energy_grid, time_grid, approx_time, delta) = conventional_grid(p['bounds'], p['steps'], p['times'], e0=p['e0'], element=p['element'], edge=p['edge'], ththth=p['ththth'])
    print(f'{p["element"]} {p["edge"]}')
    return(energy_grid, time_grid)
