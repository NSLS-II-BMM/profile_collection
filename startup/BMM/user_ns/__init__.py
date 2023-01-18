
try:
    from bluesky_queueserver import is_re_worker_active
except ImportError:
    # TODO: delete this when 'bluesky_queueserver' is distributed as part of collection environment
    def is_re_worker_active():
        return False

from .base import *
from .bmm import *
from .bw import *
from .motors import *
from .instruments import *
from .gonio import *
from .metadata import *
from .dwelltime import *
from .dcm import *
from .detectors import *
from .utilities import *
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
