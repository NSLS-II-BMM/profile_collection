import nslsii
ip = get_ipython()

nslsii.configure_base(ip.user_ns, 'temp', configure_logging=False) ###

bec.disable_plots()
bec.disable_baseline()

import ophyd
ophyd.EpicsSignal.set_default_timeout(timeout=10, connection_timeout=10)

#from databroker.core import SingleRunCache

from bluesky.utils import ts_msg_hook
RE.msg_hook = ts_msg_hook
