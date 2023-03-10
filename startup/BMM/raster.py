
try:
    from bluesky_queueserver import is_re_worker_active
except ImportError:
    # TODO: delete this when 'bluesky_queueserver' is distributed as part of collection environment
    def is_re_worker_active():
        return False

import numpy, os, re, shutil, openpyxl
import textwrap, configparser, datetime
from scipy.io import savemat
import matplotlib.pyplot as plt

from bluesky.plans import count
from bluesky.plan_stubs import sleep, mv, null
from bluesky.preprocessors import subs_decorator, finalize_wrapper

from PIL import Image
from tiled.client import from_profile

from BMM.areascan        import areascan
from BMM.db              import file_resource
from BMM.dossier         import BMMDossier
from BMM.functions       import countdown, boxedtext, now, isfloat, inflect, e2l, etok, ktoe, present_options, plotting_mode, PROMPT
from BMM.functions       import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.gdrive          import copy_to_gdrive, synch_gdrive_folder, rsync_to_gdrive
from BMM.logging         import BMM_log_info, BMM_msg_hook, report, img_to_slack, post_to_slack
from BMM.metadata        import bmm_metadata, display_XDI_metadata, metadata_at_this_moment
from BMM.motor_status    import motor_sidebar, motor_status
from BMM.resting_state   import resting_state_plan
from BMM.suspenders      import BMM_suspenders, BMM_clear_to_start, BMM_clear_suspenders

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

from BMM.user_ns.base      import db, startup_dir, bmm_catalog
from BMM.user_ns.dwelltime import _locked_dwell_time

def read_ini(inifile, **kwargs):

    config = configparser.ConfigParser(interpolation=None)
    config.read_file(open(inifile))
    parameters = dict()
    found = dict()

    ## folder cif url doi + various flags
    BMMuser = user_ns['BMMuser']
    parameters['folder'] = BMMuser.folder
    parameters['url'], parameters['doi'], parameters['cif'] = '', '', ''
    
    ## strings
    for a in ('experimenters', 'detector', 'filename', 'edge', 'element', 'sample', 'prep', 'comment'):
        found[a] = False
        if a in kwargs:
            parameters[a] = str(kwargs[a])
            found[a] = True
        else:
            try:
                parameters[a] = config.get('scan', a)
                found[a] = True
            except:
                if a in ('experimenters', 'edge', 'element'):
                    parameters[a] = getattr(BMMuser, a)
                elif a == 'detector':
                    parameters[a] = 'If'
                else:
                    parameters[a] = None
    parameters['mode'] = 'transmission'
    if parameters['detector'].lower in ('if', 'xs', 'xs1'):
        parameters['mode'] = 'fluorescence'

                    
    ## floats
    for a in ('dwelltime', 'energy'):
        found[a] = False
        if a in kwargs:
            parameters[a] = float(kwargs[a])
            found[a] = True
        else:
            try:
                parameters[a] = float(config.get('scan', a))
                found[a] = True
            except:
                if a == 'dwelltime':
                    parameters[a] = 0.1
                else:
                    parameters[a] = None

    ## booleans
    for a in ('snapshots', 'lims', 'htmlpage', 'usbstick', 'contour', 'log'):
        found[a] = False
        if a in kwargs:
            parameters[a] = kwargs[a]
            found[a] = True
        else:
            try:
                parameters[a] = config.get('scan', a)
                found[a] = True
            except:
                parameters[a] = True
    parameters['ththth'] = False

                    
    ## fast and slow
    found['fast_motor'], found['fast_start'], found['fast_stop'], found['fast_steps'] = False, False, False, False
    found['slow_motor'], found['slow_start'], found['slow_stop'], found['slow_steps'] = False, False, False, False
    if 'fast' in kwargs:
        this = kwargs['fast'].split()
        parameters['fast_motor'] = this[0]
        parameters['fast_start'] = float(this[1])
        parameters['fast_stop']  = float(this[2])
        parameters['fast_steps'] = int(this[3])
        found['fast_motor'], found['fast_start'], found['fast_stop'], found['fast_steps'] = True, True, True, True
    else:
        try:
            this = config.get('scan', 'fast').split()
            parameters['fast_motor'] = this[0]
            parameters['fast_start'] = float(this[1])
            parameters['fast_stop']  = float(this[2])
            parameters['fast_steps'] = int(this[3])
            found['fast_motor'], found['fast_start'], found['fast_stop'], found['fast_steps'] = True, True, True, True
        except:
            parameters['fast_motor'] = None
            parameters['fast_start'] = None
            parameters['fast_stop']  = None
            parameters['fast_steps'] = None
    if 'slow' in kwargs:
        this = kwargs['slow'].split()
        parameters['slow_motor'] = this[0]
        parameters['slow_start'] = float(this[1])
        parameters['slow_stop']  = float(this[2])
        parameters['slow_steps'] = int(this[3])
        found['slow_motor'], found['slow_start'], found['slow_stop'], found['slow_steps'] = True, True, True, True
    else:
        try:
            this = config.get('scan', 'slow').split()
            parameters['slow_motor'] = this[0]
            parameters['slow_start'] = float(this[1])
            parameters['slow_stop']  = float(this[2])
            parameters['slow_steps'] = int(this[3])
            found['slow_motor'], found['slow_start'], found['slow_stop'], found['slow_steps'] = True, True, True, True
        except:
            parameters['slow_motor'] = None
            parameters['slow_start'] = None
            parameters['slow_stop']  = None
            parameters['slow_steps'] = None
            
    return parameters, found


def preserve_data(uid, label, xlsxout, matout):
    '''Save the data from an areascan as a .xlsx file (a simple spreadsheet
    which can be ingested by many plotting programs) and as a .mat
    file (which can be ingested by Matlab).
    '''
    motors = db.v2[uid].metadata['start']['motors']
    print('Reading data set...')
    datatable = db.v2[uid].primary.read()
    
    slow = numpy.array(datatable[motors[0]])
    fast = numpy.array(datatable[motors[1]])
    i0   = numpy.array(datatable['I0'])

    if '4-element SDD' in db.v2[uid].metadata['start']['detectors'] or 'if' in db.v2[uid].metadata['start']['detectors'] or 'xs' in db.v2[uid].metadata['start']['detectors']:
        det_name = db.v2[uid].metadata['start']['plan_name'].split()[-1]
        det_name = det_name[:-1]
        z = numpy.array(datatable[det_name+'1'])+numpy.array(datatable[det_name+'2'])+numpy.array(datatable[det_name+'3'])+numpy.array(datatable[det_name+'4'])
    elif 'noisy_det' in db.v2[uid].metadata['start']['detectors']:
        det_name = 'noisy_det'
        z = numpy.array(datatable['noisy_det'])

    ## save map in xlsx format
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = label
    ws1.append((user_ns[motors[0]].name, user_ns[motors[1]].name, f'{det_name}/I0', det_name, 'I0'))
    for i in range(len(slow)):
        ws1.append((slow[i], fast[i], z[i]/i0[i], z[i], i0[i]))
    wb.save(filename=os.path.join(user_ns['BMMuser'].folder, 'maps', xlsxout))
    print(f'wrote {user_ns["BMMuser"].folder}/maps/{xlsxout}')
    
    ## save map in matlab format 
    savemat(os.path.join(user_ns['BMMuser'].folder, 'maps', matout), {'label'   : label,
                                                                      motors[0] : list(slow),
                                                                      motors[1] : list(fast),
                                                                      'I0'      : list(i0),
                                                                      'signal'  : list(z),})
    print(f'wrote {user_ns["BMMuser"].folder}/maps/{matout}')

def difference_data(uid1, uid2, tag):
    '''Given two UIDs, make a difference map.  The assumption here is that
    uid1 is the UID of the higher energy map, and uid2 is the UID of
    the lower energy (or baseline) map.  

    For example, consider an experiment mapping the Ce3+ and Ce4+
    content of an object.  You might measure one map below the Ce L3
    edge, one map at about 5726 eV (near a XANES peak associated with
    Ce3+), and one map around 5738 eV (near a XANES peak associated
    with Ce4+).  To get the Ce3+ map, uid1 would be the UID of the
    5726 eV map and uid2 would be the map from below the edge.

    This function will write 3 files to the "maps/" folder in the
    user's data folder:
    * <tag>.xlsx : The data as a simple spreadsheet that many plotting programs can ingest
    * <tag>.mat  : The data in a form that Matlab can ingest
    * <tag>.png  : A matplotlib image of the processed difference map

    parameters
    ==========
    uid1 : (str) the UID of the first mapping
    uid2 : (str) the UID of the baseline map
    tag  : (str) a string to use to identify this difference spectrum

    '''

    ## HIP1
    ## 4+ : b9da51fb-a74b-4e86-bf92-e53e01ec763c
    ## 3+ : 66672202-4d35-4e50-869a-9c6fef89cf84
    ## bkg: 7afeb391-782a-4240-a676-4373fdbee301
    
    ## get motor names and image shape
    motors = db.v2[uid1].metadata['start']['motors']
    [nslow, nfast] = db.v2[uid1].metadata['start']['shape']

    ## slurp in data
    print('Reading primary data set...')
    datatable1 = db.v2[uid1].primary.read()
    print('Reading secondary data set...')
    datatable2 = db.v2[uid2].primary.read()

    ## common arrays and I0 arrays
    slow = numpy.array(datatable1[motors[0]])
    fast = numpy.array(datatable1[motors[1]])
    i01  = numpy.array(datatable1['I0'])
    i02  = numpy.array(datatable2['I0'])

    ## grab the signal based on what is listed in 'detectors' in the start document
    if 'xs' in db.v2[uid1].metadata['start']['detectors']:
        det_name = db.v2[uid1].metadata['start']['plan_name'].split()[-1]
        det_name = det_name[:-1]
        z1 = numpy.array(datatable1[det_name+'1'])+numpy.array(datatable1[det_name+'2'])+numpy.array(datatable1[det_name+'3'])+numpy.array(datatable1[det_name+'4'])
        z2 = numpy.array(datatable2[det_name+'1'])+numpy.array(datatable2[det_name+'2'])+numpy.array(datatable2[det_name+'3'])+numpy.array(datatable2[det_name+'4'])
    elif 'noisy_det' in db.v2[uid1].metadata['start']['detectors']:
        z1 = numpy.array(datatable1['noisy_det'])
        z2 = numpy.array(datatable2['noisy_det'])

    ## save map in xlsx format
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = tag
    ws1.append(('slow', 'fast', 'difference', 'normalized_1', 'normalized_2', 'signal_1', 'I0_1', 'signal_2', 'I0_2'))
    n1 = z1/i01
    n2 = z2/i02
    diff = n1 - n2
    for i in range(len(slow)):
        ws1.append((slow[i], fast[i], diff[i], n1[i], n2[i], z1[i], i01[i], z2[i], i02[i]))
    wb.save(filename=os.path.join(user_ns['BMMuser'].folder, 'maps', f'{tag}.xlsx'))
    print(f'wrote {user_ns["BMMuser"].folder}/maps/{tag}.xlsx')
    
    ## save map in matlab format 
    savemat(os.path.join(user_ns['BMMuser'].folder, 'maps', f'{tag}.mat'), {'label'        : tag,
                                                                            motors[0]      : list(slow),
                                                                            motors[1]      : list(fast),
                                                                            'difference'   : list(diff),
                                                                            'normalized_1' : list(n1),
                                                                            'normalized_2' : list(n2),
                                                                            'I0_1'         : list(i01),
                                                                            'signal_1'     : list(z1),
                                                                            'I0_2'         : list(i02),
                                                                            'signal_2'     : list(z2), })
    print(f'wrote {user_ns["BMMuser"]}/maps/{tag}.mat')

    ## make a pretty picture of the difference map
    zzz=diff.reshape(nfast, nslow)
    # grabbing the first nfast elements of x and every
    # nslow-th element of y is more reliable than 
    # numpy.unique due to float &/or motor precision issues

    plt.title(tag)
    plt.xlabel(f'fast axis ({motors[0]}) position (mm)')
    plt.ylabel(f'slow axis ({motors[1]}) position (mm)')
    plt.gca().invert_yaxis()  # plot an xafs_x/xafs_y plot upright
    plt.contourf(fast[:nfast], slow[::nslow], zzz, cmap=plt.cm.viridis)
    plt.colorbar()
    plt.show()
    plt.savefig(os.path.join(user_ns['BMMuser'].folder, 'maps', f'{tag}.png'))

    
    
def raster(inifile=None, **kwargs):
    '''Perform a raster scan of an object. Read parameters from an INI
    file or provide parameters as argument (overriding the content of
    the INI file).

    Plan logic:
    1. Read the INI file and do sanity checking of the parameters
    2. Move to an energy specified in the INI file or in the argument list
    3. If interactive, prompt the user to verify the parameters
    4. Record relevant metadata and snap pictures from all cameras
    5. Do an areascan
    6. Save scan data (I0 and ROIs) as xlsx and matlab
    7. Write a dossier

    '''
    def main_plan(inifile, **kwargs):

        verbose = False
        if 'verbose' in kwargs and kwargs['verbose'] is True:
            verbose = True

        if is_re_worker_active():
            BMMuser.prompt = False
            kwargs['force'] = True

        if verbose: print(verbosebold_msg('checking clear to start (unless force=True)')) 
        if 'force' in kwargs and kwargs['force'] is True:
            (ok, text, force) = (True, '', True)
        else:
            (ok, text) = BMM_clear_to_start()
            if ok is False:
                print(error_msg('\n'+text))
                print(bold_msg('Quitting scan sequence....\n'))
                yield from null()
                return
        
        _locked_dwell_time.quadem_dwell_time.settle_time = 0
        inifile = os.path.join(BMMuser.folder, inifile)


        if inifile is None:
            print(error_msg('\nNo inifile specified\n'))
            return(yield from null())
        if not os.path.isfile(inifile):
            print(error_msg('\ninifile does not exist\n'))
            return(yield from null())

        report(f'== starting raster scan', level='bold', slack=True)

        p, f = read_ini(inifile, **kwargs)
        #print(f)
        #print(p)

        fast  = user_ns[p['fast_motor']]
        slow  = user_ns[p['slow_motor']]

        length = 0
        if BMMuser.prompt:
            text  = '\n'
            addition = f'fast motor: {fast.name} from {p["fast_start"]} to {p["fast_stop"]} in {p["fast_steps"]} steps (current position={fast.position:7.3f})'
            text = text + addition.rstrip() + '\n'
            if len(addition) > length: length = len(addition)
            
            addition = f'slow motor: {slow.name} from {p["slow_start"]} to {p["slow_stop"]} in {p["slow_steps"]} steps (current position={slow.position:7.3f})'
            text = text + addition.rstrip() + '\n\n'
            if len(addition) > length: length = len(addition)
            for k in sorted(p.keys()):
                if 'slow' in k or 'fast' in k:
                    continue
                if k in ('url', 'cif', 'doi'):
                    continue
                addition = f'{k:13} : {p[k]}'
                text = text + addition.rstrip() + '\n'
                if len(addition) > length: length = len(addition)
            boxedtext('How does this look?', text, 'green', width=length+4) # see 05-functions

            pngout  = os.path.join(p['folder'], 'maps', f"{p['filename']}.png")
            basename = p['filename']
            seqnumber = 1
            if os.path.isfile(pngout):
                seqnumber = 2
                while os.path.isfile(os.path.join(p['folder'], 'maps', "%s-%2.2d.png" % (p['filename'],seqnumber))):
                    seqnumber += 1
                basename = "%s-%2.2d" % (p['filename'],seqnumber)
                pngout = os.path.join(BMMuser.DATA, 'maps', "%s-%2.2d.png" % (p['filename'],seqnumber))

            dossier.pngout = os.path.basename(pngout)
            dossier.xlsxout = f"{basename}.xlsx"
            dossier.matout  = f"{basename}.mat"
            print(f'\nImage data to be written to {pngout}, .xslx, and .mat')
            estimate = float(p['fast_steps'])*float(p['slow_steps']) * (float(p['dwelltime'])+0.43)
            minutes = int(estimate/60)
            #seconds = int(estimate - minutes*60)
            print(f'Rough time estimate: {minutes} min')
            
            
            action = input("\nBegin raster scan? " + PROMPT)
            if action.lower() == 'q' or action.lower() == 'n':
                yield from null()
                return

        ## move to measurement energy
        yield from mv(dcm.energy, p['energy'])
                    
        ## gather up input data into a format suitable for the dossier
        with open(inifile, 'r') as fd: content = fd.read()
        output = re.sub(r'\n+', '\n', re.sub(r'\#.*\n', '\n', content)) # remove comment and blank lines
        clargs = textwrap.fill(str(kwargs), width=50) # .replace('\n', '<br>')
        BMM_log_info('starting raster scan using %s:\n%s\ncommand line arguments = %s' % (inifile, output, str(kwargs)))
        #BMM_log_info(motor_status())

        ## organize metadata for injection into database and XDI output
        print(bold_msg('gathering metadata'))
        md = bmm_metadata(measurement   = p['mode'],
                          experimenters = p['experimenters'],
                          edge          = p['edge'],
                          element       = p['element'],
                          edge_energy   = p['energy'],
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
        
        if not os.path.isdir(os.path.join(BMMuser.folder, 'maps')):
            os.makedirs(os.path.join(BMMuser.folder, 'maps'))
        
        #if p['detector'].lower() in ('if', 'xs', 'xs1'):

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## snap photos
        if p['snapshots']:
            yield from dossier.cameras(p['folder'], p['filename'], md)
            
        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## capture dossier metadata for start document
        md['_snapshots'] = {**dossier.cameras_md}

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## show the metadata to the user
        display_XDI_metadata(md)

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## populate the static html page for this scan 
        these_kwargs = {'fast': fast, 'slow': slow,
                        'fast_motor': f'{fast.name} [{p["fast_start"]}:{p["fast_stop"]}], {p["fast_steps"]} steps',
                        'slow_motor': f'{slow.name} [{p["slow_start"]}:{p["slow_stop"]}], {p["slow_steps"]} steps',
                        'fast_init': f'{fast.position:7.3f}', 'slow_init': f'{slow.position:7.3f}' }
        dossier.prep_metadata(p, inifile, clargs, these_kwargs)

        ## --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--
        ## engage suspenders right before starting scan sequence
        if 'force' in kwargs and kwargs['force'] is True:
            force = True
            pass
        else:
            force = False
            BMM_suspenders()
        yield from areascan(p['detector'],
                            slow, p['slow_start'], p['slow_stop'], p['slow_steps'],
                            fast, p['fast_start'], p['fast_stop'], p['fast_steps'],
                            pluck=False, force=force, dwell=p['dwelltime'],
                            fname=pngout, contour=p['contour'], log=p['log'], md=md)
        dossier.scanuid = db.v2[-1].metadata['start']['uid']
        preserve_data(dossier.scanuid, f'{dossier.filename} {dossier.energy} eV', dossier.xlsxout, dossier.matout)
        
    def cleanup_plan(inifile):
        BMM_clear_suspenders()
        try:
            print('Finishing up after a raster scan')
            yield from mv(dossier.fast, float(dossier.fast_init), dossier.slow, float(dossier.slow_init))
            dossier.seqend = now('%A, %B %d, %Y %I:%M %p')
            how = 'finished  :tada:'
            try:
                if 'primary' not in db[-1].stop['num_events']:
                    how = '*stopped*'
                elif db[-1].stop['num_events']['primary'] != db[-1].start['num_points']:
                    how = '*stopped*'
            except:
                how = '*stopped*'
            report(f'== Raster scan {how}', level='bold', slack=True)
            try:
                htmlout = dossier.raster_dossier()
            except Exception as E:
                print(error_msg('Failed to write dossier.  Here is the exception message:'))
                print(E)
                htmlout, prjout, pngout = None, None, None
            if htmlout is not None:
                htmlout = dossier.raster_dossier()
                report('wrote dossier %s' % htmlout, 'bold')
            rsync_to_gdrive()
            synch_gdrive_folder()
        except:
            print(whisper('Quitting raster scan. Not returning to start position or writing dossier.'))
        yield from resting_state_plan()



    RE, BMMuser, dcm, dwell_time = user_ns['RE'], user_ns['BMMuser'], user_ns['dcm'], user_ns['dwell_time']
    xascam, anacam = user_ns['xascam'], user_ns['anacam']
    usbcam1, usbcam2 = user_ns['usbcam1'], user_ns['usbcam2']
    RE.msg_hook = None
    dossier = BMMDossier()
    dossier.measurement = 'raster'

    if is_re_worker_active():
        inifile = '/home/xf06bm/Data/bucket/raster.ini'
    if inifile is None:
        inifile = present_options('ini')
    if inifile is None:
        return(yield from null())
    if inifile[-4:] != '.ini':
        inifile = inifile+'.ini'
    yield from finalize_wrapper(main_plan(inifile, **kwargs), cleanup_plan(inifile))
    RE.msg_hook = BMM_msg_hook
        
