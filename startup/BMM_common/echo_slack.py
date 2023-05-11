
import os, datetime, emojis

import redis
rkvs = redis.Redis(host='xf06bm-ioc2', port=6379, db=0)

startup_dir = '/nsls2/data/bmm/shared/config/bluesky/profile_collection/startup/'

def echo_slack(text='', img=None, icon='message', rid=None):
    #BMMuser = user_ns['BMMuser']
    folder = rkvs.get('BMM:user:folder').decode('utf-8')
    rawlogfile = os.path.join(folder, 'dossier', '.rawlog')
    rawlog = open(rawlogfile, 'a')
    rawlog.write(message_div(text, img, icon, rid))
    rawlog.close()

    with open(os.path.join(startup_dir, 'tmpl', 'messagelog.tmpl')) as f:
        content = f.readlines()

    with open(rawlogfile, 'r') as fd:
        allmessages = fd.read()
        
    messagelog = os.path.join(folder, 'dossier', 'messagelog.html')
    o = open(messagelog, 'w')
    o.write(''.join(content).format(text = allmessages, channel = 'BMM #beamtime'))
    o.close()
        
# this bit of html+css is derived from https://www.w3schools.com/howto/howto_css_chat.asp
def message_div(text='', img=None, icon='message', rid=None):
    if icon == 'message':
        avatar = 'message.png'
        image  = ''
        words  = f'<p>{emojis.encode(text)}</p>'
    elif icon == 'plot':
        avatar = 'plot.png'
        image  = f'<br><a href="../snapshots/{img}"><img class="left" src="../snapshots/{img}" style="height:240px;max-width:320px;width: auto;" alt="" /></a>'
        words  = f'<span class="figuretitle">{text}</span>'
    elif icon == 'camera':
        avatar = 'camera.png'
        image  = f'<br><a href="../snapshots/{img}"><img class="left" src="../snapshots/{img}" style="height:240px;max-width:320px;width: auto;" alt="" /></a>'
        words  = f'<span class="figuretitle">{text}</span>'
    else:
        return
    
    thisrid, clss, style = '', 'left', ''
    if rid is None:
        avatar = 'blank.png'
    elif rid is True:
        clss = 'top'
        style = ' style="border-top: 1px solid #000;"'  # horizontal line to demark groupings of comments
    else:
        thisrid = f' id="{rid}"'
        clss = 'top'
        style = ' style="border-top: 1px solid #000;"'
        
    this = f'''    <div class="container"{thisrid}{style}>
      <div class="left"><img src="{avatar}" style="width:30px;" /></div>
      <span class="time-right">{datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")}</span>
      {words}{image}
    </div>
'''
    return this
        
