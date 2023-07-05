
import os

from BMM.functions import run_report
from BMM.user_ns.bmm import BMMuser

run_report(__file__, text='dwelltime')
UNREAL=True
##############################################################
# ______ _    _ _____ _      _    _____ ________  ___ _____  #
# |  _  \ |  | |  ___| |    | |  |_   _|_   _|  \/  ||  ___| #
# | | | | |  | | |__ | |    | |    | |   | | | .  . || |__   #
# | | | | |/\| |  __|| |    | |    | |   | | | |\/| ||  __|  #
# | |/ /\  /\  / |___| |____| |____| |  _| |_| |  | || |___  #
# |___/  \/  \/\____/\_____/\_____/\_/  \___/\_|  |_/\____/  #
##############################################################


with_quadem, with_struck, with_xspress3 = True, False, True
with_ic0, with_ic1, with_ic2 = True, False, False
with_dualem = False             # deprecated

# An error gets triggered during Azure CI testing that does not get triggered when
# running under IPython. This disables the Xspress3 during testing.
# This is a crude stopgap.
# See https://dev.azure.com/nsls2/profile_collections/_build/results?buildId=2609&view=results
if os.environ.get('AZURE_TESTING') or UNREAL:
    with_xspress3 = False

if with_xspress3 is True:
    BMMuser.readout_mode = 'xspress3'
from BMM.dwelltime import LockedDwellTimes

_locked_dwell_time = LockedDwellTimes('', name='dwti')
dwell_time = _locked_dwell_time.dwell_time
dwell_time.name = 'inttime'
