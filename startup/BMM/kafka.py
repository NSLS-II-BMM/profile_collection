
import os

try:
    from bluesky_queueserver import is_re_worker_active
except ImportError:
    # TODO: delete this when 'bluesky_queueserver' is distributed as part of collection environment
    def is_re_worker_active():
        return False

#if is_re_worker_active():
#    from nslsii import _read_bluesky_kafka_config_file
#else:
from nslsii.kafka_utils import _read_bluesky_kafka_config_file
    
from bluesky_kafka.produce import BasicProducer

from BMM.functions import proposal_base, warning_msg

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

kafka_config = _read_bluesky_kafka_config_file(config_file_path="/etc/bluesky/kafka.yml")

producer = BasicProducer(bootstrap_servers=kafka_config['bootstrap_servers'],
                         topic='bmm.test',
                         producer_config=kafka_config["runengine_producer_config"],
                         key='abcdef'
)


def kafka_message(message):
    '''Broadcast a message to kafka on the private BMM channel.

    For all BMM workers, the message is a dict.  See worker
    documentation for details.

    '''
    producer.produce(['bmm', message])


# Maintenance of kafka output
def close_line_plots():
    kafka_message({'close': 'line'})

def close_plots():
    kafka_message({'close': 'all'})

def kafka_verbose(onoff=False):
    kafka_message({'verbose': onoff})

# this is awkward.  it only works on fully qualified paths to
# something in Workspace or on a filename relative to user's Workspace
# This needs a file selection dialog!
def preserve(fname, target=None):
    '''Safely copy a file from your workspace to your proposal folder.
    '''
    if target is None:
        target = proposal_base()
    fullname = os.path.join(user_ns['BMMuser'].workspace, fname)
    if os.path.isfile(fullname):
        print(f'Copying {fname} to {target}')
        kafka_message({'copy': True,
                       'file': fullname,
                       'target': target})
    else:
        print(warning_msg(f"There is not a file called {fname} in {user_ns['BMMuser'].workspace}."))
