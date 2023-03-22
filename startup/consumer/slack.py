
import json, os
from urllib import request, parse
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

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
    except SlackApiError as e:
        post_to_slack(f'failed to post image: {imagefile}')
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        print(f"Got an error: {e.response['error']}")
    except Exception as em:
        print("EXCEPTION: " + str(em))
        report(f'failed to post image: {imagefile}', level='bold', slack=True)

