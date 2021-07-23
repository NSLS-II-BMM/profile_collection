import subprocess
import os

from BMM.functions import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper

from IPython import get_ipython
from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

from BMM.user_ns.bmm import BMMuser


def athena():
    os.environ['DEMETER_FORCE_IFEFFIT'] = '1' 
    subprocess.Popen(["dathena"])
    
def hephaestus():
    os.environ['DEMETER_FORCE_IFEFFIT'] = '1' 
    subprocess.Popen(["dhephaestus"])


TOPRJ = '/home/xf06bm/bin/toprj.pl'

def toprj(folder=None, name=None, base=None, start=None, end=None, bounds=None, mode=None):
    ##########################################################################################
    # Hi Tom!  Yes, I am making a system call right here.  Again.  And to run a perl script, #
    # no less!  Are you having an aneurysm?  If so, please get someone to film it.  I'm      #
    # going to want to see that!  XOXO, Bruce                                                #
    ##########################################################################################
    os.environ['DEMETER_FORCE_IFEFFIT'] = '1'
    bail = 0
    if folder is None:
        folder = BMMuser.DATA
    if name   is None:
        print(error_msg("cannot run toprj, missing name argument"))
        bail = 1
    if base   is None:
        print(error_msg("cannot run toprj, missing base argument"))
        bail = 1
    if start  is None:
        print(error_msg("cannot run toprj, missing start argument"))
        bail = 1
    if end    is None:
        print(error_msg("cannot run toprj, missing end argument"))
        bail = 1
    if bounds is None:
        print(error_msg("cannot run toprj, missing bounds argument"))
        bail = 1
    if mode   is None:
        mode = 'transmission'
    if bail == 1:
        return()
        
    print(f'{TOPRJ} --folder="{folder}" --name={base} --base={base} --start={start} --end={end} --bounds="{bounds}" --mode={mode}')
    result = subprocess.run([TOPRJ,
                             '--folder', '%s' % folder,       # data folder
                             '--name',   '%s' % name,         # file stub
                             '--base',   '%s' % base,         # basename (with scan sequence numbering)		 
                             '--start',  '%d' % int(start),   # first suffix number					 
                             '--end',    '%d' % int(end),     # last suffix number					 
                             '--bounds', '%s' % bounds,       # scan boundaries (used to distinguish XANES from EXAFS)
                             '--mode',   '%s' % mode],        # measurement mode
                            stdout=subprocess.PIPE)
    pngfile = os.path.join(folder, 'snapshots', base+'.png')
    #png = open(pngfile, 'wb')    
    #png.write(result.stdout)
    #png.close()
    return(pngfile)

