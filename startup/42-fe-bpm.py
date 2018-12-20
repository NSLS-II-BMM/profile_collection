from ophyd import (SingleTrigger, Component as Cpt, Device, DeviceStatus, EpicsSignalRO)

run_report(__file__)

class FEBPM(Device):
    x = Cpt(EpicsSignalRO, 'X-I')
    y = Cpt(EpicsSignalRO, 'Y-I')

try:
    bpm_upstream   = FEBPM('SR:C06-BI{BPM:4}Pos:', name='bpm_upstream')
    bpm_downstream = FEBPM('SR:C06-BI{BPM:5}Pos:', name='bpm_downstream')
except:
    pass

def read_bpms():
    return(bpm_upstream.x.value, bpm_upstream.y.value, bpm_downstream.x.value, bpm_downstream.y.value)
