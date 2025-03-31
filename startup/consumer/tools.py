import os, datetime, emojis, re, configparser


startup_dir = os.path.dirname(os.path.dirname(__file__))
cfile = os.path.join(startup_dir, "BMM_configuration.ini")
profile_configuration = configparser.ConfigParser(interpolation=None)
profile_configuration.read_file(open(cfile))


import redis
from redis_json_dict import RedisJSONDict
nsls2_redis = profile_configuration.get('services', 'nsls2_redis')
redis_client = redis.Redis(host=nsls2_redis)

bmm_redis = profile_configuration.get('services', 'bmm_redis')
rkvs = redis.Redis(host=bmm_redis, port=6379, db=0)

#startup_dir = '/nsls2/data/bmm/shared/config/bluesky/profile_collection/startup/'


DATA_SECURITY = True

def experiment_folder(catalog, uid):

    facility_dict = RedisJSONDict(redis_client=redis_client, prefix='xas-')
    if 'data_session' in catalog[uid].metadata['start']:
        proposal = catalog[uid].metadata['start']['data_session'] #[5:]
    else:
        proposal = facility_dict['xas-data_session']
    if 'XDI' in catalog[uid].metadata['start'] and 'Facility' in catalog[uid].metadata['start']['XDI']:
        cycle = catalog[uid].metadata['start']['XDI']['Facility']['cycle']
    else:
        cycle = facility_dict['xas-cycle']
        
    if DATA_SECURITY:
        folder    = os.path.join('/nsls2', 'data3', 'bmm', 'proposals', cycle, f'{proposal}')
    else:
        proposal  = catalog[uid].metadata['start']['XDI']['Facility']['SAF']
        startdate = catalog[uid].metadata['start']['XDI']['_user']['startdate']
        folder = os.path.join('/nsls2', 'data3', 'bmm', 'XAS', cycle, str(proposal), startdate)
    #print(f'folder is {folder}')
    return folder

def file_resource(catalog, uid):
    '''Dig through the documents for this uid to find the resource
    documents.  Make a list of fully resolved file paths pointed to in
    the resource documents.

    At BMM, these will point to files in the proposal assets folder.
    '''
    docs = catalog[uid].documents()
    found = []
    for d in docs:
        if d[0] == 'resource':
            this = os.path.join(d[1]['root'], d[1]['resource_path'])
            if '_%d' in this or re.search('%\d\.\dd', this) is not None:
                this = this % 0
            found.append(this)
    return found



def echo_slack(text='', img=None, icon='message', rid=None, measurement='xafs'):
    facility_dict = RedisJSONDict(redis_client=redis_client, prefix='xas-')
    base   = os.path.join('/nsls2', 'data3', 'bmm', 'proposals', facility_dict['cycle'], facility_dict['data_session'])
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
    else:
        answer = int(results[-1][-3:]) + 1
    rkvs.set('BMM:next_index', answer)
    print(f"Next index for {stub} in {folder} is {answer}.")


def file_exists(folder, filename, start, stop, number):
    '''Return true is a file of the supplied name exists in the supplied folder.'''
    target = os.path.join(folder, filename) 
    found, text = False, []
    if number is True:
        for i in range(start, stop+1, 1):
            this = f'{target}.{i:03d}'
            #print(this)
            if os.path.isfile(this):
                found = True
                text.append(f'{filename}.{i:03d}')
    else:
        if os.path.isfile(target):
            found = True
            text.append(filename)
        

    if found is True:
        rkvs.set('BMM:file_exists', 'true')
        print(f"{', '.join(text)} found in {folder}.")
    else:
        rkvs.set('BMM:file_exists', 'false')
        print(f'"{filename}" not found in {folder} in range {start} - {stop}.')
            
