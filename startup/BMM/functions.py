import os, time, datetime
from numpy import pi, sin, cos, arcsin, sqrt
from IPython import get_ipython
user_ns = get_ipython().user_ns


## users find "less" unfamiliar and mistakes are made / confusion is
## had when doing <function>??  `cat` seems less likely to befuddle
## the hoi palloi, but it's not a pager.
##
## trying "most".  It's a pager, like less, but has helpful hints in
## the bottom gutter.  Let's see how it goes....
os.environ['PAGER'] = 'most'

get_ipython().magic(u"%xmode Plain")

## some global parameters
BMM_STAFF = ('Bruce Ravel', 'Jean Jordan-Sweet', 'Joe Woicik')
HBARC = 1973.27053324


# Black, Blue, Brown, Cyan, DarkGray, Green, NoColor, Normal, Purple,
# Red, White, Yellow,

# LightBlue, LightCyan, LightGray, LightGreen, LightPurple, LightRed,

# BlinkBlack, BlinkBlue, BlinkCyan, BlinkGreen, BlinkLightGray,
# BlinkPurple, BlinkRed, BlinkYellow,

from IPython.utils.coloransi import TermColors as color
def colored(text, tint='white', attrs=[]):
    '''
    A simple wrapper around IPython's interface to TermColors
    '''
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
    return text
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
    return colored(text, 'purple')
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
    if user_ns['dcm']._crystal is '111':
        m = -3.9241e-06 
        b = 4.15159473
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

## CRUDE HACK ALERT! inflection.py is in ~/.ipython (https://pypi.org/project/inflection/)
import inflection
def inflect(word, number):
    if abs(number) == 1:
        return('%d %s' % (number, inflection.singularize(word)))
    else:
        return('%d %s' % (number, inflection.pluralize(word)))

import textwrap
import ansiwrap
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
    user_ns['rkvs'].set('BMM:scan:type',      '')
    user_ns['rkvs'].set('BMM:scan:starttime', '')
    user_ns['rkvs'].set('BMM:scan:estimated', '')
    

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
    BMMuser = user_ns['BMMuser']
    options = [x for x in os.listdir(BMMuser.folder) if x.endswith(suffix)]
    options = sorted(options)
    print(bold_msg(f'Looking in {BMMuser.folder}\n'))
    
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
    if user_ns['with_xspress3'] and any(x in mode for x in ('xs', 'fluo', 'flou', 'both')):
        return 'xs'
    elif not user_ns['with_xspress3'] and any(x in mode for x in ('fluo', 'flou', 'both')):
        return 'fluo'
    elif mode == 'ref':
        return 'ref'
    else:
        return 'trans'
