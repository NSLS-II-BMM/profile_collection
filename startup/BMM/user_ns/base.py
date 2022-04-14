import nslsii
import os

from bluesky.plan_stubs import mv, mvr, sleep

try:
    from bluesky_queueserver import is_re_worker_active
except ImportError:
    # TODO: delete this when 'bluesky_queueserver' is distributed as part of collection environment
    def is_re_worker_active():
        return False

use_kafka = True
os.environ['BLUESKY_KAFKA_BOOTSTRAP_SERVERS'] = 'kafka1.nsls2.bnl.gov:9092'

## the intent here is to return $HOME/.profile_collection/startup
#startup_dir = os.path.split(os.path.split(os.path.split(__file__)[0])[0])[0]
startup_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

uns_dict = dict()

if not is_re_worker_active():
    ip = get_ipython()
    nslsii.configure_base(ip.user_ns, 'bmm', configure_logging=True, publish_documents_with_kafka=use_kafka)
    ip.log.setLevel('ERROR')
    RE  = ip.user_ns['RE']
    db  = ip.user_ns['db']
    sd  = ip.user_ns['sd']
    bec = ip.user_ns['bec']
else:
    nslsii.configure_base(uns_dict, 'bmm', configure_logging=True, publish_documents_with_kafka=use_kafka)
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
