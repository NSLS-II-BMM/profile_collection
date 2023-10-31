
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

kafka_config = _read_bluesky_kafka_config_file(config_file_path="/etc/bluesky/kafka.yml")

producer = BasicProducer(bootstrap_servers=kafka_config['bootstrap_servers'],
                         topic='bmm.test',
                         producer_config=kafka_config["runengine_producer_config"],
                         key='abcdef'
)


def kafka_message(message):
    producer.produce(['bmm', message])


# Maintenance of kafka output
def close_line_plots():
    kafka_message({'close': 'line'})

def close_plots():
    kafka_message({'close': 'all'})

def kafka_verbose(onoff=False):
    kafka_message({'verbose': onoff})
    
