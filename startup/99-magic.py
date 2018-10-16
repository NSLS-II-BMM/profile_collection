from IPython.core.magic import register_line_magic  #, register_cell_magic, register_line_cell_magic)

run_report(__file__)


@register_line_magic
def h(line):
    "BMM help text"
    BMM_help()
    return None

@register_line_magic
def k(line):
    "help on ipython keyboard shortcuts"
    BMM_keys()
    return None

@register_line_magic
def ut(line):
    "show BMM utilities status"
    su()
    return None

@register_line_magic
def m(line):
    "show BMM motor status"
    ms()
    return None

@register_line_magic
def w(arg):
    "show a motor position"
    motor = eval(arg)
    return motor.wh()


