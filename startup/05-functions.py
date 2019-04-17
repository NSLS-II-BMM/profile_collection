import os
from numpy import pi, sin, cos, arcsin, sqrt

import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="CA.Client.Exception")

## users find "less" unfamiliar and mistakes are made / confusion is
## had when doing <function>??  `cat` seems less likely to befuddle
## folk.
os.environ['PAGER'] = 'cat'


## some global parameters
BMM_STAFF = ('Bruce Ravel', 'Jean Jordan-Sweet', 'Joe Woicik')
_user_is_defined = False
DATA = os.path.join(os.getenv('HOME'), 'Data', 'bucket') + '/'


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

def run_report(thisfile):
    '''
    Noisily proclaim to be importing a file of python code.
    '''
    print(colored('Importing %s ...' % thisfile.split('/')[-1], 'lightcyan'))

run_report(__file__)

get_ipython().magic(u"%xmode Plain")


def error_msg(text):
    return colored(text, 'lightred')
def warning_msg(text):
    return colored(text, 'yellow')
def url_msg(text):
    return text
def bold_msg(text):
    return colored(text, 'white')
def list_msg(text):
    return colored(text, 'cyan')

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

def boxedtext(title, text, tint, width=75):
    '''
    Put text in a lovely unicode block element box.  The top
    of the box will contain a title.  The box elements will
    be coloreded.
    '''
    remainder = width - 5 - len(title)
    ul        = u'\u250C' # u'\u2554'
    ur        = u'\u2510' # u'\u2557'
    ll        = u'\u2514' # u'\u255A'
    lr        = u'\u2518' # u'\u255D'
    bar       = u'\u2500' # u'\u2550'
    strut     = u'\u2502' # u'\u2551'
    template  = '%-' + str(width) + 's'

    print('')
    print(colored(''.join([ul, bar*3, ' ', title, ' ', bar*remainder, ur]), tint))
    for line in text.split('\n'):
        add = ''
        if line.count(color.Normal) == 1:
            add = ' '*11
        elif line.count(color.Normal) == 2:
            add = ' '*22
        elif line.count(color.Normal) == 3:
            add = ' '*27
        elif line.count(color.Normal) == 4:
            add = ' '*26
        print(''.join([colored(strut, tint), template%line, add, colored(strut, tint)]))
    print(colored(''.join([ll, bar*width, lr]), tint))


def clear_dashboard():
    '''Clean up in a way that helps the cadashboard utility'''
    if os.path.isfile('/home/xf06bm/Data/.xafs.scan.running'):
        os.remove('/home/xf06bm/Data/.xafs.scan.running')
    elif os.path.isfile('/home/xf06bm/Data/.line.scan.running'):
        os.remove('/home/xf06bm/Data/.line.scan.running')
    elif os.path.isfile('/home/xf06bm/Data/.area.scan.running'):
        os.remove('/home/xf06bm/Data/.area.scan.running')
    elif os.path.isfile('/home/xf06bm/Data/.time.scan.running'):
        os.remove('/home/xf06bm/Data/.time.scan.running')
