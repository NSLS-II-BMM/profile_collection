
import nslsii.kafka_utils
from bluesky_kafka.produce import BasicProducer

kafka_config = nslsii.kafka_utils._read_bluesky_kafka_config_file(config_file_path="/etc/bluesky/kafka.yml")

producer = BasicProducer(bootstrap_servers=kafka_config['bootstrap_servers'],
                         topic='bmm.test',
                         producer_config=kafka_config["runengine_producer_config"],
                         key='abcdef'
)


def kafka_message(message):
    producer.produce(['bmm', message])
