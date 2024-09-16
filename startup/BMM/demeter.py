import subprocess
import os

from BMM.functions import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

from BMM.user_ns.bmm import BMMuser


# def run_athena():
#     os.environ['DEMETER_FORCE_IFEFFIT'] = '1' 
#     subprocess.Popen(["dathena"], stderr=subprocess.DEVNULL)
    
def run_hephaestus():
    os.environ['DEMETER_FORCE_IFEFFIT'] = '1' 
    subprocess.Popen(["dhephaestus"], stderr=subprocess.DEVNULL)


