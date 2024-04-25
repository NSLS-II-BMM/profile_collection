import datetime, signal, pprint, uuid, sys, os, time
sys.path.append('/home/xf06bm/.ipython/profile_collection/startup')

from bluesky_kafka.consume import BasicConsumer
import nslsii
import nslsii.kafka_utils

from tiled.client import from_profile
bmm_catalog = from_profile('bmm')


import redis
if not os.environ.get('AZURE_TESTING'):
    redis_host = 'xf06bm-ioc2'
else:
    redis_host = '127.0.0.1'
class NoRedis():
    def set(self, thing, otherthing):
        return None
    def get(self, thing):
        return None
try:
    rkvs = redis.Redis(host=redis_host, port=6379, db=0)
except:
    rkvs = NoRedis()


from echo_slack import echo_slack
from slack import img_to_slack

# legible screen output
from pygments import highlight
from pygments.lexers import PythonLexer, HtmlLexer
from pygments.formatters import Terminal256Formatter

from dossier_kafka import BMMDossier, startup_dir

# capture Ctrl-c to exit kafka polling loop semi-gracefully
def handler(signal, frame):
    print('Exiting Kafka consumer')
    sys.exit(0)
signal.signal(signal.SIGINT, handler)

import logging

logger = logging.getLogger('BMM file manager logger')
logger.handlers = []

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
    

def clear_logger(logger):
    logger.handlers = []

def establish_logger(logger):
    folder = rkvs.get('BMM:user:folder').decode('UTF8')
    log_master_file = os.path.join(folder, 'file_manager.log')
    if not os.path.isfile(log_master_file):
        os.mknod(log_master_file)
    fh = logging.FileHandler(log_master_file)
    fh.setLevel(logging.INFO) 
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s\n%(message)s\n')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    #logging.basicConfig(filename=log_master_file, encoding='utf-8', level=logging.INFO,
    #                    format='%(asctime)s - %(name)s - %(levelname)s\n%(message)s\n')
    print(f'established a logging handler for experiment in {folder}')


    
def manage_files_from_kafka_messages(beamline_acronym):

    def examine_message(consumer, doctype, doc):
        global be_verbose, dossier, logger
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
                print(f'\n[{datetime.datetime.now().isoformat(timespec="seconds")}]') # \ndossier : {message["dossier"]}')

            if 'dossier' in message:
                if message['dossier'] == 'start':
                    dossier = BMMDossier()
                    print(startup_dir)

                elif message['dossier'] == 'logger':
                    establish_logger(logger)

                elif message['dossier'] == 'clear_logger':
                    clear_logger(logger)

                elif message['dossier'] == 'set':
                    dossier.set_parameters(**message)
                    print(f'set {len(message)-1} parameters')

                elif message['dossier'] == 'show':
                    pobj(dossier)
                    
                elif message['dossier'] == 'motors':
                    try:
                        print(highlight(dossier.motor_sidebar(bmm_catalog),
                                        HtmlLexer(),
                                        Terminal256Formatter(style='monokai')))
                    except Exception as E:
                        logger.error(str(E))

                elif message['dossier'] == 'write':
                    dossier.write_dossier(bmm_catalog, logger)

            elif 'echoslack' in message:
                if 'img' not in message or  message['img'] is None:
                    print(f'seding message "{message["text"]}" to slack')
                    if 'icon' not in message: message['icon'] = 'message'
                    if 'rid'  not in message: message['rid']  = None
                    echo_slack(text = message['text'],
                               icon = message['icon'],
                               rid  = message['rid'] )

                elif 'img' in message and os.path.exists(message['img']):
                    img_to_slack(message['img'])
                    
                    
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
        
