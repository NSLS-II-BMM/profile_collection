
from BMM.dwelltime import LockedDwellTimes

run_report(__file__)


_locked_dwell_time = LockedDwellTimes('', name='dwti')
dwell_time = _locked_dwell_time.dwell_time
dwell_time.name = 'inttime'

#abs_set(_locked_dwell_time, 0.5)
