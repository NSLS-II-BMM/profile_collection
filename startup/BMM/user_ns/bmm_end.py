try:
    from bluesky_queueserver import is_re_worker_active
except ImportError:
    # TODO: delete this when 'bluesky_queueserver' is distributed as part of collection environment
    def is_re_worker_active():
        return False

import os, textwrap
from BMM.functions import run_report, disconnected_msg, error_msg, whisper, boxedtext
from BMM.workspace import rkvs

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

from BMM.user_ns.bmm import BMM_CONFIGURATION_LOCATION, BMMuser, rois
from BMM.user_ns.motors import mcs8_motors

run_report(__file__, text='import the rest of the things')

run_report('\t'+'resting state')
from BMM.resting_state import resting_state, resting_state_plan, end_of_macro

run_report('\t'+'motor status reporting')
from BMM.motor_status import motor_metadata, motor_status, ms, motor_sidebar, xrd_motors, xrdm

run_report('\t'+'derived plot')
from BMM.derivedplot import close_all_plots, close_last_plot, interpret_click

run_report('\t'+'suspenders')
from BMM.suspenders import BMM_suspenders, BMM_clear_to_start, BMM_clear_suspenders

run_report('\t'+'linescan, rocking curve, slit_height, pluck')
from BMM.linescans import linescan, pluck, rocking_curve, slit_height, ls2dat, find_slot, rectangle_scan

run_report('\t'+'wafers!')
from BMM.wafer import Wafer
wafer = Wafer()


#run_report('\t'+'positioning of instruments')
#from BMM.positioning import find_slot

###########################################################################################
#  _____  _       ___   _   _ _____ _____ _   _ _____    ___   _   _ _____  _      _____  #
# |  __ \| |     / _ \ | \ | /  __ \_   _| \ | |  __ \  / _ \ | \ | |  __ \| |    |  ___| #
# | |  \/| |    / /_\ \|  \| | /  \/ | | |  \| | |  \/ / /_\ \|  \| | |  \/| |    | |__   #
# | | __ | |    |  _  || . ` | |     | | | . ` | | __  |  _  || . ` | | __ | |    |  __|  #
# | |_\ \| |____| | | || |\  | \__/\_| |_| |\  | |_\ \ | | | || |\  | |_\ \| |____| |___  #
#  \____/\_____/\_| |_/\_| \_/\____/\___/\_| \_/\____/ \_| |_/\_| \_/\____/\_____/\____/  #
###########################################################################################


run_report('\tglancing angle stage')
from BMM.glancing_angle import GlancingAngle, GlancingAngleMacroBuilder
ga = GlancingAngle('XF:06BMB-CT{DIODE-Local:1}', name='glancing angle stage')

gawheel = GlancingAngleMacroBuilder()
gawheel.description = 'the glancing angle stage'
gawheel.instrument  = 'glancing angle'
gawheel.folder = BMMuser.folder
gawheel.cleanup = 'yield from mv(xafs_x, samx, xafs_pitch, samp, xafs_det, 205)\n        yield from ga.reset()'
gawheel.initialize = 'samx, samp = xafs_x.position, xafs_pitch.position'


#########################################################################################
# ___  ___  ___  _____ ______ _____  ______ _   _ _____ _    ______ ___________  _____  #
# |  \/  | / _ \/  __ \| ___ \  _  | | ___ \ | | |_   _| |   |  _  \  ___| ___ \/  ___| #
# | .  . |/ /_\ \ /  \/| |_/ / | | | | |_/ / | | | | | | |   | | | | |__ | |_/ /\ `--.  #
# | |\/| ||  _  | |    |    /| | | | | ___ \ | | | | | | |   | | | |  __||    /  `--. \ #
# | |  | || | | | \__/\| |\ \\ \_/ / | |_/ / |_| |_| |_| |___| |/ /| |___| |\ \ /\__/ / #
# \_|  |_/\_| |_/\____/\_| \_|\___/  \____/ \___/ \___/\_____/___/ \____/\_| \_|\____/  #
#########################################################################################

from BMM.functions import present_options, bold_msg
from openpyxl import load_workbook

def xlsx():
    '''Prompt for a macro building spreadsheet for any instrument. Use the
    content of cell B1 to direct this spreadsheet to the correct builder.

    if cell B1 is "Glancing angle" --> build a glancing angle macro

    if cell B1 is "Sample wheel" --> build a sample wheel macro

    if cell B1 is empty --> build a sample wheel macro

    Then prompt for the sheet, if there are more than 1 sheet in the
    spreadsheet file.
    
    '''
    spreadsheet = present_options('xlsx')
    if spreadsheet is None:
        print(error_msg('No spreadsheet specified!'))
        return None

    wb = load_workbook(os.path.join(BMMuser.folder, spreadsheet), read_only=True);
    #ws = wb.active
    sheets = wb.sheetnames
    if len(sheets) == 1:
        sheet = sheets[0]
    elif len(sheets) == 2 and 'Version history' in sheets:
        sheet = sheets[0]
    else:
        print(f'Select a sheet from {spreadsheet}:\n')
        actual = [];
        for i,x in enumerate(sheets):
            if x == 'Version history':
                continue
            print(f' {i+1:2}: {x}')
            actual.append(x)

        print('\n  r: return')
        choice = input("\nSelect a sheet > ")
        try:
            if int(choice) > 0 and int(choice) <= len(actual):
                sheet = actual[int(choice)-1]
            else:
                print('No sheet specified')
                return
        except Exception as E:
            print(E)
            print('No sheet specified')
            return
    instrument = str(wb[sheet]['B1'].value).lower()

    if instrument.lower() == 'glancing angle':
        print(bold_msg('This is a glancing angle spreadsheet'))
        gawheel.spreadsheet(spreadsheet, sheet)
        BMMuser.instrument = 'glancing angle stage'
    elif instrument.lower() == 'double wheel':
        print(bold_msg('This is a double sample wheel spreadsheet'))
        wmb.spreadsheet(spreadsheet, sheet, double=True)
        BMMuser.instrument = 'double wheel'
    elif instrument.lower() == 'linkam':
        print(bold_msg('This is a Linkam spreadsheet'))
        lmb.spreadsheet(spreadsheet, sheet)
        BMMuser.instrument = 'Linkam stage'
    elif instrument.lower() == 'lakeshore':
        print(bold_msg('This is a LakeShore spreadsheet'))
        lsmb.spreadsheet(spreadsheet, sheet)
        BMMuser.instrument = 'LakeShore 331'
    elif instrument.lower() == 'grid':
        print(bold_msg('This is a motor grid spreadsheet'))
        gmb.spreadsheet(spreadsheet, sheet)
        BMMuser.instrument = 'motor grid'
    else:
        print(bold_msg('This is a sample wheel spreadsheet'))
        wmb.spreadsheet(spreadsheet, sheet, double=False)
        BMMuser.instrument = 'sample wheel'
    rkvs.set('BMM:automation:type', instrument)


def set_instrument(instrument=None):
    if instrument.lower() == 'glancing angle':
        print(bold_msg('Setting instrument as glancing angle stage'))
        BMMuser.instrument = 'glancing angle stage'
    elif instrument.lower() == 'double wheel':
        print(bold_msg('Setting instrument as double sample wheel'))
        BMMuser.instrument = 'double wheel'
    elif instrument.lower() == 'linkam':
        print(bold_msg('Setting instrument as Linkam stage'))
        BMMuser.instrument = 'Linkam stage'
    elif instrument.lower() == 'lakeshore':
        print(bold_msg('Setting instrument as LakeShore 331'))
        BMMuser.instrument = 'LakeShore'
    elif instrument.lower() == 'grid':
        print(bold_msg('Setting instrument as sample grid'))
        BMMuser.instrument = 'motor grid'
    else:
        print(bold_msg('Default instrument choice: sample wheel'))
        BMMuser.instrument = 'sample wheel'
    rkvs.set('BMM:automation:type', instrument)
    
    




        

run_report('\t'+'areascan')
from BMM.areascan import areascan, as2dat

run_report('\t'+'timescan')
from BMM.timescan import timescan, ts2dat

run_report('\t'+'energystep')
from BMM.energystep import energystep

run_report('\t'+'other plans')
from BMM.plans import tu, td, mvbct, mvrbct, mvbender, mvrbender
from BMM.plans import recover_mirror2, recover_mirror3, recover_mirrors, recover_diagnostics, recover_slits2, recover_slits3

run_report('\t'+'change_mode, change_xtals')
from BMM.modes import change_mode, describe_mode, get_mode, mode, read_mode_data, change_xtals, pds_motors_ready

if os.path.isfile(os.path.join(BMM_CONFIGURATION_LOCATION, 'Modes.json')):
     MODEDATA = read_mode_data()
if BMMuser.pds_mode is None:
     BMMuser.pds_mode = get_mode()


run_report('\t'+'change_edge')
from BMM.edge import show_edges, change_edge
from BMM.functions import approximate_pitch


XDI_record = {'xafs_linx'                        : (True,  'Sample.x'),
              'xafs_x'                           : (True,  'Sample.x'),
              'xafs_liny'                        : (True,  'Sample.y'),
              'xafs_y'                           : (True,  'Sample.y'),
              'xafs_lins'                        : (True,  'Sample.SDD_position'),
              'xafs_det'                         : (True,  'Sample.SDD_position'),
              'xafs_linxs'                       : (False, 'BMM.sample_ref_position'),
              'xafs_pitch'                       : (False, 'Sample.pitch'),
              'xafs_roll'                        : (False, 'BMM.sample_roll_position'),
              'xafs_roth'                        : (False, 'BMM.sample_roth_position'),
              'xafs_wheel'                       : (False, 'BMM.sample_wheel_position'),
              'xafs_ref'                         : (False, 'BMM.sample_ref_position'),
              'xafs_rots'                        : (False, 'BMM.sample_rots_position'),
              'first_crystal_temperature'        : (False, 'BMM.mono_first_crystal_temperature'),
              'compton_shield_temperature'       : (False, 'BMM.mono_compton_shield_temperature'),
              'dm3_bct'                          : (False, 'BMM.beamline_bct_position'),
              'ring_current'                     : (False, 'BMM.facility_ring_current'),
              'bpm_upstream_x'                   : (False, 'BMM.facility_bpm_upstream_x'),
              'bpm_upstream_y'                   : (False, 'BMM.facility_bpm_upstream_y'),
              'bpm_downstream_x'                 : (False, 'BMM.facility_bpm_downstream_x'),
              'bpm_downstream_y'                 : (False, 'BMM.facility_bpm_downstream_y'),
              'monotc_inboard_temperature'       : (False, 'BMM.mono_tc_inboard'),
              'monotc_upstream_high_temperature' : (False, 'BMM.mono_tc_upstream_high'),
              'monotc_downstream_temperature'    : (False, 'BMM.mono_tc_downstream'),
              'monotc_upstream_low_temperature'  : (False, 'BMM.mono_tc_upstream_low'),
              }
run_report('\t'+'XDI')
from BMM.xdi import write_XDI

run_report('\t'+'machine learning and data evaluation')
from BMM.ml import BMMDataEvaluation
clf = BMMDataEvaluation()

## suppress some uninteresting messages from lib/python3.7/site-packages/hdf5plugin/__init__.py
import logging
logging.getLogger("hdf5plugin").setLevel(logging.ERROR)
run_report('\t'+'xafs')
from BMM.xafs import howlong, xafs, db2xdi

run_report('\t'+'mono calibration')
from BMM.mono_calibration import calibrate, calibrate_high_end, calibrate_low_end, calibrate_mono, calibrate_pitch

run_report('\t'+'Larch')
from BMM.larch_interface import Pandrosus, Kekropidai
## examples that only work at BMM...
# se = Pandrosus()
# se.fetch('8e293af3-811c-4e96-a4e5-733d0dc77dad', name\='Se metal', mode='transmission')

# seo = Pandrosus()
# seo.fetch('69c35332-6c8a-4f43-9eb2-e5e9cbe7f798', name='SeO2', mode='transmission')

# bunch = Kekropidai(name='Selenium standards')
# bunch.add(se)
# bunch.add(seo)


run_report('\t'+'Demeter')
from BMM.demeter import athena, hephaestus, toprj

run_report('\t'+'telemetry')
from BMM.telemetry import BMMTelemetry
tele = BMMTelemetry()

if not is_re_worker_active():
    run_report('\t'+'user interaction')
    from BMM.wdywtd import WDYWTD
    _do = WDYWTD()
    do = _do.wdywtd
    setup_xrd = _do.do_SetupXRD


if rois.trigger is True:        # set Struck rois from persistent user information
     if len(BMMuser.rois) == 3:
          rois.set(BMMuser.rois)
          rois.select(BMMuser.element)
     rois.trigger = False

if BMMuser.element is None:
     try:
          BMMuser.element = rkvs.get('BMM:pds:element').decode('utf-8')
     except:
          pass
     try:
          BMMuser.edge    = rkvs.get('BMM:pds:edge').decode('utf-8')
     except:
          pass

run_report('\t'+'final setup: Xspress3')
from BMM.user_ns.dwelltime import with_xspress3
from BMM.user_ns.detectors import xs, xs1, use_4element, use_1element
if BMMuser.element is not None and with_xspress3 is True: # make sure Xspress3 is configured to measure from the correct ROI
    if use_4element:
        BMMuser.verify_roi(xs, BMMuser.element, BMMuser.edge, tab='\t\t\t')
    if use_1element:
        BMMuser.verify_roi(xs1, BMMuser.element, BMMuser.edge)
    show_edges()

run_report('\t'+'final setup: cameras')
from BMM.user_ns.detectors import xascam, xrdcam, anacam
xascam._root = os.path.join(BMMuser.folder, 'snapshots')
xrdcam._root = os.path.join(BMMuser.folder, 'snapshots')
anacam._root = os.path.join(BMMuser.folder, 'snapshots')

     
run_report('\t'+'checking motor connections')
from BMM.edge import all_connected
if all_connected(True) is False:
     print(error_msg('Ophyd connection failure (testing main PDS motors)'))
     print(error_msg('You likely have to restart bsui.'))

run_report('\t'+'data folders and logging')
from BMM.user_ns.base import startup_dir
from BMM.user_ns.instruments import wmb, lmb, gmb, lsmb
wmb.folder = BMMuser.folder      # single or double wheel
gawheel.folder = BMMuser.folder  # glancing angle stage
lmb.folder = BMMuser.folder      # Linkam stage
lsmb.folder = BMMuser.folder     # LakeShore 331 temperature controller
gmb.folder = BMMuser.folder      # generic motor grid
gawheel.description = 'the glancing angle stage'

from BMM.logging import BMM_msg_hook
user_ns['RE'].msg_hook = BMM_msg_hook

def measuring(element, edge=None):
    BMMuser.element = element
    rkvs.set('BMM:pds:element', element)
    if edge is not None:
        BMMuser.edge = edge
        rkvs.set('BMM:pds:edge', edge)
    if use_4element:
        xs.reset_rois()
    if use_1element:
        xs1.reset_rois()
    show_edges()

def check_for_synaxis():
    '''A disconnected motor (due to IOC or controller not running) will be
    defined as a SynAxis. This does a test for that situation and
    reports about it at startup.  It also sets BMMuser.syns to True so
    things like motor_status() behave non-disastrously.
    '''
    BMMuser.syns = False
    syns = []
    for m in mcs8_motors:
        if 'SynAxis' in f'{m}':
            syns.append(m.name)
    if len(syns) > 0:
        BMMuser.syns = True
        text = 'The following are disconnected & defined as simulated motors:\n\n'
        text += '\n'.join(disconnected_msg(x) for x in textwrap.wrap(', '.join(syns))) + '\n\n'
        text += 'This allows bsui to operate normally, but do not expect anything\n'
        text += 'involving those motors to work correctly.\n'
        text += whisper('(This likely means that an IOC or a motor controller (or both) are off.)')
        boxedtext('Disconnected motors', text, 'red', width=74)
check_for_synaxis()
    
try:
    from bluesky_widgets.utils.streaming import stream_documents_into_runs
    from bluesky_widgets.models.plot_builders import Lines
    from bluesky_widgets.qt.figures import QtFigure
    # model = Lines("xafs_y", ["I0"], max_runs=1)
    # view = QtFigure(model.figure)
    # view.show()
except:
    pass


#import logging
#debug_monitor_log = logging.getLogger('ophyd.event_dispatcher')
#debug_monitor_log.addHandler(logging.StreamHandler(stream=sys.stdout))

