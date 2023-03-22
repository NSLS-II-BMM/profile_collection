import os, time, datetime, psutil, glob
import inflection, textwrap, ansiwrap, termcolor
from numpy import pi, sin, cos, arcsin, sqrt

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

## trying "most".  It's a pager, like less, but has helpful hints in
## the bottom gutter.  Let's see how it goes....
os.environ['PAGER'] = 'most'


## some global parameters
BMM_STAFF  = ('Bruce Ravel', 'Jean Jordan-Sweet', 'Joe Woicik', 'Vesna Stanic')
HBARC      = 1973.27053324
LUSTRE_XAS = os.path.join('/nsls2', 'data', 'bmm', 'XAS')

PROMPT = f"[{termcolor.colored('yes', attrs=['underline'])}: y then Enter (or just Enter) ● {termcolor.colored('no', attrs=['underline'])}: n then Enter] "



# Black, Blue, Brown, Cyan, DarkGray, Green, NoColor, Normal, Purple,
# Red, White, Yellow,

# LightBlue, LightCyan, LightGray, LightGreen, LightPurple, LightRed,

# BlinkBlack, BlinkBlue, BlinkCyan, BlinkGreen, BlinkLightGray,
# BlinkPurple, BlinkRed, BlinkYellow,

try:
    from bluesky_queueserver import is_re_worker_active
except ImportError:
    # TODO: delete this when 'bluesky_queueserver' is distributed as part of collection environment
    def is_re_worker_active():
        return False

def colored(text, tint='white', attrs=[]):
    '''
    A simple wrapper around IPython's interface to TermColors
    '''
    if not is_re_worker_active():
        from IPython.utils.coloransi import TermColors as color
        tint = tint.lower()
        if 'dark' in tint:
            tint = 'Dark' + tint[4:].capitalize()
        elif 'light' in tint:
            tint = 'Light' + tint[5:].capitalize()
        elif 'blink' in tint:
            tint = 'Blink' + tint[5:].capitalize()
        elif 'no' in tint:
            tint = 'Normal'
        else:
            tint = tint.capitalize()
        return '{0}{1}{2}'.format(getattr(color, tint), text, color.Normal)
    else:
        return(text)
        
def run_report(thisfile, text=None):
    '''
    Noisily proclaim to be importing a file of python code.
    '''
    add = '...'
    if text is not None:
        add = f'({text})'
    importing = 'Importing'
    if thisfile[0] == '\t':
        importing = '\t'
    print(colored(f'{importing} {thisfile.split("/")[-1]} {add}', 'lightcyan'))


def error_msg(text):
    '''Red text'''
    return colored(text, 'lightred')
def warning_msg(text):
    '''Yellow text'''
    return colored(text, 'yellow')
def go_msg(text):
    '''Green text'''
    return colored(text, 'lightgreen')
def url_msg(text):
    '''Undecorated text, intended for URL decoration...'''
    return colored(text, 'normal')
def bold_msg(text):
    '''Bright white text'''
    return colored(text, 'white')
def verbosebold_msg(text):
    '''Bright cyan text'''
    return colored(text, 'lightcyan')
def list_msg(text):
    '''Cyan text'''
    return colored(text, 'cyan')
def disconnected_msg(text):
    '''Purple text'''
    return colored(text, 'lightpurple')
def info_msg(text):
    '''Brown text'''
    return colored(text, 'brown')
def whisper(text):
    '''Light gray text'''
    return colored(text, 'darkgray')

##BMM_logfile = '/home/bravel/BMM_master.log'

KTOE = 3.8099819442818976
def etok(ee):
    '''convert relative energy to wavenumber'''
    return sqrt(ee/KTOE)
def ktoe(k):
    '''convert wavenumber to relative energy'''
    return k*k*KTOE

def e2l(val):
    """Convert absolute photon energy to photon wavelength"""
    return 2*pi*HBARC/val
l2e = e2l



## see calibrate_pitch in BMM/mono_calibration.py
def approximate_pitch(energy):
    if user_ns['dcm']._crystal == '111':
        m = -4.5329e-06
        b = 4.26511766
        return(m*energy + b)
    else:
        m = -2.5276e-06
        b = 2.36374402
        return(m*energy + b)
        

def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def now(fmt="%Y-%m-%dT%H-%M-%S"):
    return datetime.datetime.now().strftime(fmt)

def inflect(word, number):
    if abs(number) == 1:
        return('%d %s' % (number, inflection.singularize(word)))
    else:
        return('%d %s' % (number, inflection.pluralize(word)))

def boxedtext(title, text, tint, width=75):
    '''
    Put text in a lovely unicode block element box.  The top
    of the box will contain a title.  The box elements will
    be colored.
    '''
    remainder = width - 2 - len(title)
    ul        = u'\u2554' # u'\u250C'
    ur        = u'\u2557' # u'\u2510'
    ll        = u'\u255A' # u'\u2514'
    lr        = u'\u255D' # u'\u2518'
    bar       = u'\u2550' # u'\u2500'
    strut     = u'\u2551' # u'\u2502'
    template  = '%-' + str(width) + 's'

    print('')
    print(colored(''.join([ul, bar*3, ' ', title, ' ', bar*remainder, ur]), tint))
    for line in text.split('\n'):
        lne = line.rstrip()
        add = ' '*(width-ansiwrap.ansilen(lne))
        print(' '.join([colored(strut, tint), lne, add, colored(strut, tint)]))
    print(colored(''.join([ll, bar*(width+3), lr]), tint))


def clear_dashboard():
    '''Clean up in a way that helps the cadashboard utility'''
    #from BMM.workspace import rkvs
    rkvs = user_ns['rkvs']
    rkvs.set('BMM:scan:type',      '')
    rkvs.set('BMM:scan:starttime', '')
    rkvs.set('BMM:scan:estimated', '')
    

def countdown(t):
    transition = max(int(t/10), 2)
    while t:
        mins, secs = divmod(t, 60)
        if t > transition:
            timeformat = bold_msg('{:02d}:{:02d}'.format(mins, secs))
        else:
            timeformat = warning_msg('{:02d}:{:02d}'.format(mins, secs))
        print(timeformat, end='\r')
        time.sleep(1)
        t -= 1
    print('Done!', end='\r')


def elapsed_time(start):
    end = time.time()
    hours, rest = divmod(end-start, 3600)
    minutes, seconds = divmod(rest, 60)
    print(f'\n\nThat took {hours} hours, {minutes} minutes, {seconds:.0f} seconds')
    

def present_options(suffix='xlsx'):
    options = [x for x in os.listdir(user_ns['BMMuser'].folder) if x.endswith(suffix)]
    options = sorted(options)
    print(bold_msg(f'Looking in {user_ns["BMMuser"].folder}\n'))
    
    print(f'Select your {suffix} file:\n')
    for i,x in enumerate(options):
        print(f' {i+1:2}: {x}')

    print('\n  r: return')
    choice = input("\nSelect a file > ")
    try:
        if int(choice) > 0 and int(choice) <= len(options):
            return options[int(choice)-1]
        else:
            return None
    except:
        return None

def plotting_mode(mode):
    mode = mode.lower()
    if user_ns['with_xspress3'] and mode == 'xs1':
        return 'xs1'
    elif user_ns['with_xspress3'] and any(x in mode for x in ('xs', 'fluo', 'flou', 'both')):
        return 'xs'
    elif not user_ns['with_xspress3'] and any(x in mode for x in ('fluo', 'flou', 'both')):
        return 'fluo'
    elif mode == 'ref':
        return 'ref'
    elif mode == 'yield':
        return 'yield'
    elif mode == 'test':
        return 'test'
    else:
        return 'trans'


def examine_fmbo_motor_group(motor_group, TAB='\t\t\t\t'):
    CHECK = '\u2714'
    for m in motor_group:
        if 'SynAxis' in f'{m}':
            print(disconnected_msg(f'{TAB}{m.name} is not connected.'))
        elif m.name in ('dcm_y', 'm2_bender'):
            print(whisper(f'{TAB}{m.name} is normally run unhomed {CHECK}'))
        elif m.hocpl.get() == 1:
            print(f'{TAB}{m.name} {CHECK}')
        elif 'filter' in m.name:
            print(whisper(f'{TAB}{m.name} is not homed, but that\'s probably OK.'))
        else:
            print(error_msg(f'{TAB}{m.name} is not homed.'))

def examine_xafs_motor_group(motor_group, TAB='\t\t\t\t'):
    CHECK = '\u2714'
    for m in motor_group:
        if 'SynAxis' in f'{m}':
            print(disconnected_msg(f'{TAB}{m.name} is not connected.'))
        else:
            print(f'{TAB}{m.name} {CHECK}')
      

def clean_img():
    '''Kill any outstanding "display" processes (i.e. ImageMagick's
    display).  Then remove any .PNG files PIL has left lying
    around in /tmp.  Finally, explicitly close the previous
    filehandle.

    This takes no care to verify neither that PIL launched the
    display process nor that PIL wrote the .PNG file in /tmp.

    Note that this will kill any other "display" processes
    running.  At NSLS-II, the centrally managed screen locker is
    configured to use feh to show a transparent png when the
    screen is locked.  Thus, display was chosen as the viewer
    rather than feh (although ownership would likely preclude
    terminating the screenlocker process).

    '''
    for proc in psutil.process_iter():
        if proc.name() == "display":
            proc.kill()
    for f in glob.glob('/tmp/tmp*.PNG'):
        try:
            os.remove(f)
        except:
            print(whisper(f'unable to delete {f} while cleaning up /tmp'))
    try:
        if BMMuser.display_img is not None:
            BMMuser.display_img.close()
    except:
        pass
