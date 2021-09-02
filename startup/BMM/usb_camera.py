
from ophyd import (SingleTrigger, AreaDetector, DetectorBase, Component as Cpt, Device,
                   EpicsSignal, EpicsSignalRO, ImagePlugin, StatsPlugin, ROIPlugin,
                   DeviceStatus)

from ophyd.areadetector.plugins import ImagePlugin_V33

class CAMERA(SingleTrigger, AreaDetector):
    image = Cpt(ImagePlugin_V33, 'image1:')

    
