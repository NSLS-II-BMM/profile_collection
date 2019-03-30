#run_report(__file__)

class dcm_parameters():
    '''A simple class for maintaining calibration parameters for the
    Si(111) and Si(311) monochromators.

    BMM_dcm.dspacing_111:   d-spacing for the Si(111) mono
    BMM_offset_111:         angular offset for the Si(111) mono

    BMM_dcm.dspacing_311:   d-spacing for the Si(311) mono
    BMM_offset_311:         angular offset for the Si(311) mono

    '''
    def __init__(self):
        self.dspacing_111 = 3.13524679 # 28 March 2019
        self.dspacing_311 = 1.63763854 # 30 May 2018
        self.offset_111 = 16.05469
        self.offset_311 = 15.99235495
BMM_dcm = dcm_parameters()
