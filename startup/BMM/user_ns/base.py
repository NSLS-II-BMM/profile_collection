import nslsii
import os

try:
    from bluesky_queueserver import is_re_worker_active
except ImportError:
    # TODO: delete this when 'bluesky_queueserver' is distributed as part of collection environment
    def is_re_worker_active():
        return False

os.environ['BLUESKY_KAFKA_BOOTSTRAP_SERVERS'] = 'kafka1.nsls2.bnl.gov:9092'

uns_dict = dict()

if not is_re_worker_active():
    ip = get_ipython()
    nslsii.configure_base(ip.user_ns, 'bmm', configure_logging=True, publish_documents_to_kafka=True)
    ip.log.setLevel('ERROR')
else:
    nslsii.configure_base(uns_dict, 'bmm', configure_logging=True, publish_documents_to_kafka=True)
    RE  = uns_dict['RE']
    db  = uns_dict['db']
    sd  = uns_dict['sd']
    bec = uns_dict['bec']

bec.disable_plots()
bec.disable_baseline()

import ophyd
ophyd.EpicsSignal.set_defaults(timeout=10, connection_timeout=10)

#from databroker.core import SingleRunCache

from bluesky.utils import ts_msg_hook
RE.msg_hook = ts_msg_hook


from bluesky.callbacks.zmq import Publisher
publisher = Publisher('localhost:5577')
RE.subscribe(publisher)
