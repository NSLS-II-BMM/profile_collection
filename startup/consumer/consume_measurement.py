import datetime, signal, pprint, uuid, sys, os
sys.path.append('/home/xf06bm/.ipython/profile_collection/startup')

from bluesky_kafka import RemoteDispatcher
import nslsii
import nslsii.kafka_utils

from tiled.client import from_profile
bmm_catalog = from_profile('bmm')

import matplotlib.pyplot as plt
import bmm_plot

# these two lines allow a stale plot to remain interactive and prevent
# the current plot from stealing focus.  thanks to Tom:
# https://nsls2.slack.com/archives/C02D9V72QH1/p1674589090772499
plt.ion()
plt.rcParams["figure.raise_window"] = False

def handler(signal, frame):
    print('Exiting Kafka consumer')
    sys.exit(0)
signal.signal(signal.SIGINT, handler)

def plot_from_kafka_messages(beamline_acronym):

    def examine_message(name, doc):
        print(
            f"{datetime.datetime.now().isoformat()} document: {name}\n"
            f"contents: {pprint.pformat(doc)}\n"
        )
        if name == 'datum':
            print('saw one')
        if name == 'stop':
            # print(
            #     f"{datetime.datetime.now().isoformat()} document: {name}\n"
            #     f"contents: {pprint.pformat(doc)}\n"
            # )
            uid = doc['run_start']
            record = bmm_catalog[uid]
            if 'BMM_kafka' in record.metadata['start']:
                hint = record.metadata['start']['BMM_kafka']['hint']
                print(f'[{datetime.datetime.now().isoformat(timespec="seconds")}]   {uid}')
                for k in record.metadata['start']['BMM_kafka'].keys():
                    print(f"\t\t{k}: {record.metadata['start']['BMM_kafka'][k]}")

                if hint.startswith('linescan'):
                    bmm_plot.plot_linescan(bmm_catalog, uid)
                elif hint.startswith('timescan'):
                    bmm_plot.plot_timescan(bmm_catalog, uid)
                elif hint.startswith('rectanglescan'):
                    bmm_plot.plot_rectanglescan(bmm_catalog, uid)
                elif hint.startswith('areascan'):
                    bmm_plot.plot_areascan(bmm_catalog, uid)
                elif hint.startswith('xafs'):
                    plt.close('all')
                    bmm_plot.plot_xafs(bmm_catalog, uid)

    kafka_config = nslsii.kafka_utils._read_bluesky_kafka_config_file(config_file_path="/etc/bluesky/kafka.yml")

    # this consumer should not be in a group with other consumers
    #   so generate a unique consumer group id for it
    unique_group_id = f"echo-{beamline_acronym}-{str(uuid.uuid4())[:8]}"

    kafka_dispatcher = RemoteDispatcher(
        topics=[f"{beamline_acronym}.bluesky.runengine.documents", "bmm.test"],
        bootstrap_servers=",".join(kafka_config["bootstrap_servers"]),
        group_id=unique_group_id,
        consumer_config=kafka_config["runengine_producer_config"],
    )

    kafka_dispatcher.subscribe(examine_message)
    try:
        kafka_dispatcher.start(work_during_wait=lambda : plt.pause(.1))
    except KeyboardInterrupt:
        print('\nExiting Kafka consumer')
        return()
