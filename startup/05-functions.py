from numpy import pi, sin, cos, arcsin, sqrt

import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="CA.Client.Exception")

#from termcolor import colored
# def colored(text, color='white', attrs=[]):
#     ''' a poor man's termcolor implementation'''
#     if color is 'red':
#         return '\x1b[01m\x1b[31m' + text + '\x1b[0m'
#     if color is 'yellow':
#         return '\x1b[01m\x1b[33m' + text + '\x1b[0m'
#     if color is 'brown':
#         return '\x1b[33m'         + text + '\x1b[0m'
#     if color is 'cyan':
#         return '\x1b[01m\x1b[36m' + text + '\x1b[0m'
#     if color is 'white':
#         return '\x1b[01m\x1b[37m' + text + '\x1b[0m'

# Black, Blue, Brown, Cyan, DarkGray, Green, NoColor, Normal, Purple,
# Red, White, Yellow,

# LightBlue, LightCyan, LightGray, LightGreen, LightPurple, LightRed,

# BlinkBlack, BlinkBlue, BlinkCyan, BlinkGreen, BlinkLightGray,
# BlinkPurple, BlinkRed, BlinkYellow,

from IPython.utils.coloransi import TermColors as color
def colored(text, tint='white', attrs=[]):
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
    print(colored('Importing %s ...' % thisfile.split('/')[-1], 'lightcyan'))

run_report(__file__)

##BMM_logfile = '/home/bravel/BMM_master.log'

##################################################
# --- a simple class for managing scan logistics #
##################################################
class xafs_scan_parameters():
    def __init__(self):
        self.prompt = True
        self.final_log_entry = True
        self.gup = 0
        self.saf = 0
BMM_xsp = xafs_scan_parameters()



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

def now():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

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
        if line.count(color.Normal) > 0:
            add = ' '*11*line.count(color.Normal)
        print(''.join([colored(strut, tint), template%line, add, colored(strut, tint)]))
    print(colored(''.join([ll, bar*width, lr]), tint))
