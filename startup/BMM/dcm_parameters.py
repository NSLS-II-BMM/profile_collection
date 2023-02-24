
class dcm_parameters():
    '''A simple class for maintaining calibration parameters for the
    Si(111) and Si(311) monochromators.

    Parameters
    ----------
    BMM_dcm.dspacing_111 : float
        d-spacing for the Si(111) mono
    BMM_offset_111 : float
        angular offset for the Si(111) mono
    BMM_dcm.dspacing_311 : float
        d-spacing for the Si(311) mono
    BMM_offset_311 : float
        angular offset for the Si(311) mono

    '''

    def __init__(self):
        self.dspacing_111 = 3.1355417  # 19 January 2023
        self.dspacing_311 = 1.6376591  # 7 October 2022
        ## *add* the fit result from these numbers!
        self.offset_111 = 16.0752237   # 19 January 2023
        self.offset_311 = 15.9912274   # hand adjusted 18 February 2023
        
