from ophyd import Component as Cpt, EpicsSignal, Signal, Device

#from termcolor import colored
def colored(text, color='white', attrs=[]):
    if color is 'red':
        return '\x1b[01m\x1b[31m' + text + '\x1b[0m'
    if color is 'yellow':
        return '\x1b[01m\x1b[33m' + text + '\x1b[0m'
    if color is 'white':
        return '\x1b[01m\x1b[37m' + text + '\x1b[0m'


def show_shutters():
    bmps_state = bool(bmps.state.value)
    bmps_text = '  BMPS: '
    if bmps_state is True:
        bmps_text += 'open'
    else:
        bmps_text += colored('closed', 'red', attrs=['bold'])

    idps_state = bool(idps.state.value)
    idps_text = '\t\tIDPS: '
    if idps_state is True:
        idps_text += 'open'
    else:
        idps_text += colored('closed', 'red', attrs=['bold'])

    # sha_state = bool(sha.enabled.value) and bool(sha.state.value)
    # sha_text = '\t\tFOE Shutter: '
    # if sha_state is True:
    #     sha_text += 'open'
    # else:
    #     sha_text += colored('closed', 'red', attrs=['bold'])

    shb_state = bool(shb.state.value)
    shb_text = '\t\tPhoton Shutter: '
    if shb_state is False:
        shb_text += 'open'
    else:
        shb_text += colored('closed', 'red', attrs=['bold'])

    print(bmps_text + idps_text + shb_text)

class Vacuum(Device):
    current  = Cpt(EpicsSignal, '-IP:1}I-I')
    pressure = Cpt(EpicsSignal, '-CCG:1}P:Raw-I')

    def _pressure(self):
        if float(self.pressure.value) > 1e-6:
            return colored(self.pressure.value, 'red', attrs=['bold'])
        if float(self.pressure.value) > 1e-8:
            return colored(self.pressure.value, 'yellow', attrs=['bold'])
        return(self.pressure.value)

vac = [Vacuum('XF:06BMA-VA{FS:1',     name='Diagnostic Module 1'),
       Vacuum('XF:06BMA-VA{Mono:DCM', name='Monochromator'),
       Vacuum('XF:06BMA-VA{FS:2',     name='Diagnostic Module 2'),
       Vacuum('XF:06BMA-VA{Mir:2',    name='Focusing Mirror'),
       Vacuum('XF:06BMA-VA{Mir:3',    name='Harmonic Rej. Mirror'),
       Vacuum('XF:06BMB-VA{BT:1',     name='Transport Pipe'),
       Vacuum('XF:06BMB-VA{FS:3',     name='Diagnostic Module 3')]

#Failed to connect to XF:06BMA-VA{Mono:DCM:OPS-BI{DCCT:1}I:Real-I

def show_vacuum():
    print(' Vacuum section       pressure    current')
    print('==================================================')
    for v in vac:
        print('%-20s  %s    %5.1f μA' % (v.name, v._pressure(), 1e6 * float(v.current.value)))


class GateValve(Device):
    state = Cpt(EpicsSignal, 'Pos-Sts')
    cls = Cpt(EpicsSignal, 'Cmd:Cls-Cmd')
    opn = Cpt(EpicsSignal, 'Cmd:Opn-Cmd')
    error = Cpt(EpicsSignal,'Err-Sts')
    permit = Cpt(EpicsSignal, 'Permit:Enbl-Sts')
    enabled = Cpt(EpicsSignal, 'Enbl-Sts')

    def open_plan(self):
        yield from mv(self.opn, 1)

    def close_plan(self):
        yield from mv(self.cls, 1)

    def open(self):
        print('Opening {}'.format(self.name))
        self.opn.put(1)

    def close(self):
        print('Closing {}'.format(self.name))
        self.cls.put(1)

    def _state(self):
        if self.state.value == 0:
            return colored('closed', 'red', attrs=['bold'])
        return('open  ')

gv = [GateValve('FE:C06B-VA{GV:1}DB:',     name='FEGV1'),
      GateValve('FE:C06B-VA{GV:3}DB:',     name='FEGV3'),
      GateValve('FE:C06B-VA{GV:2}DB:',     name='FEGV2'),
      GateValve('XF:06BMA-VA{FS:1-GV:1}',  name='GV1'),
      GateValve('XF:06BMA-VA{BS:PB-GV:1}', name='GV2'),
      GateValve('XF:06BMA-VA{FS:2-GV:1}',  name='GV3'),
      GateValve('XF:06BMA-VA{Mir:2-GV:1}', name='GV4'),
      GateValve('XF:06BMA-VA{Mir:3-GV:1}', name='GV5'),
      GateValve('XF:06BMB-VA{BT:1-GV:1}',  name='GV6')]

def show_gate_valves():
    print('Valve     state')
    print('==================')
    for g in gv:
        print('  %s     %s' % (g.name, g._state()))


class Thermocouple(Device):
    temperature = Cpt(EpicsSignal, '-I-I')
    warning     = Cpt(EpicsSignal, '-I_High-RB')
    alarm       = Cpt(EpicsSignal, '-I_HiHi-RB')

    def _state(self):
        t = "%.1f" % self.temperature.value
        if self.temperature.value > self.alarm.value:
            return(colored(t, 'red', attrs=['bold']))
        if self.temperature.value > self.warning.value:
            return(colored(t, 'yellow', attrs=['bold']))
        return(t)


tcs = [Thermocouple('FE:C06B-OP{Mir:1}T:1',                  name = 'Mirror 1, inboard fin'),
       Thermocouple('FE:C06B-OP{Mir:1}T:2',                  name = 'Mirror 1, disaster mask'),
       Thermocouple('FE:C06B-OP{Mir:1}T:3',                  name = 'Mirror 1, outboard fin'),
       Thermocouple('XF:06BMA-OP{FS:1}T:1',                  name = 'First fluorescent screen'),
       Thermocouple('XF:06BMA-OP{Mono:DCM-Crys:1}T',         name = '111 first crystal'),
       Thermocouple('XF:06BMA-OP{Mono:DCM-Crys:2}T',         name = '311 first crystal'),
       Thermocouple('XF:06BMA-OP{Mono:DCM-Crys:1-Ax:R}T',    name = 'Compton shield'),
       Thermocouple('XF:06BMA-OP{Mono:DCM-Crys:2-Ax:P}T',    name = 'Second crystal pitch'),
       Thermocouple('XF:06BMA-OP{Mono:DCM-Crys:2-Ax:R}T',    name = 'Second crystal roll'),
       Thermocouple('XF:06BMA-OP{Mono:DCM-Crys:2-Ax:Perp}T', name = 'Second crystal perpendicular'),
       Thermocouple('XF:06BMA-OP{Mono:DCM-Crys:2-Ax:Para}T', name = 'Second crystal parallel'),
       Thermocouple('XF:06BMA-OP{Mir:2}T:1',                 name = 'Mirror 2 upstream'),
       Thermocouple('XF:06BMA-OP{Mir:2}T:2',                 name = 'Mirror 2 downstream'),
       Thermocouple('XF:06BMA-OP{Mir:3}T:1',                 name = 'Mirror 3 upstream'),
       Thermocouple('XF:06BMA-OP{Mir:3}T:2',                 name = 'Mirror 3 downstream'),
       Thermocouple('XF:06BMA-OP{Fltr:1}T:1',                name = 'Filter assembly 1, slot 1'),
       Thermocouple('XF:06BMA-OP{Fltr:1}T:3',                name = 'Filter assembly 1, slot 2'),
       Thermocouple('XF:06BMA-OP{Fltr:1}T:5',                name = 'Filter assembly 1, slot 3'),
       Thermocouple('XF:06BMA-OP{Fltr:1}T:7',                name = 'Filter assembly 1, slot 4'),
       Thermocouple('XF:06BMA-OP{Fltr:1}T:2',                name = 'Filter assembly 2, slot 1'),
       Thermocouple('XF:06BMA-OP{Fltr:1}T:4',                name = 'Filter assembly 2, slot 2'),
       Thermocouple('XF:06BMA-OP{Fltr:1}T:6',                name = 'Filter assembly 2, slot 3'),
       Thermocouple('XF:06BMA-OP{Fltr:1}T:8',                name = 'Filter assembly 2, slot 4'),
]


def show_thermocouples():
    print('Thermocouple     Temperature')
    print('===================================')
    for t in tcs:
        print('  %-28s     %s' % (t.name, t._state()))


import datetime
def show_utilities():
    print('  ' + datetime.datetime.now().strftime('%A %d %B, %Y %I:%M %p'))
    print('')
    show_shutters()
    print('')
    ltcs = len(tcs)
    lvac = len(vac)
    lgv  = len(gv)
    print('  Thermocouple               Temperature         Valve   state          Vacuum section       pressure     current')
    print('=======================================================================================================================')
    for i in range(0,ltcs):
        if i < lvac and i < lgv:
            print('  %-28s     %s C        %-5s   %s        %-20s  %s    %5.1f μA' %
                  (tcs[i].name, tcs[i]._state(), gv[i].name, gv[i]._state(), vac[i].name, vac[i]._pressure(), 1e6 * float(vac[i].current.value)))
        elif i < lgv:
            print('  %-28s     %s C        %-5s   %s' %
                  (tcs[i].name, tcs[i]._state(), gv[i].name, gv[i]._state()))
        else:
            print('  %-28s     %s C' %
                  (tcs[i].name, tcs[i]._state()))

def su():
    show_utilities()
