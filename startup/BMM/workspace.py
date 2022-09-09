from ophyd import EpicsSignalRO
import os, subprocess, shutil, socket
import redis
import BMM.functions  #from BMM.functions import verbosebold_msg, error_msg
from BMM.user_ns.base import startup_dir

if not os.environ.get('AZURE_TESTING'):
    redis_host = 'xf06bm-ioc2'
else:
    redis_host = '127.0.0.1'


class NoRedis():
    def set(self, thing, otherthing):
        return None
    def get(self, thing):
        return None
    
###################################################################
# things that are configurable                                    #
###################################################################
rkvs = redis.Redis(host=redis_host, port=6379, db=0)
#rkvs = NoRedis()
NAS = '/mnt/nfs/nas1'
LUSTRE_ROOT = '/nsls2/data'
LUSTRE_ROOT_BMM = '/nsls2/data/bmm'
SECRETS = os.path.join(LUSTRE_ROOT_BMM, 'XAS', 'secrets')
SECRET_FILES = ('slack_secret', 'image_uploader_token')
REDISVAR="BMM:scan:type"
###################################################################

rkvs.set('BMM:scan:type', 'idle')

def rkvs_keys(printed=True):
    '''Convert rkvs.keys() into a list of normal strings

    With printed=True, write a table of keys and values to the screen

    With printed=False, return a list containing keys as normal strings
    '''
    keys = sorted(list(x.decode('UTF-8') for x in rkvs.keys()))
    if printed is True:
        for k in keys:
            if rkvs.type(k) == b'string':
                print(f'{k:25} {rkvs.get(k).decode("UTF-8")}')
            elif rkvs.type(k) == b'list':
                this = ' '.join(x.decode('UTF-8') for x in rkvs.lrange(k, 0, -1))
                print(f'{k:25} {this}')
            else:
                #print(f'{k:25} {rkvs.get(k)}')
                pass
        return()
    else:
        return(keys)
    
CHECK = '\u2714'
TAB = '\t\t\t'

def initialize_workspace():
    '''Perform a series of checks to see if the workspace on this computer
    is set up as expected by the BMM data collection profile.  This
    includes checks that:
      * various directories exist
      * NAS1 is mounted
      * a redis server is available
      * certain git repositories are cloned onto this computer
      * authentication files for Slack are available.
      * the public key for xf06bm@xf06bm-ws3 is available or that this is xf06bm-ws3

    For most checks, a failure triggers a corrective action, if
    possible.  Some failures print a warning to screen, with no
    corrective action.

    '''
    print(BMM.functions.verbosebold_msg('Checking workspace on this computer ...'))
    check_workstation_access()
    check_profile_branch()
    initialize_data_directories()
    #initialize_beamline_configuration()
    initialize_lustre()
    #initialize_nas()
    initialize_secrets()
    initialize_redis()
    #initialize_gdrive()
    #initialize_ssh()
    
def check_workstation_access():
    wa = EpicsSignalRO('XF:06BM-CT{}Prmt:RemoteExp-Sel',   name='write_access')
    if wa.get() == 0:
        print(f'{TAB}*** Uh oh!  The beamline is not enabled for write access to PVs!')
        print(f'{TAB}    You need to get a beamline staff person to do:')
        print(f'{TAB}       caput XF:06BM-CT{{}}Prmt:RemoteExp-Sel 1')
        print(f'{TAB}    then restart bsui')
        ## the next line is intended to trigger an immediate error and return to the IPython command line
        wa.put(1)
        
def check_profile_branch():
    here = os.getcwd()
    os.chdir(os.path.dirname(startup_dir))
    try:
        branch = subprocess.check_output(['git', 'branch', '--show-current']).decode("utf-8")[:-1]
    except subprocess.CalledProcessError:
        branch = "not a git repository"
    print(f'{TAB}Using profile branch {branch}')
    os.chdir(here)
    
def check_directory(dir, desc):
    if os.path.isdir(dir):
        print(f'{TAB}{desc.capitalize()} directory {dir}: {CHECK}')
        return True
    else:
        print(f'{TAB}Making {desc} directory {dir}')
        os.mkdir(dir)
        return False

    
def initialize_data_directories():
    '''Verify that a Data directory is available under the home of the
    user running bsui.  Then verify that several subdirectories exist.
    Create any missing directories.

    '''
    DATA=f'{os.environ["HOME"]}/Data'
    check_directory(DATA, 'data')
    for sub in ('bucket', 'Staff', 'Visitors'):
        folder = f'{DATA}/{sub}'
        check_directory(folder, 'data')


def initialize_beamline_configuration():
    '''Check that a git directory exists beneath the home of the usr
    running bsui.  Create the git directory and clone the
    BMM-beamline-configuration repository if absent.  If present, pull
    from the upstream repository to be sure the modes JSON file is up
    to date.

    '''
    GIT=f'{os.environ["HOME"]}/git'
    check_directory(GIT, 'git')
    BLC = f'{GIT}/BMM-beamline-configuration'
    existed = check_directory(BLC, 'git')
    here = os.getcwd()
    if existed:
        os.chdir(BLC)
        subprocess.run(['git', 'pull']) 
    else:
        os.chdir(GIT)
        subprocess.run(['git', 'clone', '-q', 'https://github.com/NSLS-II-BMM/BMM-beamline-configuration']) 
    os.chdir(here)

def initialize_nas():
    '''Check if a the NAS1 mount point is mounted.  If not, complain on
    screen.

    '''
    if os.path.ismount(NAS):
        print(f'{TAB}Found NAS1 mount point: {CHECK}')
    else:
        print(BMM.functions.error_msg(f'{TAB}NAS1 is not mounted!'))

def initialize_lustre():
    '''Check if a the Lustre mount point for data directories is mounted.
    If not, complain on screen.

    '''
    if os.path.ismount(LUSTRE_ROOT_BMM):
        print(f'{TAB}Found Lustre mount point: {CHECK}')
    else:
        print(BMM.functions.error_msg(f'{TAB}Lustre is not mounted!'))
        

def initialize_secrets():
    '''Check that the Slack secret files are in their expected locations.
    If not, copy them from Lustre at /nsls2/data/bmm/XAS/secrets.

    '''
    STARTUP = os.path.join(startup_dir, 'BMM')
    for fname in SECRET_FILES:
        if os.path.isfile(os.path.join(STARTUP, fname)):
            print(f'{TAB}Found {fname} file: {CHECK}')
        else:
            try:
                shutil.copyfile(os.path.join(SECRETS, fname), os.path.join(STARTUP, fname))
                print(f'{TAB}Copied {fname} file')
            except Exception as e:
                print(e)
                print(BMM.functions.error_msg(f'{TAB}Failed to copy {os.path.join(SECRETS, fname)}!'))

                
def initialize_redis():
    '''Check to see if a successful response can be obtained from a redis
    server.  If not, complain on screen.

    '''
    if rkvs.get(REDISVAR) is not None:
        print(f'{TAB}Found Redis server: {CHECK}')
    else:
        print(BMM.functions.error_msg(f'{TAB}Did not find redis server'))


def initialize_ssh():
    '''Check to see if xf06bm-ws3 has an authorized ssh key from this
    computer.  If not, complain on screen.

    '''
    if 'xf06bm-ws3' in socket.gethostname():
        print(f'{TAB}This is xf06bm-ws3, no ssh key needed: {CHECK}')
        return
    s = subprocess.run(['ssh', '-q', '-oBatchMode=yes', 'xf06bm@xf06bm-ws1', 'true'])
    if s.returncode == 0:
        print(f'{TAB}Key exists for xf06bm@xf06bm-ws3: {CHECK}')
    else:
        print(BMM.functions.error_msg(f'{TAB}Key does not exist for xf06bm@xf06bm-ws1'))
