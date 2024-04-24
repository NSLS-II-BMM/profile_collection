import datetime, signal, pprint, uuid, sys, os, time
sys.path.append('/home/xf06bm/.ipython/profile_collection/startup')

from bluesky_kafka.consume import BasicConsumer
import nslsii
import nslsii.kafka_utils

from tiled.client import from_profile
bmm_catalog = from_profile('bmm')


# legible screen output
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import Terminal256Formatter

from dossier_kafka import BMMDossier, startup_dir

# capture Ctrl-c to exit kafka polling loop semi-gracefully
def handler(signal, frame):
    print('Exiting Kafka consumer')
    sys.exit(0)
signal.signal(signal.SIGINT, handler)


be_verbose = False
dossier = BMMDossier()


def pobj(text, style='monokai'):
    '''Pretty print a dictionary representation of an object to the
    screen with syntax highlighting provided by Pygments.

    Default style is easy to read on a dark terminal.
    See https://pygments.org/styles/
    '''
    print(highlight(pprint.pformat(dossier.__dict__),
                    PythonLexer(),
                    Terminal256Formatter(style=style)))
    

def manage_files_from_kafka_messages(beamline_acronym):

    def examine_message(consumer, doctype, doc):
        #global xafsviz_window
        global be_verbose, dossier
        # print(
        #     f"\n[{datetime.datetime.now().isoformat(timespec='seconds')}] document topic: {doctype}\n"
        #     f"contents: {pprint.pformat(doc)}\n"
        # )
        name, message = doc

        if be_verbose is True:
            print('\n\nVerbose mode is on:')
            pprint.pprint(message)
            print('\n')

        if name == 'bmm':
            if be_verbose is True:
                print(f'\n[{datetime.datetime.now().isoformat(timespec="seconds")}]\n{pprint.pformat(message, compact=True)}')
            else:
                print(f'\n[{datetime.datetime.now().isoformat(timespec="seconds")}]\ndossier : {message["dossier"]}')

            if 'dossier' in message:
                if message['dossier'] == 'start':
                    dossier = BMMDossier()
                    print(startup_dir)

                if message['dossier'] == 'logger':
                    dossier.establish_logger()

                if message['dossier'] == 'clear_logger':
                    dossier.clear_logger()

                if message['dossier'] == 'set':
                    dossier.set_parameters(**message)
                    print(f'set {len(message)-1} parameters')

                if message['dossier'] == 'show':
                    pobj(dossier)

                if message['dossier'] == 'write':
                    dossier.write_dossier(bmm_catalog)

                    
    kafka_config = nslsii.kafka_utils._read_bluesky_kafka_config_file(config_file_path="/etc/bluesky/kafka.yml")

    # this consumer should not be in a group with other consumers
    #   so generate a unique consumer group id for it
    unique_group_id = f"echo-{beamline_acronym}-{str(uuid.uuid4())[:8]}"
    kafka_consumer = BasicConsumer(
        #topics            = [f"{beamline_acronym}.bluesky.runengine.documents", f"{beamline_acronym}.test"],
        topics            = [f"{beamline_acronym}.test"],
        bootstrap_servers = kafka_config["bootstrap_servers"],
        group_id          = unique_group_id,
        consumer_config   = kafka_config["runengine_producer_config"],
        process_message   = examine_message,
    )

    try:
        kafka_consumer.start_polling(work_during_wait=lambda : time.sleep(0.1))
    except KeyboardInterrupt:
        print('\n\nExiting Kafka consumer (file manager)')
        return()

print('Ready to receive documents...')
manage_files_from_kafka_messages('bmm')
        
