from base import *
from bmm import *
from bw import *
from motors import *
from instruments import *
from metadata import *
from dcm import *
from detectors import *
from utilities import *
from bmm import *

from IPython import get_ipython

# Only run this if we are inside a running IPython application.
if get_ipython() is not None:
    from magic import *
