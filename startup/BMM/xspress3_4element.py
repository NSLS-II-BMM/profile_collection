from bluesky import __version__ as bluesky_version
from ophyd import Component as Cpt
from ophyd import EpicsSignal
from ophyd.areadetector import Xspress3Detector
import sys

# this was a relevant check when the Xspress3 was first commissioned
# at BMM.  Not so much any more.  Aug 27, 2024
if sys.version_info[1] == 9:
    from nslsii.areadetector.xspress3 import build_detector_class
else:
    from nslsii.areadetector.xspress3 import build_xspress3_class

from BMM import user_ns as user_ns_module
user_ns = vars(user_ns_module)

from BMM.xspress3      import BMMXspress3DetectorBase, BMMXspress3Channel


################################################################################
# Notes:
#
# Before every count or scan, must explicitly set the number of points in the
# measurement:
#   xs.total_points.put(5) 
#
# This means that Xspress3 will require its own count plan
# also that a linescan or xafs scan must set total_points up front

# JOSH: I wish someone had put that note in nslsii.detector.xspress3.py
class BMMXspress3Detector_4Element_Base(BMMXspress3DetectorBase):
    '''Subclass of BMMXspress3DetectorBase specific to the 4-element interface.
    '''

    def __init__(self, prefix, *, configuration_attrs=None, read_attrs=None,
                 **kwargs):
        if read_attrs is None:
            read_attrs = ['hdf5']
        super().__init__(prefix, configuration_attrs=configuration_attrs,
                         read_attrs=read_attrs, **kwargs)
        self.hdf5.num_extra_dims.put(0)

        ## May 22, 2024: this PV suppresses the EraseOnStart function
        ## of the Xspress3 IOC.  When on and used in the way BMM uses
        ## the IOC, this leads to trouble in the form of a "ghost
        ## frame" whenever the Xspress3 is counted.  This confuses a
        ## simple count, and also adds considerable overhead to an
        ## XAFS scan.  These two lines force that PV to off in a way
        ## that is intentionally hidden.
        erase_on_start = EpicsSignal('XF:06BM-ES{Xsp:1}:det1:EraseOnStart', name='erase_on_start')
        erase_on_start.put(0)

if sys.version_info[1] == 9:
    BMMXspress3Detector_4Element = build_detector_class(
        channel_numbers=(1, 2, 3, 4),
        mcaroi_numbers=range(1, 17),
        detector_parent_classes=(BMMXspress3Detector_4Element_Base, )
    )
else:
    BMMXspress3Detector_4Element = build_xspress3_class(
        channel_numbers=(1, 2, 3, 4),
        mcaroi_numbers=range(1, 17),
        image_data_key="xrf",
        xspress3_parent_classes=(BMMXspress3Detector_4Element_Base, ),
    )
