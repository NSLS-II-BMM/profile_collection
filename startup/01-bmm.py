
DATA = os.path.join(os.getenv('HOME'), 'Data', 'bucket') + '/'

from BMM.functions           import now, colored, run_report, boxedtext
from BMM.functions           import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
run_report('\t'+'logging')
from BMM.logging             import report, BMM_log_info, BMM_msg_hook


run_report('\t'+'user')
from BMM.user import BMM_User
run_report('\t'+'detector ROIs')
from BMM.referencefoils import ReferenceFoils
foils = ReferenceFoils()
run_report('\t'+'reference foils')
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










RE.msg_hook = BMM_msg_hook
