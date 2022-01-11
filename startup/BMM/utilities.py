from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, Signal, Device

from BMM.functions import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper

class Vacuum(Device):
    current  = Cpt(EpicsSignal, '-IP:1}I-I')
    pressure = Cpt(EpicsSignal, '-CCG:1}P:Raw-I')

    def _pressure(self):
        #print(self.pressure.get())
        #print(type(self.pressure.get()))
        if self.connected is False:
            return(disconnected_msg('?????'))
        if self.pressure.get() == 'OFF':
            return(disconnected_msg(-1.1E-15))

        if type(self.pressure.get()) is str and self.pressure.get() == 'LO<E-11':
            return whisper('1.00e-11')
        if float(self.pressure.get()) > 1e-6:
            return error_msg(self.pressure.get())
        if float(self.pressure.get()) > 1e-8:
            return warning_msg(self.pressure.get())
        return(self.pressure.get())

    def _current(self):
        if self.connected is False:
            return(disconnected_msg('?????'))
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
        if self.connected is False:
            return(disconnected_msg('?????'))
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
        if self.connected is False:
            return(disconnected_msg('?????'))
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
        if self.connected is False:
            return(disconnected_msg('?????'))
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
        if self.connected is False:
            return disconnected_msg('?????')
        if self.state.get() == 0:
            return error_msg('closed')
        return('open  ')


class Thermocouple(Device):
    temperature = Cpt(EpicsSignal, '-I-I')
    warning     = Cpt(EpicsSignal, '-I_High-RB')
    alarm       = Cpt(EpicsSignal, '-I_HiHi-RB')

    def _state(self, info=False):
        t = "%.1f" % self.temperature.get()
        if self.connected is False:
            return(disconnected_msg('?????'))
        if self.temperature.get() > self.alarm.get():
            return(error_msg(t))
        if self.temperature.get() > self.warning.get():
            return(warning_msg(t))
        if info is True and self.temperature.get() > (0.5 * self.warning.get()):
            return(info_msg(t))
        return(t)

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


class BMM_DIWater(Device):
    dcm_flow = Cpt(EpicsSignal, 'F:2-I')
    dm1_flow = Cpt(EpicsSignal, 'F:1-I')
    return_pressure = Cpt(EpicsSignal, 'P:Return-I')
    return_temperature = Cpt(EpicsSignal, 'T:Return-I')
    supply_pressure = Cpt(EpicsSignal, 'P:Supply-I')
    supply_temperature = Cpt(EpicsSignal, 'T:Supply-I')
    
