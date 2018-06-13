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
