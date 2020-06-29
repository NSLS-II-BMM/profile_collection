import nslsii
ip = get_ipython()

nslsii.configure_base(ip.user_ns, 'bmm', configure_logging=False)

bec.disable_plots()
bec.disable_baseline()

import ophyd
ophyd.EpicsSignal.set_default_timeout(timeout=60, connection_timeout=10)

from databroker.core import SingleRunCache

from BMM.functions           import now, colored, run_report, boxedtext
from BMM.functions           import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.logging             import report, BMM_log_info, BMM_msg_hook


from BMM.user import BMM_User
from BMM.referencefoils import ReferenceFoils
foils = ReferenceFoils()
from BMM.rois import ROI
rois = ROI()


BMMuser = BMM_User()
BMMuser.start_experiment_from_serialization()

if BMMuser.pds_mode is None:
    try:                        # do the right then when "%run -i"-ed
        BMMuser.pds_mode = get_mode()
    except:                     # else wait until later to set this correctly, get_mode() defined in 74-mode.py
        pass
## some backwards compatibility....
whoami           = BMMuser.show_experiment()
start_experiment = BMMuser.start_experiment
end_experiment   = BMMuser.end_experiment

from BMM.mirror_trigonometry import move_m2, move_m3











RE.msg_hook = BMM_msg_hook

