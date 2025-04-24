from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, Signal, Device

from BMM.functions import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper

class Vacuum(Device):
    current  = Cpt(EpicsSignal, '-IP:1}I-I')
    pressure = Cpt(EpicsSignal, '-CCG:1}P:Raw-I')

    def _pressure(self):
        #print(self.pressure.get())
        #print(type(self.pressure.get()))
        if self.connected is False:
            return('[magenta]?????[/magenta]')
        if self.pressure.get() == 'OFF':
            return('[magenta]-1.1E-15[/magenta]')

        if type(self.pressure.get()) is str and self.pressure.get() == 'LO<E-11':
            return('[bold black]1.00e-11[/bold black]')
        if float(self.pressure.get()) > 1e-6:
            return('[bold red]' + str(self.pressure.get()) + '[/bold red]')
        if float(self.pressure.get()) > 1e-8:
            return('[bold yellow]' + str(self.pressure.get())  + '[/bold yellow]')
        return(f'[white]{self.pressure.get()}[/white]')

    def _current(self):
        if self.connected is False:
            return('[magenta]?????[/magenta]')
        curr = float(self.current.get())
        if curr > 2e-3:
            out = '%.1f' % (1e3*curr)
            return(f'[bold red]{out}[/bold red]')
        if curr > 5e-4:
            out = '%.1f' % (1e3*curr)
            return(f'[bold yellow]{out}[/bold yellow]')
        out = '%.1f' % (1e6*curr)
        return(f'[white]{out}[/white]')

class TCG(Device):
    pressure = Cpt(EpicsSignalRO, '-TCG:1}P:Raw-I')

    def _pressure(self):
        if self.connected is False:
            return('[magenta]?????[/magenta]')
        if self.pressure.get() == 'OFF':
            return('[magenta]-1.1e-15[/magenta]')
        if float(self.pressure.get()) > 1e-1:
            return(f'[bold yellow]{self.pressure.get()}[/bold yellow]')
        if float(self.pressure.get()) > 6e-3:
            return(f'[bold red]{self.pressure.get()}[/bold red]')
        return(f'[white]{self.pressure.get()}[/white]')

class Rack(Device):
    temperature = Cpt(EpicsSignalRO, 'T-I')
    def _state(self, info=False):
        if self.connected is False:
            return('[magenta]?????[/magenta]')
        if self.temperature.get() == 'OFF':
            return('[magenta]OFF[/magenta]')
        if float(self.temperature.get()) > 26:
            return(f'[bold yellow]{self.temperature.get()}[/bold yellow]')
        if float(self.temperature.get()) > 30:
            return(f'[bold red]{self.temperature.get()}[/bold red]')
        return(f'[white]{self.temperature.get()}[/white]')
    
    
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
            return('[magenta]?????[/magenta]')
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
            return('[magenta]-1.1e-15[/magenta]')

        if float(sgnl.get()) > 1e-6:
            return(f'[bold red]{self.pressure.get()}[/bold red]')
        if float(sgnl.get()) > 1e-8:
            return(f'[bold yellow]{self.pressure.get()}[/bold yellow]')
        return(f'[white]{sgnl.get()}[/white]')

    def _current(self, num=None):
        if self.connected is False:
            return('[magenta]?????[/magenta]')
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
            return(f'[bold red]{out}[/bold red]')
        if curr > 5e-4:
            out = '%.1f' % (1e3*curr)
            return(f'[bold yellow]{out}[/bold yellow]')
        out = '%.1f' % (1e6*curr)
        return(f'[white]{out}[/white]')



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
        #if self.connected is False:
        #    return disconnected_msg('?????')
        if self.state.get() == 0:
            return('[bold red]closed[/bold red]')
        return('open  ')


class Thermocouple(Device):
    temperature = Cpt(EpicsSignal, '-I-I')
    warning     = Cpt(EpicsSignal, '-I_High-RB')
    alarm       = Cpt(EpicsSignal, '-I_HiHi-RB')

    def _state(self, info=False):
        t = "%.1f" % self.temperature.get()
        if self.connected is False:
            return('[magenta]?????[/magenta]')
        if self.temperature.get() > self.alarm.get():
            return(f'[bold red]{t}[/bold red]')
        if self.temperature.get() > self.warning.get():
            return(f'[bold yellow]{t}[/bold yellow]')
        if info is True and self.temperature.get() > (0.5 * self.warning.get()):
            return(f'[yellow]{t}[/yellow]')
        return(f'[white]{t}[/white]')

class OneWireTC(Device):
    temperature = Cpt(EpicsSignal, '-I')
    warning     = Cpt(EpicsSignal, ':Hi-SP')
    alarm       = Cpt(EpicsSignal, '-I.HIHI')

    def _state(self, info=False):
        t = "%.1f" % self.temperature.get()
        if self.temperature.get() > self.alarm.get():
            return(f'[bold red]{t}[/bold red]')
        if self.temperature.get() > self.warning.get():
            return(f'[bold yellow]{t}[/bold yellow]')
        if info is True and self.temperature.get() > (0.5 * self.warning.get()):
            return(f'[yellow]{t}[/yellow]')
        return(f'[white]{t}[/white]')


class BMM_DIWater(Device):
    dcm_flow = Cpt(EpicsSignal, 'F:2-I')
    dm1_flow = Cpt(EpicsSignal, 'F:1-I')
    return_pressure = Cpt(EpicsSignal, 'P:Return-I')
    return_temperature = Cpt(EpicsSignal, 'T:Return-I')
    supply_pressure = Cpt(EpicsSignal, 'P:Supply-I')
    supply_temperature = Cpt(EpicsSignal, 'T:Supply-I')
    
