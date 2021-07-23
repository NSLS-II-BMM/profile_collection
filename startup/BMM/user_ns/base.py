import nslsii
import os
import __main__
ip = get_ipython()

os.environ['BLUESKY_KAFKA_BOOTSTRAP_SERVERS'] = 'kafka1.nsls2.bnl.gov:9092'
nslsii.configure_base(ip.user_ns, 'bmm', configure_logging=True, publish_documents_to_kafka=True)
ip.log.setLevel('ERROR')

bec = __main__.bec
bec.disable_plots()
bec.disable_baseline()

import ophyd
ophyd.EpicsSignal.set_defaults(timeout=10, connection_timeout=10)

#from databroker.core import SingleRunCache

from bluesky.utils import ts_msg_hook
RE = __main__.RE
RE.msg_hook = ts_msg_hook


from bluesky.callbacks.zmq import Publisher
publisher = Publisher('localhost:5577')
RE.subscribe(publisher)
