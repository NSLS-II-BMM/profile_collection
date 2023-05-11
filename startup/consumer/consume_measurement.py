import datetime, signal, pprint, uuid, sys, os
sys.path.append('/home/xf06bm/.ipython/profile_collection/startup')

#from bluesky_kafka import RemoteDispatcher
from bluesky_kafka.consume import BasicConsumer
import nslsii
import nslsii.kafka_utils

from tiled.client import from_profile
bmm_catalog = from_profile('bmm')

import matplotlib.pyplot as plt
import bmm_plot

from plotWindow import plotWindow
import xafs_visualization
xafsviz_window=None

from xafs_sequence import XAFSSequence
xafsseq = XAFSSequence()
xafsseq.catalog = bmm_catalog

from glancing_angle_stage import GlancingAngle
ga = GlancingAngle()

from align_wheel import AlignWheel
aw = AlignWheel()


doing = None

from bmm_live import LineScan, XAFSScan
ls = LineScan()
xs = XAFSScan()
ts = LineScan()

# these two lines allow a stale plot to remain interactive and prevent
# the current plot from stealing focus.  thanks to Tom:
# https://nsls2.slack.com/archives/C02D9V72QH1/p1674589090772499
plt.ion()
plt.rcParams["figure.raise_window"] = False

# capture Ctrl-c to exit kafka polling loop semi-gracefully
def handler(signal, frame):
    print('Exiting Kafka consumer')
    sys.exit(0)
signal.signal(signal.SIGINT, handler)


def plot_from_kafka_messages(beamline_acronym):

    def examine_message(consumer, doctype, doc):
        global xafsviz_window
        global doing
        # print(
        #     f"\n[{datetime.datetime.now().isoformat(timespec='seconds')}] document topic: {doctype}\n"
        #     f"contents: {pprint.pformat(doc)}\n"
        # )
        name, message = doc

        if name == 'bmm':
            print(f'\n[{datetime.datetime.now().isoformat(timespec="seconds")}]\n{pprint.pformat(message, compact=True)}')

            if 'xafs_sequence' in message:
                if message['xafs_sequence'] == 'start':
                    xafsseq.start(element=message['element'], edge=message['edge'], folder=message['folder'],
                                  repetitions=message['repetitions'], mode=message['mode'])
                elif message['xafs_sequence'] == 'stop':
                    xafsseq.stop(filename=message['filename'])
                elif message['xafs_sequence'] == 'add':
                    xafsseq.add(message['uid'])

            elif 'xafs_visualization' in message:
                xafs_visualization.gridded_plot(uid=message['xafs_visualization'], element=message['element'],
                                                edge=message['edge'], folder=message['folder'],
                                                mode=message['mode'], catalog=bmm_catalog)
                    
            elif 'glancing_angle' in message:
                if message['glancing_angle'] == 'linear':
                    ga.plot_linear(**message)
                elif message['glancing_angle'] == 'pitch':
                    ga.plot_pitch(**message)
                elif message['glancing_angle'] == 'fluo':
                    ga.plot_fluo(**message)
                elif message['glancing_angle'] == 'start':
                    ga.start(**message)
                elif message['glancing_angle'] == 'stop':
                    ga.stop()

            elif 'align_wheel' in message:
                if message['align_wheel'] == 'start':
                    aw.start(**message)
                elif message['align_wheel'] == 'stop':
                    aw.stop()
                else:
                    aw.plot_rectangle(**message)

            elif 'wafer' in message:
                bmm_plot.wafer_plot(**message)

            elif 'mono_calibration' in message:
                bmm_plot.mono_calibration_plot(**message)

            elif 'linescan' in message:
                if message['linescan'] == 'start':
                    ls.start(**message)
                    doing = 'linescan'
                elif message['linescan'] == 'stop':
                    ls.stop(**message)
                    doing = None

            elif 'xafsscan' in message:
                if message['xafsscan'] == 'start':
                    xs.start(**message)
                    doing = 'xafsscan'
                elif message['xafsscan'] == 'next':
                    xs.Next(**message)
                elif message['xafsscan'] == 'stop':
                    xs.stop(**message)
                    doing = None

            elif 'timescan' in message:
                if message['timescan'] == 'start':
                    ts.motor = None
                    ts.start(**message)
                    doing = 'timescan'
                elif message['timescan'] == 'stop':
                    ts.stop(**message)
                    doing = None

            ## todo...
            elif 'areascan' in message:
                pass

            elif 'close' in message:
                if message['close'] == 'all':
                    plt.close('all')
                elif message['close'] == 'line':
                    ls.close_all_lineplots()
                elif message['close'] == 'last':
                    plt.close(ls.plots[-1])

        # for live plotting, need to capture and parse event
        # documents. use the global state variable "doing"
        # to keep track of which plotting chore needs to be done.
        elif name == 'event':
            if doing is None:
                pass
            elif doing == 'linescan':
                ls.add(**message)
            elif doing == 'xafsscan':
                #pprint.pprint(message)
                xs.add(**message)
            elif doing == 'timescan':
                #pprint.pprint(message)
                ts.add(**message)
            elif doing == 'areascan':
                pass
                
        # if name == 'stop':
        #     #print(
        #     #    f"{datetime.datetime.now().isoformat()} document: {name}\n"
        #     #    f"contents: {pprint.pformat(doc)}\n"
        #     #)
        #     #return
        #     uid = message['run_start']  # stop document is the second item in the doc list
        #     record = bmm_catalog[uid]
        #     verbose = False
        #     if 'BMM_kafka' in record.metadata['start']:
        #         hint = record.metadata['start']['BMM_kafka']['hint']
        #         #print(f'[{datetime.datetime.now().isoformat(timespec="seconds")}]   {uid}')
        #         for k in record.metadata['start']['BMM_kafka'].keys():
        #             if k == 'hint':
        #                 continue
        #             print(f"\t\t{k}: {record.metadata['start']['BMM_kafka'][k]}")

        #         if hint.startswith('linescan'):
        #             if verbose: print('saw a linescan stop doc')
        #             #bmm_plot.plot_linescan(bmm_catalog, uid)
        #         elif hint.startswith('timescan'):
        #             if verbose: print('saw a timescan stop doc')
        #             #bmm_plot.plot_timescan(bmm_catalog, uid)
        #         elif hint.startswith('rectanglescan'):
        #             if verbose: print('saw a rectanglescan stop doc')
        #             #bmm_plot.plot_rectanglescan(bmm_catalog, uid)
        #         elif hint.startswith('areascan'):
        #             if verbose: print('saw a areascan stop doc')
        #             print(f"{datetime.datetime.now().isoformat()} document: {name}\n")
        #             bmm_plot.plot_areascan(bmm_catalog, uid)
        #         elif hint.startswith('xafs'):
        #             if verbose: print('saw an xafs stop doc')
        #             #plt.close('all')
        #             #bmm_plot.plot_xafs(bmm_catalog, uid)
    ## end of examine_message ##################################################################
    
    kafka_config = nslsii.kafka_utils._read_bluesky_kafka_config_file(config_file_path="/etc/bluesky/kafka.yml")

    # this consumer should not be in a group with other consumers
    #   so generate a unique consumer group id for it
    unique_group_id = f"echo-{beamline_acronym}-{str(uuid.uuid4())[:8]}"

    kafka_consumer = BasicConsumer(
        topics            = [f"{beamline_acronym}.bluesky.runengine.documents", f"{beamline_acronym}.test"],
        bootstrap_servers = kafka_config["bootstrap_servers"],
        group_id          = unique_group_id,
        consumer_config   = kafka_config["runengine_producer_config"],
        process_message   = examine_message,
    )

    try:
        kafka_consumer.start_polling(work_during_wait=lambda : plt.pause(.1))
    except KeyboardInterrupt:
        print('\nExiting Kafka consumer')
        return()
