import nslsii
ip = get_ipython()

nslsii.configure_base(ip.user_ns, 'bmm', configure_logging=False)

bec.disable_plots()
bec.disable_baseline()

import ophyd
ophyd.EpicsSignal.set_default_timeout(timeout=60, connection_timeout=10)

from databroker.core import SingleRunCache
src = SingleRunCache()
