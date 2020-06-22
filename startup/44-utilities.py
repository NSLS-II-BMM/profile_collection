from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, Signal, Device

run_report(__file__)

#############################
# beamline enabled/disabled #
#############################

try:
    bl_enabled = EpicsSignalRO('SR:C06-EPS{PLC:1}Sts:BM_BE_Enbl-Sts', name='enabled')
except:
    bl_enabled = 0

#####################
# state of shutters #
#####################

def show_shutters():

    ena_text = '  Beamline: '
    if bl_enabled.get() == 1:
        ena_text += 'enabled      '
    else:
        ena_text += error_msg('disabled      ')
    
    bmps_state = bool(bmps.state.get())
    bmps_text = '  BMPS: '

    if bmps_state is True:
        bmps_text += 'open'
    else:
        bmps_text += error_msg('closed')

    idps_state = bool(idps.state.get())
    idps_text = '            IDPS: '
    if idps_state is True:
        idps_text += 'open'
    else:
        idps_text += error_msg('closed')

    # sha_state = bool(sha.enabled.get()) and bool(sha.state.get())
    # sha_text = '            FOE Shutter: '
    # if sha_state is True:
    #     sha_text += 'open'
    # else:
    #     sha_text += error_msg('closed')

    shb_state = bool(shb.state.get())
    shb_text = '            Photon Shutter: '
    if shb_state is False:
        shb_text += 'open'
    else:
        shb_text += error_msg('closed')

    return(ena_text + bmps_text + idps_text + shb_text)


##########################################################
# state of vacuum levels in the various vacuum sections  #
# the seven PDS vacuum sections report on Pirani and CCG #
# the XRD flight path is just a Pirani                   #
##########################################################

class Vacuum(Device):
    current  = Cpt(EpicsSignal, '-IP:1}I-I')
    pressure = Cpt(EpicsSignal, '-CCG:1}P:Raw-I')

    def _pressure(self):
        #print(self.pressure.get())
        #print(type(self.pressure.get()))
        if self.pressure.get() == 'OFF':
            return(disconnected_msg(-1.1E-15))

        if float(self.pressure.get()) > 1e-6:
            return error_msg(self.pressure.get())
        if float(self.pressure.get()) > 1e-8:
            return warning_msg(self.pressure.get())
        return(self.pressure.get())

    def _current(self):
        curr = float(self.current.get())
        if curr > 2e-3:
            out = '%.1f' % (1e3*curr)
            return(error_msg(out))
        if curr > 5e-4:
            out = '%.1f' % (1e3*curr)
            return(warning_msg(out))
        out = '%.1f' % (1e6*curr)
        return(out)

class TCG(Device):
    pressure = Cpt(EpicsSignalRO, '-TCG:1}P:Raw-I')

    def _pressure(self):
        if self.pressure.get() == 'OFF':
            return(disconnected_msg(-1.1e-15))
        if float(self.pressure.get()) > 1e-1:
            return warning_msg(self.pressure.get())
        if float(self.pressure.get()) > 6e-3:
            return error_msg(self.pressure.get())
        return(self.pressure.get())

    
## front end vacuum readings FE:C06B-VA{CCG:#}P-1 and FE:C06B-VA{IP:#}P-1
## at 6BM, # = (1 .. 6)

class FEVac(Device):
    #pressure = [None,
    p1 = Cpt(EpicsSignal, 'CCG:1}P:Raw-I')
    p2 = Cpt(EpicsSignal, 'CCG:2}P:Raw-I')
    p3 = Cpt(EpicsSignal, 'CCG:3}P:Raw-I')
    p4 = Cpt(EpicsSignal, 'CCG:4}P:Raw-I')
    p5 = Cpt(EpicsSignal, 'CCG:5}P:Raw-I')
    p6 = Cpt(EpicsSignal, 'CCG:6}P:Raw-I')
    c1 = Cpt(EpicsSignal, 'IP:1}P-I')
    c2 = Cpt(EpicsSignal, 'IP:2}P-I')
    c3 = Cpt(EpicsSignal, 'IP:3}P-I')
    c4 = Cpt(EpicsSignal, 'IP:4}P-I')
    c5 = Cpt(EpicsSignal, 'IP:5}P-I')
    c6 = Cpt(EpicsSignal, 'IP:6}P-I')
               
    def _pressure(self, num=None):
        if num is None:
            num = 1
        if num < 1:
            num = 1
        if num > 6:
            num = 6
        sgnl = getattr(self, 'p'+str(num))
        #print(self.pressure.get())
        #print(type(self.pressure.get()))
        if sgnl.get() == 'OFF':
            return(disconnected_msg(-1.1E-15))

        if float(sgnl.get()) > 1e-6:
            return error_msg(self.pressure.get())
        if float(sgnl.get()) > 1e-8:
            return warning_msg(self.pressure.get())
        return(sgnl.get())

    def _current(self, num=None):
        if num is None:
            num = 1
        if num < 1:
            num = 1
        if num > 6:
            num = 6
        sgnl = getattr(self, 'c'+str(num))
        curr = float(sgnl.get())
        if curr > 2e-3:
            out = '%.1f' % (1e3*curr)
            return(error_msg(out))
        if curr > 5e-4:
            out = '%.1f' % (1e3*curr)
            return(warning_msg(out))
        out = '%.1f' % (1e6*curr)
        return(out)

fev = FEVac('FE:C06B-VA{', name='FrontEndVacuum')

vac = [Vacuum('XF:06BMA-VA{FS:1',     name='Diagnostic Module 1'),
       Vacuum('XF:06BMA-VA{Mono:DCM', name='Monochromator'),
       Vacuum('XF:06BMA-VA{FS:2',     name='Diagnostic Module 2'),
       Vacuum('XF:06BMA-VA{Mir:2',    name='Focusing Mirror'),
       Vacuum('XF:06BMA-VA{Mir:3',    name='Harmonic Rej. Mirror'),
       Vacuum('XF:06BMB-VA{BT:1',     name='Transport Pipe'),
       Vacuum('XF:06BMB-VA{FS:3',     name='Diagnostic Module 3')]

flight_path = TCG('XF:06BMB-VA{FltPth:1', name='Flight Path')

#Failed to connect to XF:06BMA-VA{Mono:DCM:OPS-BI{DCCT:1}I:Real-I


def show_vacuum():
    text  = ' Vacuum section       pressure    current\n'
    text += '==================================================\n'
    for v in vac:
        if float(v.current.get()) > 5e-4:
            text += '%-20s  %s    %4s  mA\n' % (v.name, v._pressure(), v._current())
        else:
            text += '%-20s  %s    %4s μA\n' % (v.name, v._pressure(), v._current())
    text += '%-20s  %s\n' % (flight_path.name, flight_path._pressure())
    for i in range(1,7):
        text += 'Front end section %d   %s\n' % (i, fev._pressure(i))
    boxedtext('BMM vacuum', text, 'brown', width=55)

############################
# state of gate valves     #
############################

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
        if self.state.get() == 0:
            return error_msg('closed')
        return('open  ')

gv = [GateValve('FE:C06B-VA{GV:1}',        name='FEGV1'),
      GateValve('FE:C06B-VA{GV:3}',        name='FEGV3'),
      GateValve('FE:C06B-VA{GV:2}',        name='FEGV2'),
      GateValve('XF:06BMA-VA{FS:1-GV:1}',  name='GV1'),
      GateValve('XF:06BMA-VA{BS:PB-GV:1}', name='GV2'),
      GateValve('XF:06BMA-VA{FS:2-GV:1}',  name='GV3'),
      GateValve('XF:06BMA-VA{Mir:2-GV:1}', name='GV4'),
      GateValve('XF:06BMA-VA{Mir:3-GV:1}', name='GV5'),
      GateValve('XF:06BMB-VA{BT:1-GV:1}',  name='GV6'),
      fs1]

def show_gate_valves():
    print('  Valve      state')
    print('=======================')
    for g in gv:
        print('  %-6s     %s' % (g.name, g._state()))

def open_valve(num):
    which = num + 2
    gv[which].open()

def close_valve(num):
    which = num + 2
    gv[which].close()
    
#############################################################
# thermocouples on photon delivery system, read through EPS #
#############################################################
        
class Thermocouple(Device):
    temperature = Cpt(EpicsSignal, '-I-I')
    warning     = Cpt(EpicsSignal, '-I_High-RB')
    alarm       = Cpt(EpicsSignal, '-I_HiHi-RB')

    def _state(self, info=False):
        t = "%.1f" % self.temperature.get()
        if self.temperature.get() > self.alarm.get():
            return(error_msg(t))
        if self.temperature.get() > self.warning.get():
            return(warning_msg(t))
        if info is True and self.temperature.get() > (0.5 * self.warning.get()):
            return(info_msg(t))
        return(t)

tcs = [Thermocouple('XF:06BM-EPS-OP{Mir:1}T:1',              name = 'Mirror 1, inboard fin'),
       Thermocouple('XF:06BM-EPS-OP{Mir:1}T:2',              name = 'Mirror 1, disaster mask'),
       Thermocouple('XF:06BM-EPS-OP{Mir:1}T:3',              name = 'Mirror 1, outboard fin'),
       Thermocouple('XF:06BMA-OP{FS:1}T:1',                  name = 'First fluorescent screen'),
       Thermocouple('XF:06BMA-OP{Mono:DCM-Crys:1}T',         name = '111 first crystal'),
       Thermocouple('XF:06BMA-OP{Mono:DCM-Crys:2}T',         name = '311 first crystal'),
       Thermocouple('XF:06BMA-OP{Mono:DCM-Crys:1-Ax:R}T',    name = 'Compton shield'),
       Thermocouple('XF:06BMA-OP{Mono:DCM-Crys:2-Ax:R}T',    name = 'Second crystal roll'),
       Thermocouple('XF:06BMA-OP{Mono:DCM-Crys:2-Ax:P}T',    name = 'Second crystal pitch'),
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


###################################################################
# One-Wire network of temperature sensors placed around the mono  #
###################################################################

class OneWireTC(Device):
    temperature = Cpt(EpicsSignal, '-I')
    warning     = Cpt(EpicsSignal, ':Hi-SP')
    alarm       = Cpt(EpicsSignal, '-I.HIHI')

    def _state(self, info=False):
        t = "%.1f" % self.temperature.get()
        if self.temperature.get() > self.alarm.get():
            return(error_msg(t))
        if self.temperature.get() > self.warning.get():
            return(warning_msg(t))
        if info is True and self.temperature.get() > (0.5 * self.warning.get()):
            return(info_msg(t))
        return(t)

monotc_inboard       = OneWireTC('XF:6BMA{SENS:001}T', name='monotc_inboard')
monotc_upstream_high = OneWireTC('XF:6BMA{SENS:002}T', name='monotc_upstream_high')
monotc_downstream    = OneWireTC('XF:6BMA{SENS:003}T', name='monotc_downstream')
monotc_upstream_low  = OneWireTC('XF:6BMA{SENS:004}T', name='monotc_upstream_low')
    

def show_thermocouples():
    print('Thermocouple     Temperature')
    print('===================================')
    for t in tcs:
        print('  %-28s     %s' % (t.name, t._state()))


################
# flow sensors #
################
class BMM_DIWater(Device):
    dcm_flow = Cpt(EpicsSignal, 'F:2-I')
    dm1_flow = Cpt(EpicsSignal, 'F:1-I')
    return_pressure = Cpt(EpicsSignal, 'P:Return-I')
    return_temperature = Cpt(EpicsSignal, 'T:Return-I')
    supply_pressure = Cpt(EpicsSignal, 'P:Supply-I')
    supply_temperature = Cpt(EpicsSignal, 'T:Supply-I')

bmm_di = BMM_DIWater('XF:06BMA-UT{DI}', name='DI Water')
bmm_di.dcm_flow.name = 'DCM DI flow'
bmm_di.dm1_flow.name = 'DM1 DI flow'
bmm_di.supply_pressure.name = 'DI supply pressure'
bmm_di.supply_temperature.name = 'DI supply temperature'
bmm_di.return_pressure.name = 'DI supply pressure'
bmm_di.return_temperature.name = 'DI supply temperature'
pbs_di_a = EpicsSignalRO('XF:06BM-PPS{DI}F:A1-I', name='PBS water flow A')
pbs_di_b = EpicsSignalRO('XF:06BM-PPS{DI}F:B1-I', name='PBS water flow B')

pcw_supply_temperature = EpicsSignalRO('XF:06BMA-PU{PCW}T:Supply-I', name='PCW supply temperature')
pcw_return_temperature = EpicsSignalRO('XF:06BMA-PU{PCW}T:Return-I', name='PCW return temperature')

foe_leak_detector = EpicsSignalRO('XF:06BMA-UT{LD:1}Alrm-Sts', name='FOE water leak detector')

def show_water():
    text  = '  ' + datetime.datetime.now().strftime('%A %d %B, %Y %I:%M %p') + '\n\n'
    text += '  Sensor                            Value\n'
    text += ' ==============================================\n'
    for pv in (bmm_di.dm1_flow, bmm_di.dcm_flow,
               bmm_di.supply_pressure, bmm_di.supply_temperature, bmm_di.return_pressure, bmm_di.return_temperature, 
               pbs_di_a, pbs_di_b, pcw_return_temperature, pcw_supply_temperature):
        if pv.alarm_status.get():
            text += error_msg('  %-28s     %.1f %s\n' % (pv.name, float(pv.get()), pv.describe()[pv.name]['units']))
        else:
            text += '  %-28s     %.1f %s\n' % (pv.name, float(pv.get()), pv.describe()[pv.name]['units'])
    if foe_leak_detector.get() > 0:
        text += '  %-28s     %s\n' % (foe_leak_detector.name, foe_leak_detector.enum_strs[foe_leak_detector.get()].replace('  ', ' '))
    else:
        text += error_msg('  %-28s     %s\n' % (foe_leak_detector.name, foe_leak_detector.enum_strs[foe_leak_detector.get()].replace('  ', ' ')))
    return text[:-1]


def sw():
    boxedtext('BMM water', show_water(), 'lightblue', width=55)
        

###########################################################################
# pretty-print a summary of temperatures, valve states, and vacuum levels #
###########################################################################

import datetime
def show_utilities():
    text = '  ' + datetime.datetime.now().strftime('%A %d %B, %Y %I:%M %p') + '\n\n'
    text += show_shutters() + '\n\n'
    ltcs = len(tcs)
    lvac = len(vac)
    lgv  = len(gv)
    text += '  Thermocouple               Temperature         Valve   state          Vacuum section       pressure     current\n'
    text += ' ====================================================================================================================\n'
    for i in range(0,ltcs):
        info = False
        if 'pitch' in tcs[i].name or 'roll' in tcs[i].name: info = True

        if i < lvac and i < lgv:
            units = 'μA'
            if float(vac[i].current.get()) > 5e-4: units = 'mA'
            text += '  %-28s     %s C        %-5s   %s        %-20s  %s    %s %s\n' % \
                    (tcs[i].name, tcs[i]._state(info=info), gv[i].name, gv[i]._state(), vac[i].name, vac[i]._pressure(), vac[i]._current(), units)

        elif i == lvac:         # flight path ... TCG class
            text += '  %-28s     %s C        %-5s   %s        %-20s  %s\n' % \
                    (tcs[i].name, tcs[i]._state(info=info), gv[i].name, gv[i]._state(), flight_path.name, flight_path._pressure())

        elif i < lgv:
            text += '  %-28s     %s C        %-5s   %s\n' % \
                    (tcs[i].name, tcs[i]._state(info=info), gv[i].name, gv[i]._state())

        else:
            text += '  %-28s     %s C\n' % (tcs[i].name, tcs[i]._state(info=info))
    return text[:-1]

def su():
    boxedtext('BMM utilities', show_utilities(), 'brown', width=124)
