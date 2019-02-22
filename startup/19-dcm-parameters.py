#run_report(__file__)

class dcm_parameters():
    '''
    A simple class for gathering metadata about the current user experiment, including
    GUP & SAF numbers, start date, and some operational flags.
    '''
    def __init__(self):
        self.dspacing_111 = 3.13563694 # 29 May 2018
        self.dspacing_311 = 1.63763854 # 30 May 2018
        self.offset_111 = 16.05684
        self.offset_311 = 15.99235495
BMM_dcm = dcm_parameters()
