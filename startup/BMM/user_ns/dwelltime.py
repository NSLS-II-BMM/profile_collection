
import os

from BMM.functions import run_report
from BMM.user_ns.bmm import BMMuser

run_report(__file__, text='dwelltime + selecting detectors for use')


################################################################################
# Configure detector selection here,
# False to exclude a detector from consideration in bsui

# Ion chambers
with_quadem   = True            # available for Iy and other signals
with_ic0      = True            # new I0 chamber
with_ic1      = True            # new It chamber
with_ic2      = True            # new Ir chamber
with_dualem   = False           # deprecated, prototype
with_iy       = False           # begin planning for yield detector

# fluorescence detectors and readout systems
with_struck   = False           # deprecated OG fluorescence read out
with_xspress3 = True
use_4element  = True
use_1element  = True

################################################################################


##############################################################
# ______ _    _ _____ _      _    _____ ________  ___ _____  #
# |  _  \ |  | |  ___| |    | |  |_   _|_   _|  \/  ||  ___| #
# | | | | |  | | |__ | |    | |    | |   | | | .  . || |__   #
# | | | | |/\| |  __|| |    | |    | |   | | | |\/| ||  __|  #
# | |/ /\  /\  / |___| |____| |____| |  _| |_| |  | || |___  #
# |___/  \/  \/\____/\_____/\_____/\_/  \___/\_|  |_/\____/  #
##############################################################


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
