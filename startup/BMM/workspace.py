
import os, subprocess, shutil
from IPython.paths import get_ipython_module_path
import redis
from BMM.functions import verbosebold_msg, error_msg

###################################################################
# things that are configurable                                    #
###################################################################
rkvs = redis.Redis(host='xf06bm-ioc2', port=6379, db=0)
SECRETS = "/mnt/nfs/nas1/xf06bm/secrets/"
SECRET_FILES = ('slack_secret', 'image_uploader_token')
REDISVAR="BMM:scan:type"
###################################################################


CHECK = '\u2714'
TAB = '\t\t\t'

def initialize_workspace():
    '''Perform a series of checks to see if the workspace on this computer
    is set up as expected by the BMM data collection profile.  This
    includes checks for:
      * the presence of various directories
      * that a redis server is available
      * that certain git repositories are cloned onto this computer
      * that authentication files for Slack are available.

    For most checks, a failure triggers a corrective action.  The
    exception is that a missing redis server is flagged on screen, but
    no corrective action is attempted.

    '''
    print(verbosebold_msg('Checking workspace on this computer ...'))
    initialize_data_directories()
    initialize_beamline_configuration()
    initialize_secrets()
    initialize_redis()
    #initialize_gdrive()


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
                shutil.copyfile(os.path.join(SECRETS, fname), STARTUP)
                print(f'{TAB}Copied {fname} file')
            except:
                print(error_msg(f'{TAB}Failed to copy {fname} file!'))

                
def initialize_redis():
    '''Check to see if a successful response can be obtained from a redis
    server.  If not, complain on screen.

    '''
    if rkvs.get(REDISVAR) is not None:
        print(f'{TAB}Found Redis server: {CHECK}')
    else:
        print(error_msg('{TAB}Did not find redis server'))
