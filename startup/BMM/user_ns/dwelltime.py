
import os

from BMM.functions import run_report
from BMM.user_ns.bmm import BMMuser

run_report(__file__, text='dwelltime + selecting detectors for use')

##############################################################
# ______ _    _ _____ _      _    _____ ________  ___ _____  #
# |  _  \ |  | |  ___| |    | |  |_   _|_   _|  \/  ||  ___| #
# | | | | |  | | |__ | |    | |    | |   | | | .  . || |__   #
# | | | | |/\| |  __|| |    | |    | |   | | | |\/| ||  __|  #
# | |/ /\  /\  / |___| |____| |____| |  _| |_| |  | || |___  #
# |___/  \/  \/\____/\_____/\_____/\_/  \___/\_|  |_/\____/  #
##############################################################

# These turn on/off the OG detector systems at BMM
with_quadem, with_struck = True, False

# use these two line to entirely turn on/off use of the Xspress3 or to turn on/off either individual detector
with_xspress3, use_4element, use_1element = True, True, True
#with_xspress3, use_4element, use_1element = False, False, False

# use these to turn on/off the monolithic ion chambers
with_ic0, with_ic1, with_ic2 = True, True, False
with_dualem = False             # deprecated, prototype

# An error gets triggered during Azure CI testing that does not get triggered when
# running under IPython. This disables the Xspress3 during testing.
# This is a crude stopgap.
if os.environ.get('AZURE_TESTING'):
    with_xspress3, use_4element, use_1element = False, False, False

if with_xspress3 is True:
    BMMuser.readout_mode = 'xspress3'
elif with_struck is True:
    BMMuser.readout_mode = 'analog'
else:
    BMMuser.readout_mode = None
    
from BMM.dwelltime import LockedDwellTimes

_locked_dwell_time = LockedDwellTimes('', name='dwti')
dwell_time = _locked_dwell_time.dwell_time
dwell_time.name = 'inttime'
