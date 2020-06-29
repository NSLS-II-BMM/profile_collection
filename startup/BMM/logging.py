import logging
import os
from os import chmod
from IPython.utils.coloransi import TermColors as color
from BMM.functions           import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper

#run_report(__file__, text='BMM-specific logging')

BMM_logger          = logging.getLogger('BMM_logger')
BMM_logger.handlers = []

BMM_formatter       = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s\n%(message)s')

## how to get hostname: os.uname()[1]

BMM_log_master_file = os.path.join(os.environ['HOME'], 'Data', 'BMM_master.log')
if not os.path.isdir(os.path.join(os.environ['HOME'], 'Data')):
    os.makedirs(os.path.join(os.environ['HOME'], 'Data'))
if not os.path.isfile(BMM_log_master_file):
    os.mknod(BMM_log_master_file)
if os.path.isfile(BMM_log_master_file):
    chmod(BMM_log_master_file, 0o644)
    BMM_log_master = logging.FileHandler(BMM_log_master_file)
    BMM_log_master.setFormatter(BMM_formatter)
    BMM_logger.addHandler(BMM_log_master)
    chmod(BMM_log_master_file, 0o444)

BMM_nas_log_file = '/nist/xf06bm/data/BMM_master.log'
if os.path.isdir('/nist'):
    if not os.path.isfile(BMM_nas_log_file):
        basedir = os.path.dirname(BMM_nas_log_file)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        os.mknod(BMM_nas_log_file)
    if os.path.isfile(BMM_nas_log_file):
        chmod(BMM_nas_log_file, 0o644)
        BMM_log_nas = logging.FileHandler(BMM_nas_log_file)
        BMM_log_nas.setFormatter(BMM_formatter)
        BMM_logger.addHandler(BMM_log_nas)

BMM_logger.setLevel(logging.INFO)

BMM_log_user = None

## this is intended to be a log file in the experiment folder
## thus all scans, etc. relevant to the experiment will be logged with the data
## call this at the beginning of the beamtime
def BMM_user_log(filename):
    BMM_log_user = logging.FileHandler(filename)
    BMM_log_user.setFormatter(BMM_formatter)
    BMM_logger.addHandler(BMM_log_user)

## remove all but the master log from the list of handlers
def BMM_unset_user_log():
    BMM_logger.handlers = []
    BMM_logger.addHandler(BMM_log_master)
    BMM_logger.addHandler(BMM_log_nas)

## use this command to properly format the log message, manage file permissions, etc
def BMM_log_info(message):
    chmod(BMM_log_master_file, 0o644)
    chmod(BMM_nas_log_file, 0o644)
    entry = ''
    for line in message.split('\n'):
        entry += '    ' + line + '\n'
    BMM_logger.info(entry)
    chmod(BMM_log_master_file, 0o444)
    chmod(BMM_nas_log_file, 0o444)


def report(text, level=None):
    '''Print a string to the screen AND to the log file.

    Report level decorations on screen:

      * error (red)
      * warning (yellow)
      * info (brown)
      * url (undecorated)
      * bold (bright white)
      * verbosebold (bright cyan)
      * list (cyan)
      * disconnected (purple)
      * whisper (gray)

    not matching a report level will be undecorated
    '''
    BMM_log_info(text)
    if color:                   # test that color is sensible...
        if level == 'error':
            print(error_msg(text))
        elif level == 'warning':
            print(warning_msg(text))
        elif level == 'info':
            print(info_msg(text))
        elif level == 'url':
            print(url_msg(text))
        elif level == 'bold':
            print(bold_msg(text))
        elif level == 'verbosebold':
            print(verbosebold_msg(text))
        elif level == 'disconnected':
            print(disconnected_msg(text))
        elif level == 'list':
            print(list_msg(text))
        elif level == 'whisper':
            print(whisper(text))
        else:
            print(text)
    else:
        print(text)



######################################################################################
# here is an example of what a message tuple looks like when moving a motor          #
# (each item in the tuple is on it's own line):                                      #
#     set:                                                                           #
#     (XAFSEpicsMotor(prefix='XF:06BMA-BI{XAFS-Ax:LinX}Mtr', name='xafs_linx', ... ) #
#     (-91.5999475,),                                                                #
#     {'group': '8c8df020-23aa-451e-b411-c427bc80b375'}                              #
######################################################################################
def BMM_msg_hook(msg):
    '''
    BMM-specific function for RE.msg_hook
    '''
    #print(msg)
    if msg[0] == 'set':
        if 'EpicsMotor' in str(type(msg[1])):
            report('Moving %s to %.3f'  % (msg[1].name, msg[2][0]))
        elif 'EpicsSignal' in str(type(msg[1])):
            report('Setting %s to %.3f' % (msg[1].name, msg[2][0]), 'whisper')
        elif 'LockedDwell' in str(type(msg[1])):
            report('Setting %s to %.3f' % (msg[1].name, msg[2][0]), 'whisper')
        elif 'PseudoSingle' in str(type(msg[1])):
            report('Moving %s to %.3f'  % (msg[1].name, msg[2][0]))


