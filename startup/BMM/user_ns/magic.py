from IPython.core.magic import register_line_magic  #, register_cell_magic, register_line_cell_magic)
from BMM.functions import run_report
from BMM.user_ns.bmm import BMMuser

run_report(__file__, text='ipython magics for BMM ... general help: %h')

from BMM.prompt import BMM_help, BMM_keys
@register_line_magic
def h(line):
    '''BMM help text'''
    BMM_help()
    return None

@register_line_magic
def k(line):
    '''help on ipython keyboard shortcuts'''
    BMM_keys()
    return None

from BMM.user_ns.utilities import su, show_vacuum, sw
@register_line_magic
def ut(line):
    '''show BMM utilities status'''
    su()
    return None

@register_line_magic
def v(line):
    '''show BMM vacuum status'''
    show_vacuum()
    return None

from BMM.edge import show_edges
@register_line_magic
def se(line):
    '''show foils and ROIs cnfiguration'''
    show_edges()
    return None

@register_line_magic
def h2o(line):
    '''show BMM DI and PCW water status'''
    sw()
    return None

from BMM.motor_status import ms, xrdm
@register_line_magic
def m(line):
    '''show BMM motor status'''
    ms()
    return None

@register_line_magic
def xm(line):
    '''show XRD motor status'''
    xrdm()
    return None

from BMM.user_ns.motors import *
from BMM.user_ns.instruments import *
from BMM.user_ns.dcm import dcm
@register_line_magic
def w(arg):
    '''show a motor position'''
    try:
        motor = eval(arg)
        return motor.wh()
    except:
        print(f'{arg} is not a thing that can be probed for position')

from BMM.derivedplot import close_all_plots
@register_line_magic
def ca(arg):
    '''close all plots'''
    close_all_plots()
    return None

from BMM.user_ns.detectors import xs
@register_line_magic
def xrf(arg):
    xs.measure_xrf()
    return None

from BMM.user_ns.bmm import whoami
if BMMuser.trigger is True:     # provide feedback if importing persistent user information 
    print('')
    whoami()
    BMMuser.trigger = False
