
try:
    from bluesky_queueserver import is_re_worker_active
except ImportError:
    # TODO: delete this when 'bluesky_queueserver' is distributed as part of collection environment
    def is_re_worker_active():
        return False

# basic Bluesky/Ophyd/Databroker functionality, deal with QS vs. bsui
from .base import *

# define/initialize BMMuser, define ROI object
from .bmm import *

# stub for bluesky widgets
#from .bw import *

# define motor groups and individual motors, ancillary motor functionality
from .motors import *

# mirrors, slits, XAS sample & reference wheel, detector mount, actuators (shutters, flags)
# busy device, Linkam, Lakeshore, motor grid, kill switches
from .instruments import *

# limited goniometer support
from .gonio import *

# Ring object, baseline definition
from .metadata import *

# tie together integration times of various detectors
from .dwelltime import *

# dcm motor group
from .dcm import *

# Struck (deprecated), electrometers, optical cameras, Pilatus, Xspress3 (4 channel & 1 channel)
from .detectors import *

# valves, temperatures, water flow, etc
from .utilities import *

# everything else, read comments in that file
from .bmm_end import *

if not is_re_worker_active():
    print('\t\t', end='')
    get_ipython().magic(u"%xmode Plain")
    from .prompt import *
    from .magic import *
    #import warnings
    #import databroker.mongo_normalized
    #warnings.filterwarnings("ignore", module='databroker.mongo_normalized')


from BMM.user_ns.bmm import whoami
if BMMuser.trigger is True:     # provide feedback if importing persistent user information 
    print('')
    whoami()
    BMMuser.trigger = False
