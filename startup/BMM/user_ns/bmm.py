
import logging
logger = logging.getLogger('ophyd')
logger.setLevel('WARNING')
logger = logging.getLogger('bluesky')
logger.setLevel('WARNING')
from BMM.user_ns.base import startup_dir
from BMM.workspace import initialize_workspace, rkvs_keys
UNREAL=True
if not UNREAL:
    initialize_workspace()

import json, time, os

## suppress the thing where matplotlib raises a new plot window to the top, stealing focus
import matplotlib as mpl
mpl.rcParams['figure.raise_window'] = False

DATA = os.path.join(os.getenv('HOME'), 'Data', 'bucket') + '/'
BMM_CONFIGURATION_LOCATION = os.path.join(startup_dir, 'lookup_table')

nas_mount_point = '/mnt/nfs/nas1'
nas_path = os.path.join(nas_mount_point, 'xf06bm', 'experiments', 'XAS', 'snapshots')

from BMM.functions           import now, colored, run_report, boxedtext, elapsed_time
from BMM.functions           import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
run_report(__file__, text='functions and other basics')
run_report('\t'+'logging')
from BMM.logging             import report, BMM_log_info, BMM_msg_hook

from bluesky.preprocessors   import finalize_wrapper

run_report('\t'+'user')
from BMM.user import BMM_User


run_report('\t'+'detector ROIs')
from BMM.rois import ROI
rois = ROI()


BMMuser = BMM_User()
BMMuser.start_experiment_from_serialization()


if BMMuser.pds_mode is None:
    try:                        # do the right then when "%run -i"-ed
        BMMuser.pds_mode = get_mode()
    except:                     # else wait until later to set this correctly, get_mode()
        pass
## some backwards compatibility....
whoami           = BMMuser.show_experiment
start_experiment = BMMuser.start_experiment
end_experiment   = BMMuser.end_experiment

import atexit, os

def teardown():
    fname = os.path.join(BMMuser.DATA, '.BMMuser')
    print("Shutting down: ", end=' ')
    BMMuser.state_to_redis(filename=os.path.join(BMMuser.DATA, '.BMMuser'), prefix='')

atexit.register(teardown)




# RE.msg_hook = BMM_msg_hook
