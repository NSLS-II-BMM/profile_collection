import logging, datetime, emojis
import os
from urllib import request, parse
import json
from os import chmod
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from IPython.utils.coloransi import TermColors as color

from BMM.functions           import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper
from BMM.echo_slack import echo_slack

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

from BMM.user_ns.base import startup_dir


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

LUSTRE_ROOT_BMM = '/nsls2/data/bmm'
BMM_lustre_log_file = os.path.join(LUSTRE_ROOT_BMM, 'XAS', 'BMM_master.log')
if os.path.isdir(LUSTRE_ROOT_BMM):
    if not os.path.isfile(BMM_lustre_log_file):
        basedir = os.path.dirname(BMM_lustre_log_file)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        os.mknod(BMM_lustre_log_file)
    if os.path.isfile(BMM_lustre_log_file):
        chmod(BMM_lustre_log_file, 0o644)
        BMM_log_lustre = logging.FileHandler(BMM_lustre_log_file)
        BMM_log_lustre.setFormatter(BMM_formatter)
        BMM_logger.addHandler(BMM_log_lustre)
    
# from BMM.user_ns.bmm import nas_mount_point
# #BMM_nas_log_file = os.path.join(user_ns['nas_mount_point'], 'xf06bm', 'data', 'BMM_master.log')
# BMM_nas_log_file = os.path.join(nas_mount_point, 'xf06bm', 'data', 'BMM_master.log')
# if os.path.isdir('/mnt/nfs/nas1'):
#     if not os.path.isfile(BMM_nas_log_file):
#         basedir = os.path.dirname(BMM_nas_log_file)
#         if not os.path.exists(basedir):
#             os.makedirs(basedir)
#         os.mknod(BMM_nas_log_file)
#     if os.path.isfile(BMM_nas_log_file):
#         chmod(BMM_nas_log_file, 0o644)
#         BMM_log_nas = logging.FileHandler(BMM_nas_log_file)
#         BMM_log_nas.setFormatter(BMM_formatter)
#         BMM_logger.addHandler(BMM_log_nas)

BMM_logger.setLevel(logging.WARNING)

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
    #BMM_logger.addHandler(BMM_log_nas)

## use this command to properly format the log message, manage file permissions, etc
def BMM_log_info(message):
    chmod(BMM_log_master_file, 0o644)
    chmod(BMM_lustre_log_file, 0o644)
    entry = ''
    for line in message.split('\n'):
        entry += '    ' + line + '\n'
    BMM_logger.info(entry)
    chmod(BMM_log_master_file, 0o444)
    chmod(BMM_lustre_log_file, 0o444)


## small effort to obfuscate the web hook URL, which is secret-ish.  See:
##   https://api.slack.com/messaging/webhooks#create_a_webhook
## in the future, this could be an ini with per-user channel URLs...
slack_secret = os.path.join(startup_dir, 'BMM', 'slack_secret')
try:
    with open(slack_secret, "r") as f:
        default_slack_channel = f.read().replace('\n','')
except:
    print(error_msg('\t\t\tslack_secret file not found!'))

def post_to_slack(text):
    try:
        channel = BMMuser.slack_channel
    except:
        channel = default_slack_channel
    if channel is None:
        channel = default_slack_channel
    post = {"text": "{0}".format(text)}
    try:
        json_data = json.dumps(post)
        req = request.Request(channel,
                              data=json_data.encode('ascii'),
                              headers={'Content-Type': 'application/json'}) 
        resp = request.urlopen(req)
    except Exception as em:
        print("EXCEPTION: " + str(em))
        print(f'slack_secret = {slack_secret}')


## Simple but useful guide to configuring a slack app:        
## https://hamzaafridi.com/2019/11/03/sending-a-file-to-a-slack-channel-using-api/
def img_to_slack(imagefile):
    token_file = os.path.join(startup_dir, 'BMM', 'image_uploader_token')
    try:
        with open(token_file, "r") as f:
            token = f.read().replace('\n','')
    except:
        post_to_slack(f'failed to post image (token failure): {imagefile}')
        return()
    client = WebClient(token=token)
    #client = WebClient(token=os.environ['SLACK_API_TOKEN'])
    try:
        response = client.files_upload(channels='#beamtime', file=imagefile)
        # #beamtime channel ID: C016GHBFHTM
        assert response["file"]  # the uploaded file
        icon = 'plot'
        if imagefile.endswith('.jpg.'): icon = 'camera'
        echo_slack(text=os.path.basename(imagefile), img=os.path.basename(imagefile), icon=icon)
    except SlackApiError as e:
        post_to_slack(f'failed to post image (SlackApiError): {imagefile}')
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        print(f"Got an error: {e.response['error']}")
    except Exception as em:
        print("EXCEPTION: " + str(em))
        report(f'failed to post image (other exception): {imagefile}', level='bold', slack=True)


        
def report(text, level=None, slack=False, rid=None):
    '''Print a string to:
      * the log file
      * the screen
      * the BMM beamtime slack channel

    Report level decorations  on screen:

      * 'error' (red)
      * 'warning' (yellow)
      * 'info' (brown)
      * 'url' (undecorated)
      * 'bold' (bright white)
      * 'verbosebold' (bright cyan)
      * 'list' (cyan)
      * 'disconnected' (purple)
      * 'whisper' (gray)

    not matching a report level will be undecorated
    '''
    BMMuser = user_ns['BMMuser']
    BMM_log_info(text)
    screen = emojis.encode(text)
    if color:                   # test that color is sensible...
        if level == 'error':
            print(error_msg(screen))
        elif level == 'warning':
            print(warning_msg(screen))
        elif level == 'info':
            print(info_msg(screen))
        elif level == 'url':
            print(url_msg(screen))
        elif level == 'bold':
            print(bold_msg(screen))
        elif level == 'verbosebold':
            print(verbosebold_msg(screen))
        elif level == 'disconnected':
            print(disconnected_msg(screen))
        elif level == 'list':
            print(list_msg(screen))
        elif level == 'whisper':
            print(whisper(screen))
        else:
            print(screen)
    else:
        print(screen)
    if BMMuser.use_slack and slack:
        post_to_slack(text)
        echo_slack(text=text, img=None, icon='message', rid=rid)


# def echo_slack(text='', img=None, icon='message', rid=None):
#     BMMuser = user_ns['BMMuser']
#     rawlogfile = os.path.join(BMMuser.folder, 'dossier', '.rawlog')
#     rawlog = open(rawlogfile, 'a')
#     rawlog.write(message_div(text, img, icon, rid))
#     rawlog.close()

#     with open(os.path.join(startup_dir, 'tmpl', 'messagelog.tmpl')) as f:
#         content = f.readlines()

#     with open(rawlogfile, 'r') as fd:
#         allmessages = fd.read()
        
#     messagelog = os.path.join(BMMuser.DATA, 'dossier', 'messagelog.html')
#     o = open(messagelog, 'w')
#     o.write(''.join(content).format(text = allmessages, channel = 'BMM #beamtime'))
#     o.close()
        
# # this bit of html+css is derived from https://www.w3schools.com/howto/howto_css_chat.asp
# def message_div(text='', img=None, icon='message', rid=None):
#     if icon == 'message':
#         avatar = 'message.png'
#         image  = ''
#         words  = f'<p>{emojis.encode(text)}</p>'
#     elif icon == 'plot':
#         avatar = 'plot.png'
#         image  = f'<br><a href="../snapshots/{img}"><img class="left" src="../snapshots/{img}" style="height:240px;max-width:320px;width: auto;" alt="" /></a>'
#         words  = f'<span class="figuretitle">{text}</span>'
#     elif icon == 'camera':
#         avatar = 'camera.png'
#         image  = f'<br><a href="../snapshots/{img}"><img class="left" src="../snapshots/{img}" style="height:240px;max-width:320px;width: auto;" alt="" /></a>'
#         words  = f'<span class="figuretitle">{text}</span>'
#     else:
#         return
    
#     thisrid, clss, style = '', 'left', ''
#     if rid is None:
#         avatar = 'blank.png'
#     elif rid is True:
#         clss = 'top'
#         style = ' style="border-top: 1px solid #000;"'  # horizontal line to demark groupings of comments
#     else:
#         thisrid = f' id="{rid}"'
#         clss = 'top'
#         style = ' style="border-top: 1px solid #000;"'
        
#     this = f'''    <div class="container"{thisrid}{style}>
#       <div class="left"><img src="{avatar}" style="width:30px;" /></div>
#       <span class="time-right">{datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")}</span>
#       {words}{image}
#     </div>
# '''
#     return this
        

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


