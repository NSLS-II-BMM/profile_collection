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

from IPython import get_ipython
user_ns = get_ipython().user_ns

gdrive_folder = os.path.join(os.environ['HOME'], 'gdrive')



        
def copy_to_gdrive(fname):
    BMMuser = user_ns['BMMuser']
    user_gdrive_folder = os.path.join(gdrive_folder, 'Data', BMMuser.name, BMMuser.date)
    print(f'copying {fname} to {user_gdrive_folder}')
    shutil.copyfile(os.path.join(BMMuser.folder, fname), os.path.join(user_gdrive_folder, fname), follow_symlinks=True)
    return()

def synch_gdrive_folder(prefix=''):
    BMMuser = user_ns['BMMuser']
    print(f'{prefix}updating {gdrive_folder}')
    user_gdrive_folder = os.path.join(gdrive_folder, 'Data', BMMuser.name, BMMuser.date)
    here = os.getcwd()
    os.chdir(user_gdrive_folder)
    subprocess.run(['/home/xf06bm/gopath/bin/drive', 'push', '-quiet', '.']) 
    os.chdir(here)
    return()

def make_gdrive_folder(prefix='', update=True):
    BMMuser = user_ns['BMMuser']
    user_folder = os.path.join(gdrive_folder, 'Data', BMMuser.name, BMMuser.date)
    BMMuser.gdrive = user_folder
    os.makedirs(user_folder, exist_ok=True)
    for f in ('dossier', 'prj', 'snapshots', 'XRF'):
        os.makedirs(os.path.join(user_folder, f), exist_ok=True)
    if update is True:
        synch_gdrive_folder(prefix)
    return(user_folder)
