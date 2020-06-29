
from BMM.frontend import FEBPM

run_report(__file__)


try:
    bpm_upstream   = FEBPM('SR:C06-BI{BPM:4}Pos:', name='bpm_upstream')
    bpm_downstream = FEBPM('SR:C06-BI{BPM:5}Pos:', name='bpm_downstream')
except:
    pass

def read_bpms():
    return(bpm_upstream.x.get(), bpm_upstream.y.get(), bpm_downstream.x.get(), bpm_downstream.y.get())
