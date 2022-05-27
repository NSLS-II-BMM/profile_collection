
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
        self.dspacing_111 = 3.1354918  # 19 May 2022
        self.dspacing_311 = 1.6375748  # 26 May 2022
        ## *add* the fit result from these numbers!
        self.offset_111 = 16.0739690   # 19 May 2022
        self.offset_311 = 15.9932456   # 26 may 2022


        ## old 111: 3.1353655   16.0608256
        #self.dspacing_311 = 1.6376015  # 12 August 2019
        #self.offset_311 = 15.9893880  # 15.9913698
        
