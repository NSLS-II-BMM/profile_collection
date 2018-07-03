from numpy import pi, sin, cos, arcsin, sqrt

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

#from termcolor import colored
def colored(text, color='white', attrs=[]):
    ''' a poor man's termcolor implementation'''
    if color is 'red':
        return '\x1b[01m\x1b[31m' + text + '\x1b[0m'
    if color is 'yellow':
        return '\x1b[01m\x1b[33m' + text + '\x1b[0m'
    if color is 'white':
        return '\x1b[01m\x1b[37m' + text + '\x1b[0m'
