
import json, os, datetime
from urllib import request, parse
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from BMM_common.echo_slack import echo_slack

import redis
rkvs = redis.Redis(host='xf06bm-ioc2', port=6379, db=0)

startup_dir = '/home/xf06bm/.ipython/profile_collection/startup/'

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
    #try:
    #    channel = BMMuser.slack_channel
    #except:
    #    channel = default_slack_channel
    #if channel is None:
    channel = default_slack_channel
    post = {"text": "{0}".format(text)}
    try:
        json_data = json.dumps(post)
        req = request.Request(channel,
                              data=json_data.encode('ascii'),
                              headers={'Content-Type': 'application/json'}) 
        resp = request.urlopen(req)
        echo_slack(text=text, img=None, icon='message', rid=None)
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
        post_to_slack(f'failed to post image: {imagefile}')
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
        post_to_slack(f'failed to post image: {imagefile}')
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        print(f"Got an error: {e.response['error']}")
    except Exception as em:
        print("EXCEPTION: " + str(em))
        post_to_slack(f'failed to post image: {imagefile}')



# def echo_slack(text='', img=None, icon='message', rid=None):
#     #BMMuser = user_ns['BMMuser']
#     folder = rkvs.get('BMM:user:folder').decode('utf-8')
#     rawlogfile = os.path.join(folder, 'dossier', '.rawlog')
#     rawlog = open(rawlogfile, 'a')
#     rawlog.write(message_div(text, img, icon, rid))
#     rawlog.close()

#     with open(os.path.join(startup_dir, 'tmpl', 'messagelog.tmpl')) as f:
#         content = f.readlines()

#     with open(rawlogfile, 'r') as fd:
#         allmessages = fd.read()
        
#     messagelog = os.path.join(folder, 'dossier', 'messagelog.html')
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
        
