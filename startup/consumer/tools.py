import os, datetime, emojis, re

DATA_SECURITY = True

def experiment_folder(catalog, uid):
    proposal  = catalog[uid].metadata['start']['XDI']['Facility']['GUP']
    #proposal  = catalog[uid].metadata['start']['data_session'][5:]
    cycle     = catalog[uid].metadata['start']['XDI']['Facility']['cycle']
    if DATA_SECURITY:
        folder    = os.path.join('/nsls2', 'data3', 'bmm', 'proposals', cycle, f'pass-{proposal}')
    else:
        proposal  = catalog[uid].metadata['start']['XDI']['Facility']['SAF']
        startdate = catalog[uid].metadata['start']['XDI']['_user']['startdate']
        folder = os.path.join('/nsls2', 'data3', 'bmm', 'XAS', cycle, str(proposal), startdate)
    print(f'folder is {folder}')
    return folder



import redis
rkvs = redis.Redis(host='xf06bm-ioc2', port=6379, db=0)

startup_dir = '/nsls2/data/bmm/shared/config/bluesky/profile_collection/startup/'

def echo_slack(text='', img=None, icon='message', rid=None, measurement='xafs'):
    #BMMuser = user_ns['BMMuser']
    folder = rkvs.get('BMM:user:folder').decode('utf-8')
    proposal = '301027'
    base   = os.path.join('/nsls2', 'data3', 'bmm', 'proposals', '2024-2', f'pass-{proposal}')
    rawlogfile = os.path.join(base, 'dossier', '.rawlog')
    rawlog = open(rawlogfile, 'a')
    rawlog.write(message_div(text, img=img, icon=icon, rid=rid, measurement=measurement))
    rawlog.close()

    with open(os.path.join(startup_dir, 'tmpl', 'messagelog.tmpl')) as f:
        content = f.readlines()

    with open(rawlogfile, 'r') as fd:
        allmessages = fd.read()
        
    messagelog = os.path.join(base, 'dossier', 'messagelog.html')
    o = open(messagelog, 'w')
    o.write(''.join(content).format(text = allmessages, channel = 'BMM #beamtime'))
    o.close()
        
# this bit of html+css is derived from https://www.w3schools.com/howto/howto_css_chat.asp
def message_div(text='', img=None, icon='message', rid=None, measurement='xafs'):
    if measurement == 'raster':
        folder = 'maps'
    elif measurement == 'xrf':
        folder = 'XRF'
    else:
        folder = 'snapshots'
        
    if icon == 'message':
        avatar = 'message.png'
        image  = ''
        words  = f'<p>{emojis.encode(text)}</p>'
    elif icon == 'plot':
        avatar = 'plot.png'
        image  = f'<br><a href="../{folder}/{img}"><img class="left" src="../{folder}/{img}" style="height:240px;max-width:320px;width: auto;" alt="" /></a>'
        words  = f'<span class="figuretitle">{text}</span>'
    elif icon == 'camera':
        avatar = 'camera.png'
        image  = f'<br><a href="../{folder}/{img}"><img class="left" src="../{folder}/{img}" style="height:240px;max-width:320px;width: auto;" alt="" /></a>'
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
        




def next_index(folder, stub):
    '''Find the next numeric filename extension for a filename stub in folder.'''
    listing = os.listdir(folder)
    r = re.compile(re.escape(stub) + '\.\d+')
    results = sorted(list(filter(r.match, listing)))
    if len(results) == 0:
        answer = 1
    answer = int(results[-1][-3:]) + 1
    rkvs.set('BMM:next_index', answer)
    
