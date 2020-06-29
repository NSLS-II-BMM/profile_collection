from ophyd import (SingleTrigger, Component as Cpt, Device, DeviceStatus, EpicsSignalRO)

class FEBPM(Device):
    x = Cpt(EpicsSignalRO, 'X-I')
    y = Cpt(EpicsSignalRO, 'Y-I')


    
