
import os, subprocess, shutil, socket
from IPython.paths import get_ipython_module_path
import redis
from BMM.functions import verbosebold_msg, error_msg

###################################################################
# things that are configurable                                    #
###################################################################
rkvs = redis.Redis(host='xf06bm-ioc2', port=6379, db=0)
NAS = '/mnt/nfs/nas1'
SECRETS = os.path.join(NAS, 'xf06bm', 'secrets')
SECRET_FILES = ('slack_secret', 'image_uploader_token')
REDISVAR="BMM:scan:type"
###################################################################


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
      * the public key for xf06bm@xf06bm-ws1 is available or that this is xf06bm-ws1

    For most checks, a failure triggers a corrective action, if
    possible.  Some failures print a warning to screen, with no
    corrective action.

    '''
    print(verbosebold_msg('Checking workspace on this computer ...'))
    initialize_data_directories()
    initialize_beamline_configuration()
    initialize_nas()
    initialize_secrets()
    initialize_redis()
    #initialize_gdrive()
    initialize_ssh()
    

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
        subprocess.run(['git', 'clone', 'https://github.com/NSLS-II-BMM/BMM-beamline-configuration']) 
    os.chdir(here)

def initialize_nas():
    '''Check if a the NAS1 mount point is mounted.  If not, complain on
    screen.

    '''
    if os.path.ismount(NAS):
        print(f'{TAB}Found NAS1 mount point: {CHECK}')
    else:
        print(error_msg('{TAB}NAS1 is not mounted!'))
    

def initialize_secrets():
    '''Check that the Slack secret files are in their expected locations.
    If not, copy them from the NAS server NFS mounted at /mnt/nfs/nas1.

    '''
    STARTUP = os.path.dirname(get_ipython_module_path('BMM.functions'))
    for fname in SECRET_FILES:
        if os.path.isfile(os.path.join(STARTUP, fname)):
            print(f'{TAB}Found {fname} file: {CHECK}')
        else:
            try:
                shutil.copyfile(os.path.join(SECRETS, fname), os.path.join(STARTUP, fname))
                print(f'{TAB}Copied {fname} file')
            except Exception as e:
                print(e)
                print(error_msg(f'{TAB}Failed to copy {os.path.join(SECRETS, fname)}!'))

                
def initialize_redis():
    '''Check to see if a successful response can be obtained from a redis
    server.  If not, complain on screen.

    '''
    if rkvs.get(REDISVAR) is not None:
        print(f'{TAB}Found Redis server: {CHECK}')
    else:
        print(error_msg('{TAB}Did not find redis server'))


def initialize_ssh():
    '''Check to see if xf06bm-ws1 has an authorized key on this computer.
    If not, complain on screen.

    '''
    AK=os.path.join(os.environ["HOME"], '.ssh', 'authorized_keys')
    if not os.path.isfile(AK):
        print(error_msg('{TAB}Did not find public key for xf06bm@xf06bm-ws1'))
        return
    
    with open(AK) as x: f = x.read()
    if socket.gethostname() == 'xf06bm-ws1':
        print(f'{TAB}This is xf06bm-ws1, no public key needed: {CHECK}')
    elif 'xf06bm@xf06bm-ws1' in f:
        print(f'{TAB}Found public key for xf06bm@xf06bm-ws1: {CHECK}')
    else:
        print(error_msg('{TAB}Did not find public key for xf06bm@xf06bm-ws1'))
        
