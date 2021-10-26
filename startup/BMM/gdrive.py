#####################################################################################
# This uses the drive tool (written in go) from https://github.com/odeke-em/drive   #
# and installed in $HOME/go/bin/                                                    #
#                                                                                   #
# This is an inelegant solution using a system call.  I could not make heads        #
# or tails out of Google's python API.                                              #
#                                                                                   #
# Until we have access to central stores here at BNL, this is ... good enough...    #
#####################################################################################
# Still need to manually grant access to the drive folder to each user, same for    #
# Slack.                                                                            #
#####################################################################################

import os, subprocess, shutil

from BMM.functions import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

#from BMM.user_ns.bmm import BMMuser

gdrive_folder = os.path.join(os.environ['HOME'], 'gdrive')


def determine_bin_location():
    if 'xf06bm-ws3' in user_ns['BMMuser'].host:
        return('/home/xf06bm/go/bin/drive')
    elif 'xf06bm-ws1' in user_ns['BMMuser'].host:
        return('/home/xf06bm/gopath/bin/drive')
    elif 'xf06bm-ws5' in user_ns['BMMuser'].host:
        return('/home/xf06bm/git/drive/bin/drive_linux')
    else:
        return(None)
        
def copy_to_gdrive(fname):
    user_gdrive_folder = os.path.join(gdrive_folder, 'Data', user_ns['BMMuser'].name, user_ns['BMMuser'].date)
    print(f'copying {fname} to {user_gdrive_folder}')
    shutil.copyfile(os.path.join(user_ns['BMMuser'].folder, fname), os.path.join(user_gdrive_folder, fname), follow_symlinks=True)
    return()

def rsync_to_gdrive():
    user_gdrive_folder = os.path.join(gdrive_folder, 'Data', user_ns['BMMuser'].name, user_ns['BMMuser'].date)
    print(f'syncing user folder to {user_gdrive_folder}')
    subprocess.run(['rsync', '-aq', user_ns['BMMuser'].folder, user_gdrive_folder]) 
    
def synch_gdrive_folder(prefix=''):
    print(f'{prefix}syncing {gdrive_folder}')
    user_gdrive_folder = os.path.join(gdrive_folder, 'Data', user_ns['BMMuser'].name, user_ns['BMMuser'].date)
    location = determine_bin_location()
    if location is None:
        print(error_msg('Unable to synch Google drive: could not determine drive program location.'))
    else:
        here = os.getcwd()
        os.chdir(user_gdrive_folder)
        subprocess.run([location, 'push', '-quiet', '.']) 
        os.chdir(here)
    return()

def make_gdrive_folder(prefix='', update=True):
    from BMM.user_ns.bmm import BMMuser
    user_folder = os.path.join(gdrive_folder, 'Data', BMMuser.name, BMMuser.date)
    BMMuser.gdrive = user_folder
    os.makedirs(user_folder, exist_ok=True)
    for f in ('dossier', 'prj', 'snapshots', 'XRF'):
        os.makedirs(os.path.join(user_folder, f), exist_ok=True)
    if update is True:
        synch_gdrive_folder(prefix)
    return(user_folder)
