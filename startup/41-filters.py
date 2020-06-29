
from BMM.attenuators import attenuator, filter_state, set_filters

run_report(__file__)

filter1 = attenuator()
filter1.motor = dm1_filters1
filter2 = attenuator()
filter2.motor = dm1_filters2


