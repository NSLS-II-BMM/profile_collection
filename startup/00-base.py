import nslsii
ip = get_ipython()

nslsii.configure_base(ip.user_ns, 'bmm', configure_logging=True, publish_documents_to_kafka=True)

bec.disable_plots()
bec.disable_baseline()

import ophyd
ophyd.EpicsSignal.set_defaults(timeout=20, connection_timeout=20)

#from databroker.core import SingleRunCache

from bluesky.utils import ts_msg_hook
RE.msg_hook = ts_msg_hook


from bluesky.callbacks.zmq import Publisher
publisher = Publisher('localhost:5577')
RE.subscribe(publisher)
