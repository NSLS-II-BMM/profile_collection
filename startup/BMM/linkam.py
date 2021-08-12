

from bluesky.plan_stubs import null, sleep, mv, mvr
from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO, Signal, Device

from BMM.functions      import error_msg, warning_msg, go_msg, url_msg, bold_msg, verbosebold_msg, list_msg, disconnected_msg, info_msg, whisper

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)


class Linkam(Device):
    init = Cpt(EpicsSignal, 'INIT')
    model_array = Cpt(EpicsSignal, 'MODEL')
    serial_array = Cpt(EpicsSignal, 'SERIAL')
    stage_model_array = Cpt(EpicsSignal, 'STAGE:MODEL')
    stage_serial_array = Cpt(EpicsSignal, 'STAGE:SERIAL')
    firm_ver = Cpt(EpicsSignal, 'FIRM:VER')
    hard_ver = Cpt(EpicsSignal, 'HARD:VER')
    ctrllr_err = Cpt(EpicsSignal, 'CTRLLR:ERR')
    config = Cpt(EpicsSignal, 'CONFIG')
    status_code = Cpt(EpicsSignal, 'STATUS')
    stage_config = Cpt(EpicsSignal, 'STAGE:CONFIG')
    temp = Cpt(EpicsSignal, 'TEMP')
    disable = Cpt(EpicsSignal, 'DISABLE')
    dsc = Cpt(EpicsSignal, 'DSC')
    startheat = Cpt(EpicsSignal, 'STARTHEAT')
    ramprate_set = Cpt(EpicsSignal, 'RAMPRATE:SET')
    ramprate = Cpt(EpicsSignal, 'RAMPRATE')
    ramptime = Cpt(EpicsSignal, 'RAMPTIME')
    holdtime_set = Cpt(EpicsSignal, 'HOLDTIME:SET')
    holdtime = Cpt(EpicsSignal, 'HOLDTIME')
    setpoint_set = Cpt(EpicsSignal, 'SETPOINT:SET')
    setpoint = Cpt(EpicsSignal, 'SETPOINT')
    power = Cpt(EpicsSignal, 'POWER')
    lnp_speed = Cpt(EpicsSignal, 'LNP_SPEED')
    lnp_mode_set = Cpt(EpicsSignal, 'LNP_MODE:SET')
    lnp_speed_set = Cpt(EpicsSignal, 'LNP_SPEED:SET')

    def goto(self, t):
        self.setpoint_set.put(t)
    
    def on(self):
        self.startheat.put(1)

    def off(self):
        self.startheat.put(0)
    
    def on_plan(self):
        yield from mv(self.startheat, 1)

    def off_plan(self):
        yield from mv(self.startheat, 0)

    def arr2word(self, lst):
        word = ''
        for l in lst[:-1]:
            word += chr(l)
        return word
        
    def serial(self):
        return self.arr2word(self.serial_array.get())
    
    def model(self):
        return self.arr2word(self.model_array.get())
    
    def stage_model(self):
        return self.arr2word(self.stage_model_array.get())
    
    def stage_serial(self):
        return self.arr2word(self.stage_serial_array.get())

    def firmware_version(self):
        return self.arr2word(self.firm_ver.get())

    def hardware_version(self):
        return self.arr2word(self.hard_ver.get())

    def status(self):
        print(f'Linkam {self.model()}, stage {self.stage_model()}\n')
        print(f'Current temperature = {self.temp.get():.1f}, setpoint = {self.setpoint.get():.1f}\n')
        code = int(self.status_code.get())
        if code & 1:
            print(error_msg('Error        : yes'))
        else:
            print('Error        : no')
        if code & 2:
            print(go_msg('At setpoint  : yes'))
        else:
            print('At setpoint  : no')
        if code & 4:
            print(go_msg('Heater       : on'))
        else:
            print('Heater       : off')
        if code & 8:
            print(go_msg('Pump         : on'))
        else:
            print('Pump         : off')
        if code & 16:
            print(go_msg('Pump Auto    : yes'))
        else:
            print('Pump Auto    : no')
            
