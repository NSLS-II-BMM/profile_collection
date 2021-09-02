
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
from .metadata import *
from .dcm import *
from .detectors import *
from .utilities import *
from .bmm_end import *

if not is_re_worker_active():
    print('\t\t', end='')
    get_ipython().magic(u"%xmode Plain")
    from .prompt import *
    from .magic import *
