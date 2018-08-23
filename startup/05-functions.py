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


# Black,
# Blue,
# Brown,
# Cyan,
# DarkGray,
# Green,
# NoColor,
# Normal,
# Purple,
# Red
# White,
# Yellow,

# LightBlue,
# LightCyan,
# LightGray
# LightGreen,
# LightPurple
# LightRed,

# BlinkBlack,
# BlinkBlue,
# BlinkCyan,
# BlinkGreen,
# BlinkLightGray,
# BlinkPurple,
# BlinkRed,
# BlinkYellow,


from IPython.utils.coloransi import TermColors as color
def colored(text, tint='white', attrs=[]):
    tint = tint.lower()
    if 'dark' in tint:
        tint = 'Dark' + tint[4:].capitalize()
    elif 'light' in tint:
        tint = 'Light' + tint[5:].capitalize()
    elif 'no' in tint:
        tint = 'Normal'
    else:
        tint = tint.capitalize()
    return '{0}{1}{2}'.format(getattr(color, tint), text, color.Normal)

def run_report(thisfile):
    print(colored('Importing %s ...' % thisfile.split('/')[-1], 'cyan'))

run_report(__file__)

BMM_logfile = '/home/bravel/BMM_master.log'

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
